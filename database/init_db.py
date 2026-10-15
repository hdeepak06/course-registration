import os
import sys
import sqlite3
from werkzeug.security import generate_password_hash

# Add parent directory to path so config and database can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from database.db import test_mysql_connection

SAMPLE_ADMIN_PASSWORD = "Admin@123"
SAMPLE_STUDENT_PASSWORD = "Student@123"

SAMPLE_STUDENTS = [
    ("Alexander Wright", "admin@courseconnect.edu", generate_password_hash(SAMPLE_ADMIN_PASSWORD), "administrator"),
    ("Sarah Jenkins", "sarah.jenkins@student.edu", generate_password_hash(SAMPLE_STUDENT_PASSWORD), "student"),
    ("Marcus Chen", "marcus.chen@student.edu", generate_password_hash(SAMPLE_STUDENT_PASSWORD), "student"),
    ("Elena Rostova", "elena.rostova@student.edu", generate_password_hash(SAMPLE_STUDENT_PASSWORD), "student"),
    ("David Kim", "david.kim@student.edu", generate_password_hash(SAMPLE_STUDENT_PASSWORD), "student"),
]

SAMPLE_COURSES = [
    ("CS101", "Introduction to Computer Science & Python", "A comprehensive introduction to computational problem-solving, algorithms, data structures, and Python programming fundamentals with practical projects.", "Dr. Alan Turing", 45, 43, "Computer Science", 4),
    ("CS204", "Relational Database Design & SQL Engineering", "In-depth study of relational modeling, normalization, indexing strategies, ACID transactions, and advanced SQL query optimization with MySQL.", "Prof. Edgar F. Codd", 35, 33, "Information Systems", 3),
    ("CS310", "Full-Stack Web Development Architecture", "Design, build, and deploy high-performance web applications using modern front-end technologies, Flask backends, and RESTful APIs.", "Dr. Grace Hopper", 40, 39, "Software Engineering", 4),
    ("CS402", "Distributed Cloud Systems & Microservices", "Architecting resilient cloud services, containerization with Docker, message queues, API gateways, and distributed state consistency.", "Prof. Leslie Lamport", 30, 28, "Cloud Computing", 3),
    ("DS201", "Applied Data Science & Machine Learning", "Statistical foundations, exploratory data analysis, feature engineering, and supervised/unsupervised machine learning models with Python.", "Dr. Fei-Fei Li", 35, 35, "Data Science", 4),
    ("SEC305", "Application Security & Cryptographic Systems", "Defensive web security, OWASP top vulnerabilities, authentication tokens, password hashing algorithms, and secure coding practices.", "Prof. Bruce Schneier", 25, 25, "Cybersecurity", 3),
    ("MATH220", "Discrete Mathematics & Graph Algorithms", "Logic, set theory, combinatorics, graph theory, tree traversals, and mathematical proofs essential for software engineering.", "Dr. Ada Lovelace", 50, 49, "Mathematics", 3),
    ("AI415", "Natural Language Processing & Large Models", "Vector embeddings, transformer architectures, tokenization, semantic search, and prompt engineering in modern AI software systems.", "Dr. Geoffrey Hinton", 30, 0, "Artificial Intelligence", 4) # Full course for testing!
]

SAMPLE_ENROLLMENTS = [
    (2, 1), # Sarah in CS101
    (2, 2), # Sarah in CS204
    (3, 1), # Marcus in CS101
    (3, 4), # Marcus in CS402
    (4, 2), # Elena in CS204
    (4, 4), # Elena in CS402
    (5, 7), # David in MATH220
]

