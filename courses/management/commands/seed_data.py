from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import StudentProfile
from courses.models import Course, Enrollment

SAMPLE_USERS = [
    {
        'username': 'admin@courseconnect.edu',
        'email': 'admin@courseconnect.edu',
        'password': 'Admin@123',
        'first_name': 'Alexander',
        'last_name': 'Wright',
        'is_staff': True,
        'is_superuser': True,
        'role': 'administrator'
    },
    {
        'username': 'sarah.jenkins@student.edu',
        'email': 'sarah.jenkins@student.edu',
        'password': 'Student@123',
        'first_name': 'Sarah',
        'last_name': 'Jenkins',
        'is_staff': False,
        'is_superuser': False,
        'role': 'student'
    },
    {
        'username': 'marcus.chen@student.edu',
        'email': 'marcus.chen@student.edu',
        'password': 'Student@123',
        'first_name': 'Marcus',
        'last_name': 'Chen',
        'is_staff': False,
        'is_superuser': False,
        'role': 'student'
    },
    {
        'username': 'elena.rostova@student.edu',
        'email': 'elena.rostova@student.edu',
        'password': 'Student@123',
        'first_name': 'Elena',
        'last_name': 'Rostova',
        'is_staff': False,
        'is_superuser': False,
        'role': 'student'
    },
    {
        'username': 'david.kim@student.edu',
        'email': 'david.kim@student.edu',
        'password': 'Student@123',
        'first_name': 'David',
        'last_name': 'Kim',
        'is_staff': False,
        'is_superuser': False,
        'role': 'student'
    },
]

SAMPLE_COURSES = [
    {
        'course_code': 'CS101',
        'course_title': 'Introduction to Computer Science & Python',
        'description': 'A comprehensive introduction to computational problem-solving, algorithms, data structures, and Python programming fundamentals with practical projects.',
        'instructor': 'Dr. Alan Turing',
        'department': 'Computer Science',
        'credits': 4,
        'max_seats': 45,
        'available_seats': 43,
    },
    {
        'course_code': 'CS204',
        'course_title': 'Relational Database Design & SQL Engineering',
        'description': 'In-depth study of relational modeling, normalization, indexing strategies, ACID transactions, and advanced SQL query optimization with MySQL.',
        'instructor': 'Prof. Edgar F. Codd',
        'department': 'Information Systems',
        'credits': 3,
        'max_seats': 35,
        'available_seats': 33,
    },
    {
        'course_code': 'CS310',
        'course_title': 'Full-Stack Web Development Architecture',
        'description': 'Design, build, and deploy high-performance web applications using modern front-end technologies, Django backends, and RESTful APIs.',
        'instructor': 'Dr. Grace Hopper',
        'department': 'Software Engineering',
        'credits': 4,
        'max_seats': 40,
        'available_seats': 39,
    },
    {
        'course_code': 'CS402',
        'course_title': 'Distributed Cloud Systems & Microservices',
        'description': 'Architecting resilient cloud services, containerization with Docker, message queues, API gateways, and distributed state consistency.',
        'instructor': 'Prof. Leslie Lamport',
        'department': 'Cloud Computing',
        'credits': 3,
        'max_seats': 30,
        'available_seats': 28,
    },
    {
        'course_code': 'DS201',
        'course_title': 'Applied Data Science & Machine Learning',
        'description': 'Statistical foundations, exploratory data analysis, feature engineering, and supervised/unsupervised machine learning models with Python.',
        'instructor': 'Dr. Fei-Fei Li',
        'department': 'Data Science',
        'credits': 4,
        'max_seats': 35,
        'available_seats': 35,
    },
    {
        'course_code': 'SEC305',
        'course_title': 'Application Security & Cryptographic Systems',
        'description': 'Defensive web security, OWASP top vulnerabilities, authentication tokens, password hashing algorithms, and secure coding practices.',
        'instructor': 'Prof. Bruce Schneier',
        'department': 'Cybersecurity',
        'credits': 3,
        'max_seats': 25,
        'available_seats': 25,
    },
    {
        'course_code': 'MATH220',
        'course_title': 'Discrete Mathematics & Graph Algorithms',
        'description': 'Logic, set theory, combinatorics, graph theory, tree traversals, and mathematical proofs essential for software engineering.',
        'instructor': 'Dr. Ada Lovelace',
        'department': 'Mathematics',
        'credits': 3,
        'max_seats': 50,
        'available_seats': 49,
    },
    {
        'course_code': 'AI415',
        'course_title': 'Natural Language Processing & Large Models',
        'description': 'Vector embeddings, transformer architectures, tokenization, semantic search, and prompt engineering in modern AI software systems.',
        'instructor': 'Dr. Geoffrey Hinton',
        'department': 'Artificial Intelligence',
        'credits': 4,
        'max_seats': 30,
        'available_seats': 0, # Full course for capacity testing!
    },
]

