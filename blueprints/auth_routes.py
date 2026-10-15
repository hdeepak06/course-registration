from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.auth_service import (
    validate_registration_input,
    register_student,
    authenticate_user,
    login_user,
    logout_user
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handles student account registration with frontend & backend validation."""
    if 'user_id' in session:
        return redirect(url_for('course.index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        is_valid, error = validate_registration_input(full_name, email, password, confirm_password)
        if not is_valid:
            flash(error, "danger")
            return render_template('register.html', full_name=full_name, email=email)

        try:
            student_id = register_student(full_name, email, password)
            flash("Account created successfully! Please log in with your credentials.", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash("An error occurred while creating your account. Please try again.", "danger")
            return render_template('register.html', full_name=full_name, email=email)

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user authentication with secure session establishment."""
    if 'user_id' in session:
        if session.get('role') == 'administrator':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.my_courses'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        next_url = request.args.get('next')

        user, error = authenticate_user(email, password)
        if error:
            flash(error, "danger")
            return render_template('login.html', email=email)

        login_user(user)
        flash(f"Welcome back, {user['full_name']}!", "success")

        if next_url and next_url.startswith('/'):
            return redirect(next_url)

        if user['role'] == 'administrator':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.my_courses'))

    return render_template('login.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Logs out the active user and clears session state."""
    logout_user()
    flash("You have been securely logged out.", "info")
    return redirect(url_for('course.index'))