def init_mysql_db():
    """Initializes the MySQL database using mysql.connector."""
    import mysql.connector
    print(f"[*] Connecting to MySQL at {Config.MYSQL_HOST}:{Config.MYSQL_PORT}...")
    
    # First connect without database to ensure database exists
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    cursor.execute(f"USE {Config.MYSQL_DATABASE};")
    
    print("[*] Creating MySQL tables...")
    cursor.execute("DROP TABLE IF EXISTS enrollments;")
    cursor.execute("DROP TABLE IF EXISTS courses;")
    cursor.execute("DROP TABLE IF EXISTS students;")
    
    cursor.execute("""
    CREATE TABLE students (
        student_id INT AUTO_INCREMENT PRIMARY KEY,
        full_name VARCHAR(100) NOT NULL,
        email VARCHAR(150) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('student', 'administrator') NOT NULL DEFAULT 'student',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """)
    
    cursor.execute("""
    CREATE TABLE courses (
        course_id INT AUTO_INCREMENT PRIMARY KEY,
        course_code VARCHAR(20) NOT NULL UNIQUE,
        course_title VARCHAR(150) NOT NULL,
        description TEXT NOT NULL,
        instructor VARCHAR(100) NOT NULL,
        max_seats INT NOT NULL,
        available_seats INT NOT NULL,
        department VARCHAR(80) DEFAULT 'Computer Science',
        credits INT DEFAULT 3,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT chk_seats CHECK (available_seats >= 0 AND available_seats <= max_seats)
    ) ENGINE=InnoDB;
    """)
    
    cursor.execute("""
    CREATE TABLE enrollments (
        enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT NOT NULL,
        course_id INT NOT NULL,
        enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status ENUM('enrolled', 'cancelled') NOT NULL DEFAULT 'enrolled',
        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
        UNIQUE KEY uq_student_course (student_id, course_id)
    ) ENGINE=InnoDB;
    """)
    
    print("[*] Inserting seed data into MySQL...")
    cursor.executemany(
        "INSERT INTO students (full_name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
        SAMPLE_STUDENTS
    )
    cursor.executemany(
        "INSERT INTO courses (course_code, course_title, description, instructor, max_seats, available_seats, department, credits) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        SAMPLE_COURSES
    )
    cursor.executemany(
        "INSERT INTO enrollments (student_id, course_id, status) VALUES (%s, %s, 'enrolled')",
        SAMPLE_ENROLLMENTS
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    print("[+] MySQL database 'course_registration' initialized successfully!")

def init_sqlite_db():
    """Initializes local SQLite database for instant development & zero-config testing."""
    db_path = os.path.abspath(Config.SQLITE_DB_PATH)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    print(f"[*] Initializing SQLite database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS enrollments;")
    cursor.execute("DROP TABLE IF EXISTS courses;")
    cursor.execute("DROP TABLE IF EXISTS students;")
    
    cursor.execute("""
    CREATE TABLE students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('student', 'administrator')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    cursor.execute("""
    CREATE TABLE courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT NOT NULL UNIQUE,
        course_title TEXT NOT NULL,
        description TEXT NOT NULL,
        instructor TEXT NOT NULL,
        max_seats INTEGER NOT NULL,
        available_seats INTEGER NOT NULL,
        department TEXT DEFAULT 'Computer Science',
        credits INTEGER DEFAULT 3,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        CHECK (available_seats >= 0 AND available_seats <= max_seats)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE enrollments (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        enrollment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL DEFAULT 'enrolled' CHECK(status IN ('enrolled', 'cancelled')),
        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
        UNIQUE (student_id, course_id)
    );
    """)
    
    print("[*] Inserting seed data into SQLite...")
    cursor.executemany(
        "INSERT INTO students (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        SAMPLE_STUDENTS
    )
    cursor.executemany(
        "INSERT INTO courses (course_code, course_title, description, instructor, max_seats, available_seats, department, credits) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        SAMPLE_COURSES
    )
    cursor.executemany(
        "INSERT INTO enrollments (student_id, course_id, status) VALUES (?, ?, 'enrolled')",
        SAMPLE_ENROLLMENTS
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    print("[+] SQLite fallback database initialized successfully with sample data!")

def main():
    print("=" * 60)
    print(" CourseConnect Database Setup & Seeding")
    print("=" * 60)
    
    mysql_online = test_mysql_connection()
    if mysql_online:
        print("[✓] Active MySQL service detected.")
        try:
            init_mysql_db()
        except Exception as e:
            print(f"[!] MySQL initialization error: {e}")
            print("[*] Initializing SQLite database as backup...")
            init_sqlite_db()
    else:
        print("[-] MySQL server is not running on localhost:3306 or credentials require setup.")
        print("[*] Initializing SQLite database so you can test and explore immediately without barrier.")
        init_sqlite_db()
        print("\nNote: When your MySQL service is started, run 'python database/init_db.py' to seed MySQL as well.")
        
    print("\nDefault Logins:")
    print(" - Administrator: admin@courseconnect.edu / Admin@123")
    print(" - Student:       sarah.jenkins@student.edu / Student@123")
    print("=" * 60)

if __name__ == '__main__':
    main()
