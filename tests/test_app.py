import os
import sys
import unittest

# Ensure application path is included
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.db import query_db
from database.init_db import main as init_db_main

class CourseConnectTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize fresh database state
        init_db_main()

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

    def test_01_homepage_renders(self):
        """Test homepage loads with hero, headlines, and golden CTA buttons."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Discover Courses.", res.data)
        self.assertIn(b"Build Your Future.", res.data)
        self.assertIn(b"Explore Courses", res.data)
        self.assertIn(b"btn-gold", res.data)
        self.assertIn(b"Total Courses", res.data)

    def test_02_explore_courses_and_search(self):
        """Test exploring courses and search query filtering."""
        res = self.client.get('/courses')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"CS101", res.data)

        # Search for Python
        search_res = self.client.get('/courses?search=Python')
        self.assertEqual(search_res.status_code, 200)
        self.assertIn(b"Introduction to Computer Science &amp; Python", search_res.data)

    def test_03_course_details_view(self):
        """Test viewing course details page."""
        course = query_db("SELECT course_id FROM courses WHERE course_code = 'CS101'", one=True)
        res = self.client.get(f"/courses/{course['course_id']}")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Dr. Alan Turing", res.data)
        self.assertIn(b"Remaining Available", res.data)
        self.assertIn(b"Maximum Capacity", res.data)

    def test_04_student_registration_validation(self):
        """Test registration validation: password mismatch and short password."""
        # Password mismatch
        res = self.client.post('/register', data={
            'full_name': 'Test User',
            'email': 'mismatch@student.edu',
            'password': 'Password123',
            'confirm_password': 'DifferentPassword123'
        }, follow_redirects=True)
        self.assertIn(b"Passwords do not match.", res.data)

        # Successful registration
        res_ok = self.client.post('/register', data={
            'full_name': 'New Student',
            'email': 'new.student@student.edu',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }, follow_redirects=True)
        self.assertIn(b"Account created successfully", res_ok.data)

    def test_05_student_login_and_logout(self):
        """Test student login and logout cycle."""
        # Invalid password
        res_fail = self.client.post('/login', data={
            'email': 'sarah.jenkins@student.edu',
            'password': 'WrongPassword'
        }, follow_redirects=True)
        self.assertIn(b"Invalid email or password", res_fail.data)

        # Valid login
        res_ok = self.client.post('/login', data={
            'email': 'sarah.jenkins@student.edu',
            'password': 'Student@123'
        }, follow_redirects=True)
        self.assertIn(b"Welcome back, Sarah Jenkins", res_ok.data)

        # Logout
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b"You have been securely logged out.", res_logout.data)

    def test_06_role_based_access_control(self):
        """Test that unauthorized users and students cannot access admin routes."""
        # Guest access to admin
        res_guest = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b"Administrator login required", res_guest.data)

        # Student access to admin
        self.client.post('/login', data={'email': 'sarah.jenkins@student.edu', 'password': 'Student@123'})
        res_student = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b"Access denied. Administrator privileges required.", res_student.data)
        self.client.get('/logout')

    def test_07_admin_dashboard_and_crud(self):
        """Test administrator dashboard access and course addition."""
        self.client.post('/login', data={'email': 'admin@courseconnect.edu', 'password': 'Admin@123'})
        
        dash_res = self.client.get('/admin')
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b"Admin Dashboard", dash_res.data)

        # Create new course
        add_res = self.client.post('/admin/courses/new', data={
            'course_code': 'TEST999',
            'course_title': 'Automated Systems Testing',
            'instructor': 'Prof. John Von Neumann',
            'department': 'Computer Science',
            'credits': 4,
            'max_seats': 20,
            'description': 'A comprehensive test course verifying automated test execution.'
        }, follow_redirects=True)
        self.assertIn(b"TEST999", add_res.data)

        # Verify duplicate code is rejected
        dup_res = self.client.post('/admin/courses/new', data={
            'course_code': 'TEST999',
            'course_title': 'Duplicate Test Course',
            'instructor': 'Someone',
            'department': 'Computer Science',
            'credits': 3,
            'max_seats': 20,
            'description': 'Duplicate course code attempt.'
        }, follow_redirects=True)
        self.assertIn(b"already registered", dup_res.data)

        self.client.get('/logout')

    def test_08_enrollment_transaction_and_capacity_rules(self):
        """Test enrollment transactions: seat decrement, duplicate prevention, and seat increment on cancellation."""
        # Log in as Elena Rostova
        self.client.post('/login', data={'email': 'elena.rostova@student.edu', 'password': 'Student@123'})
        
        # Elena wants to enroll in CS310 (Dr. Grace Hopper)
        course = query_db("SELECT course_id, available_seats FROM courses WHERE course_code = 'CS310'", one=True)
        initial_seats = course['available_seats']
        course_id = course['course_id']

        # Enroll
        enroll_res = self.client.post(f"/courses/{course_id}/enroll", follow_redirects=True)
        self.assertIn(b"Successfully enrolled in CS310", enroll_res.data)

        # Verify seat decremented by 1
        updated_course = query_db("SELECT available_seats FROM courses WHERE course_id = %s", (course_id,), one=True)
        self.assertEqual(updated_course['available_seats'], initial_seats - 1)

        # Attempt duplicate enrollment
        dup_enroll = self.client.post(f"/courses/{course_id}/enroll", follow_redirects=True)
        self.assertIn(b"already enrolled", dup_enroll.data)

        # Cancel enrollment
        cancel_res = self.client.post(f"/courses/{course_id}/cancel", follow_redirects=True)
        self.assertIn(b"has been cancelled. Seat released.", cancel_res.data)

        # Verify seat was restored (+1)
        restored_course = query_db("SELECT available_seats FROM courses WHERE course_id = %s", (course_id,), one=True)
        self.assertEqual(restored_course['available_seats'], initial_seats)

        # Attempt to enroll in full course (AI415 with 0 seats)
        full_course = query_db("SELECT course_id FROM courses WHERE course_code = 'AI415'", one=True)
        full_res = self.client.post(f"/courses/{full_course['course_id']}/enroll", follow_redirects=True)
        self.assertIn(b"maximum capacity", full_res.data)

        self.client.get('/logout')

if __name__ == '__main__':
    unittest.main()
