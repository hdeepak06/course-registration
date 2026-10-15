from database.db import query_db, transaction

def get_all_courses(search=None, department=None, availability=None):
    """Fetches all courses with optional search, department filter, and availability filter."""
    sql = """
        SELECT c.*, 
               (c.max_seats - c.available_seats) AS enrolled_count,
               COUNT(e.enrollment_id) as active_enrollments
        FROM courses c
        LEFT JOIN enrollments e ON c.course_id = e.course_id AND e.status = 'enrolled'
        WHERE 1=1
    """
    params = []
    
    if search:
        search_term = f"%{search.strip()}%"
        sql += " AND (c.course_title LIKE %s OR c.course_code LIKE %s OR c.instructor LIKE %s OR c.description LIKE %s)"
        params.extend([search_term, search_term, search_term, search_term])
        
    if department and department != 'all':
        sql += " AND c.department = %s"
        params.append(department)
        
    if availability == 'available':
        sql += " AND c.available_seats > 0"
    elif availability == 'full':
        sql += " AND c.available_seats = 0"
        
    sql += " GROUP BY c.course_id ORDER BY c.course_code ASC"
    
    return query_db(sql, tuple(params))

def get_featured_courses(limit=6):
    """Fetches featured courses for homepage."""
    return query_db(
        """
        SELECT c.*, (c.max_seats - c.available_seats) AS enrolled_count
        FROM courses c
        ORDER BY c.course_id ASC
        LIMIT %s
        """,
        (limit,)
    )

def get_course_by_id(course_id):
    """Fetches a single course with enrolled count."""
    return query_db(
        """
        SELECT c.*, (c.max_seats - c.available_seats) AS enrolled_count
        FROM courses c
        WHERE c.course_id = %s
        """,
        (course_id,),
        one=True
    )

def get_course_by_code(course_code):
    """Fetches a single course by course code."""
    return query_db(
        "SELECT * FROM courses WHERE UPPER(course_code) = UPPER(%s)",
        (course_code.strip(),),
        one=True
    )

def get_departments():
    """Returns list of distinct departments."""
    rows = query_db("SELECT DISTINCT department FROM courses WHERE department IS NOT NULL ORDER BY department ASC")
    return [r['department'] for r in rows if r['department']]

def validate_course_data(data, course_id=None):
    """Validates course fields. Returns (is_valid, error_dict)."""
    errors = {}
    code = data.get('course_code', '').strip().upper()
    title = data.get('course_title', '').strip()
    instructor = data.get('instructor', '').strip()
    description = data.get('description', '').strip()
    department = data.get('department', 'General').strip()
    
    try:
        max_seats = int(data.get('max_seats', 0))
    except (ValueError, TypeError):
        errors['max_seats'] = "Maximum seats must be a valid positive integer."
        max_seats = 0

    try:
        credits = int(data.get('credits', 3))
    except (ValueError, TypeError):
        credits = 3

    if not code or len(code) < 2 or len(code) > 20:
        errors['course_code'] = "Course code must be between 2 and 20 characters (e.g. CS101)."
    else:
        # Check uniqueness
        if course_id:
            existing = query_db("SELECT course_id FROM courses WHERE UPPER(course_code) = %s AND course_id != %s", (code, course_id), one=True)
        else:
            existing = query_db("SELECT course_id FROM courses WHERE UPPER(course_code) = %s", (code,), one=True)
        if existing:
            errors['course_code'] = f"Course code '{code}' is already registered."

    if not title or len(title) < 3:
        errors['course_title'] = "Course title must be at least 3 characters long."

    if not instructor or len(instructor) < 2:
        errors['instructor'] = "Instructor name is required."

    if not description or len(description) < 10:
        errors['description'] = "Course description must be at least 10 characters long."

    if max_seats <= 0:
        errors['max_seats'] = "Maximum seats must be greater than 0."

    if credits < 1 or credits > 10:
        errors['credits'] = "Credits must be between 1 and 10."

    return (len(errors) == 0), errors

def create_course(data):
    """Inserts a new course into database."""
    code = data['course_code'].strip().upper()
    title = data['course_title'].strip()
    instructor = data['instructor'].strip()
    description = data['description'].strip()
    department = data.get('department', 'Computer Science').strip()
    max_seats = int(data['max_seats'])
    available_seats = int(data.get('available_seats', max_seats))
    credits = int(data.get('credits', 3))

    # ensure available_seats is valid
    if available_seats > max_seats:
        available_seats = max_seats
    if available_seats < 0:
        available_seats = 0

    result = query_db(
        """
        INSERT INTO courses (course_code, course_title, description, instructor, max_seats, available_seats, department, credits)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (code, title, description, instructor, max_seats, available_seats, department, credits),
        commit=True
    )
    return result['lastrowid']

def update_course(course_id, data):
    """Updates an existing course safely and adjusts capacity properly."""
    course = get_course_by_id(course_id)
    if not course:
        return False, "Course not found."

    code = data['course_code'].strip().upper()
    title = data['course_title'].strip()
    instructor = data['instructor'].strip()
    description = data['description'].strip()
    department = data.get('department', course['department']).strip()
    new_max_seats = int(data['max_seats'])
    credits = int(data.get('credits', course['credits']))

    # Currently occupied seats
    occupied_seats = course['max_seats'] - course['available_seats']
    if new_max_seats < occupied_seats:
        return False, f"Maximum seats cannot be set lower than currently enrolled students ({occupied_seats})."

    # New available seats is new max minus occupied seats
    new_available_seats = new_max_seats - occupied_seats

    query_db(
        """
        UPDATE courses 
        SET course_code = %s,
            course_title = %s,
            description = %s,
            instructor = %s,
            max_seats = %s,
            available_seats = %s,
            department = %s,
            credits = %s
        WHERE course_id = %s
        """,
        (code, title, description, instructor, new_max_seats, new_available_seats, department, credits, course_id),
        commit=True
    )
    return True, "Course updated successfully."

def delete_course(course_id):
    """Deletes a course and associated enrollments via cascade."""
    with transaction() as (conn, cursor):
        cursor.execute("DELETE FROM enrollments WHERE course_id = %s", (course_id,))
        cursor.execute("DELETE FROM courses WHERE course_id = %s", (course_id,))
    return True
