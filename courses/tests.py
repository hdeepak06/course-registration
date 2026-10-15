from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import StudentProfile
from courses.models import Course, Enrollment

class CourseConnectDjangoTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Admin
        self.admin_user = User.objects.create_superuser(
            username='admin@courseconnect.edu',
            email='admin@courseconnect.edu',
            password='Admin@123',
            first_name='Alexander',
            last_name='Wright'
        )
        self.admin_profile = self.admin_user.student_profile
        self.admin_profile.role = 'administrator'
        self.admin_profile.save()

        # Create Student
        self.student_user = User.objects.create_user(
            username='sarah.jenkins@student.edu',
            email='sarah.jenkins@student.edu',
            password='Student@123',
            first_name='Sarah',
            last_name='Jenkins'
        )

        # Create Sample Course
        self.course_cs101 = Course.objects.create(
            course_code='CS101',
            course_title='Introduction to Computer Science & Python',
            description='Computational problem-solving and algorithms with Python.',
            instructor='Dr. Alan Turing',
            department='Computer Science',
            credits=4,
            max_seats=30,
            available_seats=28
        )

        # Create Full Course
        self.full_course = Course.objects.create(
            course_code='AI415',
            course_title='Natural Language Processing',
            description='Advanced language models and deep neural nets.',
            instructor='Dr. Geoffrey Hinton',
            department='Artificial Intelligence',
            credits=4,
            max_seats=20,
            available_seats=0
        )

    def test_01_homepage_renders(self):
        """Test homepage loads with hero, headlines, statistics, and golden buttons."""
        res = self.client.get(reverse('courses:index'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Discover Courses.")
        self.assertContains(res, "Build Your Future.")
        self.assertContains(res, "Explore Courses")
        self.assertContains(res, "btn-gold")
        self.assertContains(res, "Total Courses")

    def test_02_explore_courses_and_search(self):
        """Test explore courses view with keyword searching."""
        res = self.client.get(reverse('courses:explore'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "CS101")

        search_res = self.client.get(reverse('courses:explore') + '?search=Python')
        self.assertEqual(search_res.status_code, 200)
        self.assertContains(search_res, "Introduction to Computer Science &amp; Python")

    def test_03_course_details_view(self):
        """Test viewing course details page."""
        res = self.client.get(reverse('courses:course_detail', args=[self.course_cs101.id]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Dr. Alan Turing")
        self.assertContains(res, "Remaining Available")
        self.assertContains(res, "Maximum Capacity")

    def test_04_student_registration_validation(self):
        """Test registration validation: password mismatch and successful sign up."""
        # Password mismatch
        res_mismatch = self.client.post(reverse('accounts:register'), {
            'full_name': 'New Student',
            'email': 'new.student@university.edu',
            'password': 'Password123',
            'confirm_password': 'DifferentPassword'
        }, follow=True)
        self.assertContains(res_mismatch, "Passwords do not match.")

        # Valid registration
        res_ok = self.client.post(reverse('accounts:register'), {
            'full_name': 'New Student',
            'email': 'new.student@university.edu',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }, follow=True)
        self.assertContains(res_ok, "Account created successfully")
        self.assertTrue(User.objects.filter(email='new.student@university.edu').exists())

    def test_05_student_login_and_logout(self):
        """Test login authentication and logout flow."""
        # Invalid login
        res_fail = self.client.post(reverse('accounts:login'), {
            'email': 'sarah.jenkins@student.edu',
            'password': 'WrongPassword'
        }, follow=True)
        self.assertContains(res_fail, "Invalid email or password")

        # Valid login
        res_ok = self.client.post(reverse('accounts:login'), {
            'email': 'sarah.jenkins@student.edu',
            'password': 'Student@123'
        }, follow=True)
        self.assertContains(res_ok, "Welcome back, Sarah Jenkins")

        # Logout
        res_logout = self.client.get(reverse('accounts:logout'), follow=True)
        self.assertContains(res_logout, "You have been securely logged out.")

    def test_06_role_based_access_control(self):
        """Test role enforcement: unauthenticated users and students cannot access admin views."""
        # Anonymous user
        res_anon = self.client.get(reverse('courses:admin_dashboard'), follow=True)
        self.assertContains(res_anon, "Administrator login required")

        # Student user
        self.client.login(username='sarah.jenkins@student.edu', password='Student@123')
        res_student = self.client.get(reverse('courses:admin_dashboard'), follow=True)
        self.assertContains(res_student, "Access denied. Administrator privileges required.")
        self.client.logout()

    def test_07_admin_course_crud(self):
        """Test administrator dashboard access, course creation, and duplicate check."""
        self.client.login(username='admin@courseconnect.edu', password='Admin@123')

        dash_res = self.client.get(reverse('courses:admin_dashboard'))
        self.assertEqual(dash_res.status_code, 200)
        self.assertContains(dash_res, "Admin Dashboard")

        # Create new course
        create_res = self.client.post(reverse('courses:admin_course_create'), {
            'course_code': 'SE450',
            'course_title': 'Software Architecture Patterns',
            'department': 'Software Engineering',
            'instructor': 'Dr. Margaret Hamilton',
            'credits': 4,
            'max_seats': 35,
            'description': 'Advanced design patterns, architectural tradeoffs, and testing.'
        }, follow=True)
        self.assertContains(create_res, "SE450")
        self.assertTrue(Course.objects.filter(course_code='SE450').exists())

        # Duplicate course code should fail
        dup_res = self.client.post(reverse('courses:admin_course_create'), {
            'course_code': 'SE450',
            'course_title': 'Duplicate SE450',
            'department': 'Software Engineering',
            'instructor': 'Someone',
            'credits': 3,
            'max_seats': 20,
            'description': 'Duplicate test'
        }, follow=True)
        self.assertContains(dup_res, "already registered")

        self.client.logout()

    def test_08_transactional_enrollment_and_capacity(self):
        """Test enrollment transactions: seat decrement, duplicate prevention, seat increment on cancellation, and full course check."""
        self.client.login(username='sarah.jenkins@student.edu', password='Student@123')
        initial_seats = self.course_cs101.available_seats

        # 1. Enroll
        enroll_res = self.client.post(reverse('courses:enroll', args=[self.course_cs101.id]), follow=True)
        self.assertContains(enroll_res, "Successfully enrolled in CS101")

        self.course_cs101.refresh_from_db()
        self.assertEqual(self.course_cs101.available_seats, initial_seats - 1)
        self.assertTrue(Enrollment.objects.filter(student=self.student_user, course=self.course_cs101, status='enrolled').exists())

        # 2. Duplicate enrollment
        dup_res = self.client.post(reverse('courses:enroll', args=[self.course_cs101.id]), follow=True)
        self.assertContains(dup_res, "already enrolled")

        # 3. Cancel enrollment
        cancel_res = self.client.post(reverse('courses:cancel', args=[self.course_cs101.id]), follow=True)
        self.assertContains(cancel_res, "has been cancelled. Seat released.")

        self.course_cs101.refresh_from_db()
        self.assertEqual(self.course_cs101.available_seats, initial_seats)

        # 4. Attempt to enroll in full course
        full_res = self.client.post(reverse('courses:enroll', args=[self.full_course.id]), follow=True)
        self.assertContains(full_res, "maximum capacity")

        self.client.logout()
