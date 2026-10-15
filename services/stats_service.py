from database.db import query_db

def get_platform_statistics():
    """Computes real-time platform statistics via SQL aggregation."""
    # 1. Total Courses
    course_stats = query_db(
        """
        SELECT 
            COUNT(*) as total_courses,
            COALESCE(SUM(max_seats), 0) as total_seats,
            COALESCE(SUM(available_seats), 0) as total_available_seats
        FROM courses
        """,
        one=True
    ) or {'total_courses': 0, 'total_seats': 0, 'total_available_seats': 0}

    # 2. Registered Students (role = 'student')
    student_stats = query_db(
        "SELECT COUNT(*) as total_students FROM students WHERE role = 'student'",
        one=True
    ) or {'total_students': 0}

    # 3. Total Active Enrollments
    enrollment_stats = query_db(
        "SELECT COUNT(*) as total_enrollments FROM enrollments WHERE status = 'enrolled'",
        one=True
    ) or {'total_enrollments': 0}

    # 4. Department distribution
    dept_distribution = query_db(
        """
        SELECT department, COUNT(*) as count 
        FROM courses 
        WHERE department IS NOT NULL 
        GROUP BY department 
        ORDER BY count DESC
        """
    ) or []

    return {
        'total_courses': course_stats.get('total_courses', 0),
        'total_seats': course_stats.get('total_seats', 0),
        'total_available_seats': course_stats.get('total_available_seats', 0),
        'total_students': student_stats.get('total_students', 0),
        'total_enrollments': enrollment_stats.get('total_enrollments', 0),
        'departments': dept_distribution
    }
