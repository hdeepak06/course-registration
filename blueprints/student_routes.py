from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.auth_service import login_required
from services.enrollment_service import (
    get_student_enrollments,
    enroll_student,
    cancel_enrollment
)
from services.course_service import get_course_by_id

student_bp = Blueprint('student', __name__)

@student_bp.route('/my-courses')
@login_required
def my_courses():
    """Student dashboard showing all active enrollments and course registration history."""
    student_id = session.get('user_id')
    enrollments = get_student_enrollments(student_id)
    
    active_enrollments = [e for e in enrollments if e['status'] == 'enrolled']
    cancelled_enrollments = [e for e in enrollments if e['status'] == 'cancelled']
    
    total_credits = sum(e.get('credits', 3) for e in active_enrollments)

    return render_template(
        'my_courses.html',
        active_enrollments=active_enrollments,
        cancelled_enrollments=cancelled_enrollments,
        total_credits=total_credits
    )

@student_bp.route('/courses/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll(course_id):
    """Enrolls the active student into the specified course with atomic validation."""
    if session.get('role') == 'administrator':
        flash("Administrators cannot enroll as students. Please use a student account.", "warning")
        return redirect(url_for('course.course_detail', course_id=course_id))

    student_id = session.get('user_id')
    success, message = enroll_student(student_id, course_id)

    if success:
        flash(message, "success")
        return redirect(url_for('student.my_courses'))
    else:
        flash(message, "danger")
        return redirect(request.referrer or url_for('course.course_detail', course_id=course_id))

@student_bp.route('/courses/<int:course_id>/cancel', methods=['POST'])
@login_required
def cancel(course_id):
    """Cancels enrollment for the active student with atomic seat restoration."""
    student_id = session.get('user_id')
    success, message = cancel_enrollment(student_id, course_id)

    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(request.referrer or url_for('student.my_courses'))
