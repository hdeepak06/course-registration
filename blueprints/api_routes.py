from flask import Blueprint, jsonify, request
from services.course_service import get_all_courses, get_course_by_id
from services.stats_service import get_platform_statistics

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/courses/search')
def api_search_courses():
    """Returns JSON list of courses matching search query and filters."""
    search = request.args.get('q', '').strip()
    department = request.args.get('dept', 'all').strip()
    availability = request.args.get('avail', 'all').strip()

    courses = get_all_courses(search=search, department=department, availability=availability)
    return jsonify({
        'status': 'success',
        'count': len(courses),
        'courses': courses
    })

@api_bp.route('/courses/<int:course_id>')
def api_course_detail(course_id):
    """Returns JSON representation of a single course."""
    course = get_course_by_id(course_id)
    if not course:
        return jsonify({'status': 'error', 'message': 'Course not found'}), 404
    return jsonify({'status': 'success', 'course': course})

@api_bp.route('/stats')
def api_stats():
    """Returns live platform metrics."""
    stats = get_platform_statistics()
    return jsonify({'status': 'success', 'stats': stats})
