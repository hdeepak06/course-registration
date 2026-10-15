from flask import Blueprint, render_template, request, session
from services.course_service import (
    get_all_courses,
    get_featured_courses,
    get_course_by_id,
    get_departments
)
from services.stats_service import get_platform_statistics
from services.enrollment_service import get_enrolled_course_ids

course_bp = Blueprint('course', __name__)

@course_bp.route('/')
def index():
    """Homepage showcasing hero, SQL-backed platform stats, and featured courses."""
    stats = get_platform_statistics()
    featured_courses = get_featured_courses(limit=6)
    
    enrolled_ids = set()
    if 'user_id' in session and session.get('role') == 'student':
        enrolled_ids = get_enrolled_course_ids(session['user_id'])
        
    return render_template(
        'index.html',
        stats=stats,
        courses=featured_courses,
        enrolled_ids=enrolled_ids
    )

@course_bp.route('/courses')
def explore():
    """Explore and search all available courses with live filter parameters."""
    search = request.args.get('search', '').strip()
    department = request.args.get('department', 'all').strip()
    availability = request.args.get('availability', 'all').strip()

    courses = get_all_courses(search=search, department=department, availability=availability)
    departments = get_departments()
    
    enrolled_ids = set()
    if 'user_id' in session and session.get('role') == 'student':
        enrolled_ids = get_enrolled_course_ids(session['user_id'])

    return render_template(
        'courses.html',
        courses=courses,
        departments=departments,
        search=search,
        selected_dept=department,
        selected_avail=availability,
        enrolled_ids=enrolled_ids
    )

@course_bp.route('/courses/<int:course_id>')
def course_detail(course_id):
    """View detailed information about a single course."""
    course = get_course_by_id(course_id)
    if not course:
        return render_template('404.html', message="The requested course could not be found."), 404

    is_enrolled = False
    if 'user_id' in session and session.get('role') == 'student':
        enrolled_ids = get_enrolled_course_ids(session['user_id'])
        is_enrolled = course_id in enrolled_ids

    return render_template(
        'course_detail.html',
        course=course,
        is_enrolled=is_enrolled
    )

@course_bp.route('/about')
def about():
    """About CourseConnect engineering architecture and portfolio details."""
    stats = get_platform_statistics()
    return render_template('about.html', stats=stats)
