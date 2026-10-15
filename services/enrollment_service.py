from database.db import query_db, transaction
import logging

logger = logging.getLogger(__name__)

def get_student_enrollments(student_id):
    """Returns list of courses the student is currently enrolled in, plus past history."""
    sql = """
        SELECT e.enrollment_id, e.student_id, e.course_id, e.enrollment_date, e.status,
               c.course_code, c.course_title, c.description, c.instructor,
               c.max_seats, c.available_seats, c.department, c.credits
        FROM enrollments e
        JOIN courses c ON e.course_id = c.course_id
        WHERE e.student_id = %s
        ORDER BY (e.status = 'enrolled') DESC, e.enrollment_date DESC
    """
    return query_db(sql, (student_id,))

def get_enrolled_course_ids(student_id):
    """Returns set of course_ids where student status is 'enrolled'."""
    rows = query_db(
        "SELECT course_id FROM enrollments WHERE student_id = %s AND status = 'enrolled'",
        (student_id,)
    )
    return {r['course_id'] for r in rows}

def is_student_enrolled(student_id, course_id):
    """Checks whether a student is currently enrolled in a course."""
    row = query_db(
        "SELECT enrollment_id FROM enrollments WHERE student_id = %s AND course_id = %s AND status = 'enrolled'",
        (student_id, course_id),
        one=True
    )
    return bool(row)

def enroll_student(student_id, course_id):
    """
    Safely enrolls a student in a course using an ACID transaction.
    - Validates student and course exist
    - Prevents duplicate active enrollment
    - Validates available seats > 0
    - Updates seats and records enrollment atomically
    Returns (success: bool, message: str)
    """
    try:
        with transaction() as (conn, cursor):
            # 1. Validate student
            cursor.execute("SELECT student_id, full_name, email FROM students WHERE student_id = %s", (student_id,))
            student = cursor.fetchone()
            if not student:
                return False, "Invalid student account."

            # 2. Fetch course with locked status
            cursor.execute(
                "SELECT course_id, course_code, course_title, available_seats, max_seats FROM courses WHERE course_id = %s",
                (course_id,)
            )
            course = cursor.fetchone()
            if not course:
                return False, "Course does not exist or has been removed."

            # 3. Check duplicate enrollment
            cursor.execute(
                "SELECT enrollment_id, status FROM enrollments WHERE student_id = %s AND course_id = %s",
                (student_id, course_id)
            )
            existing_enrollment = cursor.fetchone()

            if existing_enrollment and existing_enrollment['status'] == 'enrolled':
                return False, f"You are already enrolled in {course['course_code']} ({course['course_title']})."

            # 4. Check seat availability
            if course['available_seats'] <= 0:
                return False, f"Enrollment failed: {course['course_code']} is at maximum capacity (0 seats available)."

            # 5. Insert or update enrollment
            if existing_enrollment:
                # Re-enrolling after previous cancellation
                cursor.execute(
                    "UPDATE enrollments SET status = 'enrolled', enrollment_date = CURRENT_TIMESTAMP WHERE enrollment_id = %s",
                    (existing_enrollment['enrollment_id'],)
                )
            else:
                cursor.execute(
                    "INSERT INTO enrollments (student_id, course_id, status) VALUES (%s, %s, 'enrolled')",
                    (student_id, course_id)
                )

            # 6. Decrement available seats
            cursor.execute(
                "UPDATE courses SET available_seats = available_seats - 1 WHERE course_id = %s AND available_seats > 0",
                (course_id,)
            )

            # Verify seat was actually decremented
            if cursor.rowcount == 0:
                conn.rollback()
                return False, "Enrollment failed: Course just filled up. Please select another course."

        return True, f"Successfully enrolled in {course['course_code']}: {course['course_title']}!"

    except Exception as e:
        logger.error(f"Enrollment transaction error: {e}")
        return False, "A database error occurred during enrollment. Please try again."

def cancel_enrollment(student_id, course_id):
    """
    Safely cancels a student's enrollment using an ACID transaction.
    - Validates active enrollment
    - Sets status to 'cancelled'
    - Increments available seats on course
    Returns (success: bool, message: str)
    """
    try:
        with transaction() as (conn, cursor):
            # 1. Fetch course details
            cursor.execute(
                "SELECT course_id, course_code, course_title, available_seats, max_seats FROM courses WHERE course_id = %s",
                (course_id,)
            )
            course = cursor.fetchone()
            if not course:
                return False, "Course does not exist."

            # 2. Check active enrollment
            cursor.execute(
                "SELECT enrollment_id FROM enrollments WHERE student_id = %s AND course_id = %s AND status = 'enrolled'",
                (student_id, course_id)
            )
            enrollment = cursor.fetchone()
            if not enrollment:
                return False, "You are not currently enrolled in this course."

            # 3. Mark enrollment cancelled
            cursor.execute(
                "UPDATE enrollments SET status = 'cancelled' WHERE enrollment_id = %s",
                (enrollment['enrollment_id'],)
            )

            # 4. Increment available seats (ensure not exceeding max_seats)
            cursor.execute(
                "UPDATE courses SET available_seats = available_seats + 1 WHERE course_id = %s AND available_seats < max_seats",
                (course_id,)
            )

        return True, f"Enrollment in {course['course_code']} has been cancelled. Seat released."

    except Exception as e:
        logger.error(f"Cancellation transaction error: {e}")
        return False, "A database error occurred during cancellation. Please try again."

def get_recent_enrollments(limit=10):
    """Retrieves recent enrollment audit records with student and course details for admin."""
    sql = """
        SELECT e.enrollment_id, e.enrollment_date, e.status,
               s.student_id, s.full_name as student_name, s.email as student_email,
               c.course_id, c.course_code, c.course_title, c.department
        FROM enrollments e
        JOIN students s ON e.student_id = s.student_id
        JOIN courses c ON e.course_id = c.course_id
        ORDER BY e.enrollment_date DESC
        LIMIT %s
    """
    return query_db(sql, (limit,))

def get_all_enrollments(search=None, status_filter=None):
    """Retrieves all enrollments with search and status filter for administrative management."""
    sql = """
        SELECT e.enrollment_id, e.enrollment_date, e.status,
               s.student_id, s.full_name as student_name, s.email as student_email,
               c.course_id, c.course_code, c.course_title, c.department
        FROM enrollments e
        JOIN students s ON e.student_id = s.student_id
        JOIN courses c ON e.course_id = c.course_id
        WHERE 1=1
    """
    params = []
    if search:
        search_term = f"%{search.strip()}%"
        sql += " AND (s.full_name LIKE %s OR s.email LIKE %s OR c.course_code LIKE %s OR c.course_title LIKE %s)"
        params.extend([search_term, search_term, search_term, search_term])
        
    if status_filter and status_filter != 'all':
        sql += " AND e.status = %s"
        params.append(status_filter)
        
    sql += " ORDER BY e.enrollment_date DESC"
    return query_db(sql, tuple(params))
