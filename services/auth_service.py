import re
from functools import wraps
from flask import session, redirect, url_for, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import query_db

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

def validate_registration_input(full_name, email, password, confirm_password):
    """Validates registration input fields. Returns (is_valid, error_message)."""
    if not full_name or len(full_name.strip()) < 2:
        return False, "Full name must be at least 2 characters long."
    
    if len(full_name.strip()) > 100:
        return False, "Full name cannot exceed 100 characters."
        
    if not email or not re.match(EMAIL_REGEX, email.strip()):
        return False, "Please provide a valid email address."
        
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."
        
    if password != confirm_password:
        return False, "Passwords do not match."
        
    # Check if email is already registered
    existing_user = query_db(
        "SELECT student_id FROM students WHERE email = %s",
        (email.strip().lower(),),
        one=True
    )
    if existing_user:
        return False, "An account with this email address already exists. Please log in."
        
    return True, None

def register_student(full_name, email, password, role="student"):
    """Registers a new student securely with hashed password."""
    clean_name = full_name.strip()
    clean_email = email.strip().lower()
    pw_hash = generate_password_hash(password)
    
    result = query_db(
        "INSERT INTO students (full_name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
        (clean_name, clean_email, pw_hash, role),
        commit=True
    )
    return result['lastrowid']

def authenticate_user(email, password):
    """Authenticates a user by email and password. Returns user dict or None."""
    if not email or not password:
        return None, "Email and password are required."
        
    user = query_db(
        "SELECT student_id, full_name, email, password_hash, role, created_at FROM students WHERE email = %s",
        (email.strip().lower(),),
        one=True
    )
    
    if not user:
        return None, "Invalid email or password."
        
    if not check_password_hash(user['password_hash'], password):
        return None, "Invalid email or password."
        
    return user, None

def login_user(user):
    """Establishes user session securely."""
    session.clear()
    session['user_id'] = user['student_id']
    session['user_name'] = user['full_name']
    session['user_email'] = user['email']
    session['role'] = user['role']
    session.permanent = True

def logout_user():
    """Clears user session."""
    session.clear()

def get_current_user():
    """Retrieves current authenticated user from session, or None."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return query_db(
        "SELECT student_id, full_name, email, role, created_at FROM students WHERE student_id = %s",
        (user_id,),
        one=True
    )

def login_required(f):
    """Decorator to enforce authenticated session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to enforce administrator role on the server."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Administrator login required.", "warning")
            return redirect(url_for('auth.login'))
        if session.get('role') != 'administrator':
            flash("Access denied. Administrator privileges required.", "danger")
            return redirect(url_for('course.index'))
        return f(*args, **kwargs)
    return decorated_function
