from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q, F
from django.contrib.auth.models import User
from functools import wraps
from .models import Course, Enrollment
from .forms import CourseForm

def admin_required(view_func):
    """Decorator checking that user is authenticated and has administrative role."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Administrator login required.")
            return redirect('accounts:login')
        profile = getattr(request.user, 'student_profile', None)
        if not (profile and profile.is_admin):
            messages.error(request, "Access denied. Administrator privileges required.")
            return redirect('courses:index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def index(request):
    """Homepage showcasing hero, database-backed platform metrics, and featured courses."""
    total_courses = Course.objects.count()
    total_students = User.objects.filter(
        Q(student_profile__role='student') | Q(student_profile__isnull=True)
    ).count()
    total_enrollments = Enrollment.objects.filter(status='enrolled').count()
    seats_agg = Course.objects.aggregate(total_avail=Sum('available_seats'))
    total_available_seats = seats_agg['total_avail'] or 0

    featured_courses = Course.objects.all()[:6]

    enrolled_ids = set()
    if request.user.is_authenticated:
        enrolled_ids = set(
            Enrollment.objects.filter(student=request.user, status='enrolled').values_list('course_id', flat=True)
        )

    stats = {
        'total_courses': total_courses,
        'total_students': total_students,
        'total_enrollments': total_enrollments,
        'total_available_seats': total_available_seats,
    }

    return render(request, 'index.html', {
        'stats': stats,
        'courses': featured_courses,
        'enrolled_ids': enrolled_ids,
    })

def explore(request):
    """Explore and search all courses with keyword and filter support."""
    search = request.GET.get('search', '').strip()
    department = request.GET.get('department', 'all').strip()
    availability = request.GET.get('availability', 'all').strip()

    courses_qs = Course.objects.all()

    if search:
        courses_qs = courses_qs.filter(
            Q(course_title__icontains=search) |
            Q(course_code__icontains=search) |
            Q(instructor__icontains=search) |
            Q(description__icontains=search)
        )

    if department and department != 'all':
        courses_qs = courses_qs.filter(department=department)

    if availability == 'available':
        courses_qs = courses_qs.filter(available_seats__gt=0)
    elif availability == 'full':
        courses_qs = courses_qs.filter(available_seats=0)

    departments = Course.objects.values_list('department', flat=True).distinct().order_by('department')

    enrolled_ids = set()
    if request.user.is_authenticated:
        enrolled_ids = set(
            Enrollment.objects.filter(student=request.user, status='enrolled').values_list('course_id', flat=True)
        )

    return render(request, 'courses.html', {
        'courses': courses_qs,
        'departments': departments,
        'search': search,
        'selected_dept': department,
        'selected_avail': availability,
        'enrolled_ids': enrolled_ids,
    })

def course_detail(request, course_id):
    """Detailed view for a single course."""
    course = get_object_or_404(Course, pk=course_id)
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course, status='enrolled').exists()

    return render(request, 'course_detail.html', {
        'course': course,
        'is_enrolled': is_enrolled,
    })

@login_required
def enroll_course(request, course_id):
    """Safely enroll student in a course using an ACID transaction."""
    if request.method != 'POST':
        return redirect('courses:course_detail', course_id=course_id)

    profile = getattr(request.user, 'student_profile', None)
    if profile and profile.is_admin:
        messages.warning(request, "Administrators cannot enroll as students. Please use a student account.")
        return redirect('courses:course_detail', course_id=course_id)

    with transaction.atomic():
        # Select for update to lock course row
        course = Course.objects.select_for_update().filter(pk=course_id).first()
        if not course:
            messages.error(request, "The requested course could not be found.")
            return redirect('courses:explore')

        # Check existing active enrollment
        existing = Enrollment.objects.filter(student=request.user, course=course).first()
        if existing and existing.status == 'enrolled':
            messages.warning(request, f"You are already enrolled in {course.course_code}: {course.course_title}.")
            return redirect('courses:course_detail', course_id=course.pk)

        # Check seat availability
        if course.available_seats <= 0:
            messages.error(request, f"Enrollment failed: {course.course_code} is at maximum capacity (0 seats available).")
            return redirect('courses:course_detail', course_id=course.pk)

        # Re-activate or create enrollment
        if existing:
            existing.status = 'enrolled'
            existing.save()
        else:
            Enrollment.objects.create(student=request.user, course=course, status='enrolled')

        # Decrement available seats atomically
        course.available_seats -= 1
        course.save()

    messages.success(request, f"Successfully enrolled in {course.course_code}: {course.course_title}!")
    return redirect('courses:my_courses')

@login_required
def cancel_enrollment(request, course_id):
    """Safely cancel student enrollment and restore seat capacity."""
    if request.method != 'POST':
        return redirect('courses:my_courses')

    with transaction.atomic():
        course = Course.objects.select_for_update().filter(pk=course_id).first()
        if not course:
            messages.error(request, "Course not found.")
            return redirect('courses:my_courses')

        enrollment = Enrollment.objects.filter(student=request.user, course=course, status='enrolled').first()
        if not enrollment:
            messages.warning(request, "You are not currently enrolled in this course.")
            return redirect('courses:my_courses')

        enrollment.status = 'cancelled'
        enrollment.save()

        # Increment available seats (ensure not exceeding max_seats)
        if course.available_seats < course.max_seats:
            course.available_seats += 1
            course.save()

    messages.success(request, f"Enrollment in {course.course_code} has been cancelled. Seat released.")
    return redirect('courses:my_courses')

@login_required
def my_courses(request):
    """Student dashboard showing active registrations and past history."""
    all_enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    active_enrollments = [e for e in all_enrollments if e.status == 'enrolled']
    cancelled_enrollments = [e for e in all_enrollments if e.status == 'cancelled']

    total_credits = sum(e.course.credits for e in active_enrollments)

    return render(request, 'my_courses.html', {
        'active_enrollments': active_enrollments,
        'cancelled_enrollments': cancelled_enrollments,
        'total_credits': total_credits,
    })

def about(request):
    """About page outlining the Django & MySQL architecture."""
    total_courses = Course.objects.count()
    total_students = User.objects.count()
    total_enrollments = Enrollment.objects.filter(status='enrolled').count()

    stats = {
        'total_courses': total_courses,
        'total_students': total_students,
        'total_enrollments': total_enrollments,
    }
    return render(request, 'about.html', {'stats': stats})

# ========================================================
# Administrator Views
# ========================================================

@admin_required
def admin_dashboard(request):
    """Administrative dashboard displaying metrics and recent activities."""
    total_courses = Course.objects.count()
    total_students = User.objects.filter(
        Q(student_profile__role='student') | Q(student_profile__isnull=True)
    ).count()
    total_enrollments = Enrollment.objects.filter(status='enrolled').count()
    seats_agg = Course.objects.aggregate(total_avail=Sum('available_seats'))
    total_available_seats = seats_agg['total_avail'] or 0

    recent_enrollments = Enrollment.objects.select_related('student', 'course')[:8]

    stats = {
        'total_courses': total_courses,
        'total_students': total_students,
        'total_enrollments': total_enrollments,
        'total_available_seats': total_available_seats,
    }

    return render(request, 'admin/dashboard.html', {
        'stats': stats,
        'recent_enrollments': recent_enrollments,
    })

@admin_required
def admin_manage_courses(request):
    """Course inventory management view with search and filters."""
    search = request.GET.get('search', '').strip()
    department = request.GET.get('department', 'all').strip()

    courses_qs = Course.objects.all()
    if search:
        courses_qs = courses_qs.filter(
            Q(course_title__icontains=search) |
            Q(course_code__icontains=search) |
            Q(instructor__icontains=search)
        )
    if department and department != 'all':
        courses_qs = courses_qs.filter(department=department)

    departments = Course.objects.values_list('department', flat=True).distinct().order_by('department')

    return render(request, 'admin/manage_courses.html', {
        'courses': courses_qs,
        'departments': departments,
        'search': search,
        'selected_dept': department,
    })

@admin_required
def admin_course_create(request):
    """Create new course."""
    departments = Course.objects.values_list('department', flat=True).distinct().order_by('department')
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f"Course '{course.course_code}' created successfully!")
            return redirect('courses:admin_manage_courses')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = CourseForm()

    return render(request, 'admin/course_form.html', {
        'form': form,
        'is_edit': False,
        'departments': departments,
    })

@admin_required
def admin_course_edit(request, course_id):
    """Edit existing course with seat capacity checks."""
    course = get_object_or_404(Course, pk=course_id)
    departments = Course.objects.values_list('department', flat=True).distinct().order_by('department')

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f"Course '{course.course_code}' updated successfully.")
            return redirect('courses:admin_manage_courses')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = CourseForm(instance=course)

    return render(request, 'admin/course_form.html', {
        'form': form,
        'course': course,
        'is_edit': True,
        'departments': departments,
    })

@admin_required
def admin_course_delete(request, course_id):
    """Delete course and associated enrollments safely."""
    if request.method == 'POST':
        course = get_object_or_404(Course, pk=course_id)
        code = course.course_code
        course.delete()
        messages.success(request, f"Course '{code}' and its enrollment history have been permanently deleted.")
    return redirect('courses:admin_manage_courses')

@admin_required
def admin_enrollments(request):
    """Audit log of all student course enrollments."""
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', 'all').strip()

    qs = Enrollment.objects.select_related('student', 'course').all()

    if search:
        qs = qs.filter(
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search) |
            Q(student__email__icontains=search) |
            Q(course__course_code__icontains=search) |
            Q(course__course_title__icontains=search)
        )

    if status_filter and status_filter != 'all':
        qs = qs.filter(status=status_filter)

    return render(request, 'admin/enrollments.html', {
        'enrollments': qs,
        'search': search,
        'status_filter': status_filter,
    })