class Command(BaseCommand):
    help = 'Seeds database with sample courses, students, and administrator account.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting CourseConnect database seeding...'))

        # 1. Create Users
        created_users = {}
        for u_data in SAMPLE_USERS:
            user, created = User.objects.get_or_create(
                username=u_data['username'],
                defaults={
                    'email': u_data['email'],
                    'first_name': u_data['first_name'],
                    'last_name': u_data['last_name'],
                    'is_staff': u_data['is_staff'],
                    'is_superuser': u_data['is_superuser'],
                }
            )
            if created:
                user.set_password(u_data['password'])
                user.save()
                profile = user.student_profile
                profile.role = u_data['role']
                profile.save()
                self.stdout.write(self.style.SUCCESS(f"Created user: {user.email} ({u_data['role']})"))
            else:
                user.set_password(u_data['password'])
                user.save()
                profile = user.student_profile
                profile.role = u_data['role']
                profile.save()
                self.stdout.write(f"Updated password for user: {user.email}")
            created_users[user.email] = user

        # 2. Create Courses
        created_courses = {}
        for c_data in SAMPLE_COURSES:
            course, created = Course.objects.update_or_create(
                course_code=c_data['course_code'],
                defaults=c_data
            )
            created_courses[course.course_code] = course
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created course: {course.course_code} - {course.course_title}"))
            else:
                self.stdout.write(f"Updated course: {course.course_code}")

        # 3. Create Sample Enrollments
        sarah = created_users.get('sarah.jenkins@student.edu')
        marcus = created_users.get('marcus.chen@student.edu')
        elena = created_users.get('elena.rostova@student.edu')

        if sarah and 'CS101' in created_courses:
            Enrollment.objects.get_or_create(student=sarah, course=created_courses['CS101'], defaults={'status': 'enrolled'})
        if sarah and 'CS204' in created_courses:
            Enrollment.objects.get_or_create(student=sarah, course=created_courses['CS204'], defaults={'status': 'enrolled'})
        if marcus and 'CS101' in created_courses:
            Enrollment.objects.get_or_create(student=marcus, course=created_courses['CS101'], defaults={'status': 'enrolled'})
        if marcus and 'CS402' in created_courses:
            Enrollment.objects.get_or_create(student=marcus, course=created_courses['CS402'], defaults={'status': 'enrolled'})
        if elena and 'CS204' in created_courses:
            Enrollment.objects.get_or_create(student=elena, course=created_courses['CS204'], defaults={'status': 'enrolled'})
        if elena and 'CS402' in created_courses:
            Enrollment.objects.get_or_create(student=elena, course=created_courses['CS402'], defaults={'status': 'enrolled'})

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
        self.stdout.write(self.style.SUCCESS('Admin Login: admin@courseconnect.edu / Admin@123'))
        self.stdout.write(self.style.SUCCESS('Student Login: sarah.jenkins@student.edu / Student@123'))
