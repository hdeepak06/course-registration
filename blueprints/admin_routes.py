from flask import Blueprint, render_template, request, redirect, url_for, flash
from services.auth_service import admin_required
from services.course_service import (
    get_all_courses,
    get_course_by_id,
    create_course,
    update_course,
    delete_course,
    validate_course_data,
    get_departments
)
from services.enrollment_service import (
    get_recent_enrollments,
    get_all_enrollments
)
from services.stats_service import get_platform_statistics

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/', strict_slashes=False)
@admin_bp.route('', strict_slashes=False)
@admin_required
def dashboard():
    """Administrator dashboard showcasing aggregate metrics and recent activities."""
    stats = get_platform_statistics()
    recent_enrollments = get_recent_enrollments(limit=8)
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_enrollments=recent_enrollments
    )

@admin_bp.route('/courses')
@admin_required
def manage_courses():
    """Course management inventory with search, capacity stats, edit, and delete options."""
    search = request.args.get('search', '').strip()
    department = request.args.get('department', 'all').strip()
    courses = get_all_courses(search=search, department=department)
    departments = get_departments()
    return render_template(
        'admin/manage_courses.html',
        courses=courses,
        departments=departments,
        search=search,
        selected_dept=department
    )

@admin_bp.route('/courses/new', methods=['GET', 'POST'])
@admin_required
def add_course():
    """Add new course with server-side validation."""
    if request.method == 'POST':
        data = {
            'course_code': request.form.get('course_code', ''),
            'course_title': request.form.get('course_title', ''),
            'instructor': request.form.get('instructor', ''),
            'department': request.form.get('department', ''),
            'credits': request.form.get('credits', 3),
            'max_seats': request.form.get('max_seats', 0),
            'description': request.form.get('description', '')
        }

        is_valid, errors = validate_course_data(data)
        if not is_valid:
            for field, err in errors.items():
                flash(err, "danger")
            return render_template('admin/course_form.html', course=data, is_edit=False, departments=get_departments())

        try:
            course_id = create_course(data)
            flash(f"Course '{data['course_code']}' created successfully!", "success")
            return redirect(url_for('admin.manage_courses'))
        except Exception as e:
            flash(f"Failed to create course: {str(e)}", "danger")
            return render_template('admin/course_form.html', course=data, is_edit=False, departments=get_departments())

    return render_template('admin/course_form.html', course={}, is_edit=False, departments=get_departments())

@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_course(course_id):
    """Edit existing course with seat capacity constraints."""
    course = get_course_by_id(course_id)
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for('admin.manage_courses'))

    if request.method == 'POST':
        data = {
            'course_code': request.form.get('course_code', ''),
            'course_title': request.form.get('course_title', ''),
            'instructor': request.form.get('instructor', ''),
            'department': request.form.get('department', ''),
            'credits': request.form.get('credits', 3),
            'max_seats': request.form.get('max_seats', 0),
            'description': request.form.get('description', '')
        }

        is_valid, errors = validate_course_data(data, course_id=course_id)
        if not is_valid:
            for field, err in errors.items():
                flash(err, "danger")
            data['course_id'] = course_id
            data['available_seats'] = course['available_seats']
            return render_template('admin/course_form.html', course=data, is_edit=True, departments=get_departments())

        success, message = update_course(course_id, data)
        if success:
            flash(message, "success")
            return redirect(url_for('admin.manage_courses'))
        else:
            flash(message, "danger")
            data['course_id'] = course_id
            return render_template('admin/course_form.html', course=data, is_edit=True, departments=get_departments())

    return render_template('admin/course_form.html', course=course, is_edit=True, departments=get_departments())

@admin_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@admin_required
def remove_course(course_id):
    """Delete course and associated enrollments safely."""
    course = get_course_by_id(course_id)
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for('admin.manage_courses'))

    try:
        delete_course(course_id)
        flash(f"Course '{course['course_code']}' and its enrollment history have been permanently deleted.", "success")
    except Exception as e:
        flash(f"Failed to delete course: {str(e)}", "danger")

    return redirect(url_for('admin.manage_courses'))

@admin_bp.route('/enrollments')
@admin_required
def view_enrollments():
    """Audit log of all student course enrollments."""
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'all').strip()
    enrollments = get_all_enrollments(search=search, status_filter=status_filter)
    return render_template(
        'admin/enrollments.html',
        enrollments=enrollments,
        search=search,
        status_filter=status_filter
    )
