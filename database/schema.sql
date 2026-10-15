-- ========================================================
-- CourseConnect Relational Database Schema (MySQL)
-- Database Name: course_registration
-- ========================================================

CREATE DATABASE IF NOT EXISTS course_registration 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE course_registration;

-- 1. Students Table
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;

CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'administrator') NOT NULL DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Courses Table
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

-- 3. Enrollments Table
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

-- Indexes for high-performance searching and filtering
CREATE INDEX idx_course_code ON courses(course_code);
CREATE INDEX idx_student_email ON students(email);
CREATE INDEX idx_enrollment_student ON enrollments(student_id);
CREATE INDEX idx_enrollment_course ON enrollments(course_id);

-- ========================================================
-- Seed Data for Testing & Demonstration
-- Passwords:
-- Admin: Admin@123
-- Students: Student@123
-- ========================================================

INSERT INTO students (full_name, email, password_hash, role) VALUES
('Alexander Wright', 'admin@courseconnect.edu', 'scrypt:32768:8:1$IjnkuEmP7zFM7Psi$e7a1aae669f93cb578477aabab314a1208d2bec8e844712b7f111db705490a92dfe0c94fb07b3e3577a0f371e5e9b1e8e0360c00265d913bfa55f1ff2aa32b2d', 'administrator'),
('Sarah Jenkins', 'sarah.jenkins@student.edu', 'scrypt:32768:8:1$u0eQFh4OGpXDt7Be$d9952e6c32dfcffa0da296f0054c3d35e3582675e57309f835de0b13d7039519eca868ca1daa7a922056464a788da5f80598c35b50a3b335f6adccfb34ef5cac', 'student'),
('Marcus Chen', 'marcus.chen@student.edu', 'scrypt:32768:8:1$u0eQFh4OGpXDt7Be$d9952e6c32dfcffa0da296f0054c3d35e3582675e57309f835de0b13d7039519eca868ca1daa7a922056464a788da5f80598c35b50a3b335f6adccfb34ef5cac', 'student'),
('Elena Rostova', 'elena.rostova@student.edu', 'scrypt:32768:8:1$u0eQFh4OGpXDt7Be$d9952e6c32dfcffa0da296f0054c3d35e3582675e57309f835de0b13d7039519eca868ca1daa7a922056464a788da5f80598c35b50a3b335f6adccfb34ef5cac', 'student');

INSERT INTO courses (course_code, course_title, description, instructor, max_seats, available_seats, department, credits) VALUES
('CS101', 'Introduction to Computer Science & Python', 'A comprehensive introduction to computational problem-solving, algorithms, data structures, and Python programming fundamentals.', 'Dr. Alan Turing', 45, 43, 'Computer Science', 4),
('CS204', 'Relational Database Design & SQL Engineering', 'In-depth study of relational modeling, normalization, indexing strategies, ACID transactions, and advanced SQL query optimization with MySQL.', 'Prof. Edgar F. Codd', 35, 33, 'Information Systems', 3),
('CS310', 'Full-Stack Web Development Architecture', 'Design, build, and deploy high-performance web applications using modern front-end technologies, Flask backends, and RESTful APIs.', 'Dr. Grace Hopper', 40, 39, 'Software Engineering', 4),
('CS402', 'Distributed Cloud Systems & Microservices', 'Architecting resilient cloud services, containerization with Docker, message queues, API gateways, and distributed state consistency.', 'Prof. Leslie Lamport', 30, 28, 'Cloud Computing', 3),
('DS201', 'Applied Data Science & Machine Learning', 'Statistical foundations, exploratory data analysis, feature engineering, and supervised/unsupervised machine learning models with Python.', 'Dr. Fei-Fei Li', 35, 35, 'Data Science', 4),
('SEC305', 'Application Security & Cryptographic Systems', 'Defensive web security, OWASP top vulnerabilities, authentication tokens, password hashing algorithms, and secure coding practices.', 'Prof. Bruce Schneier', 25, 25, 'Cybersecurity', 3);

-- Sample Enrollments (Sarah Jenkins and Marcus Chen enrolled in CS101 and CS204)
INSERT INTO enrollments (student_id, course_id, status) VALUES
(2, 1, 'enrolled'),
(2, 2, 'enrolled'),
(3, 1, 'enrolled'),
(3, 4, 'enrolled'),
(4, 2, 'enrolled'),
(4, 4, 'enrolled');
