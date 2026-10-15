# CourseConnect — Premium Course Registration Platform

> An enterprise-grade, full-stack academic course registration website built for a backend software engineering portfolio. Developed with **Python (Flask)**, **MySQL**, and **Vanilla HTML5, CSS3, & Modern JavaScript**, featuring an elegant metallic **Golden Button Design System** throughout the interface.

---

## 🌟 Key Highlights & Engineering Features

- **Relational MySQL Database Architecture**: 3NF normalized schema with `students`, `courses`, and `enrollments` tables, foreign key constraints, cascading deletes, and database-level `CHECK` constraints.
- **ACID Transaction Management**: Multi-step course enrollment and cancellation operations execute inside explicit atomic database transactions to guarantee zero seat over-subscription or inconsistent states.
- **Role-Based Access Control (RBAC)**: Enforced strictly on the server via custom decorators (`@login_required`, `@admin_required`), protecting administrator routes against unauthorized access.
- **OWASP Secure Authentication**: Passwords hashed using industry-standard **scrypt** and PBKDF2 mechanisms via `werkzeug.security`. Never stores plaintext passwords.
- **Golden Button Design System**: Crafted with rich metallic gold gradients (`#B8860B`, `#D4AF37`, `#F5D76E`), subtle highlights, smooth cubic-bezier transitions, hover elevation, and pressed feedback.
- **Zero-Friction Hybrid Database Adapter**: Built-in support for native `mysql-connector-python` with an intelligent fallback adapter to local SQLite if the MySQL service is offline, allowing instant local testing without setup barriers.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, Modern CSS3 (Vanilla design system, no Tailwind), ES6 JavaScript |
| **Backend** | Python 3.12, Flask 3.1, Jinja2 templating |
| **Database** | MySQL (with Python MySQL Connector), Fallback SQLite adapter |
| **Security** | Scrypt / PBKDF2 password hashing, Parameterized SQL queries, Session cookies with HttpOnly & SameSite |
| **Testing** | Python `unittest` test suite covering routes, auth, transactions, and role enforcement |

---

## 🎨 Golden Button Design System

The application features a bespoke golden button design (`.btn-gold`, `.btn-gold:hover`, `.btn-gold:active`) tailored for high visual appeal and accessibility:
- **Gradient**: `linear-gradient(135deg, #B8860B 0%, #D4AF37 50%, #F5D76E 100%)`
- **Text Color**: Deep Navy Charcoal (`#060D17`) for contrast ratio compliance.
- **Highlight Sheen**: Specular diagonal reflection on hover.
- **Elevated Shadows**: Subtle multi-layered box-shadow with gold-tinted glow (`0 4px 14px rgba(184, 134, 11, 0.28)`).
- **Destructive Actions**: Course deletions use a dedicated warning styling (`.btn-danger`) rather than gold, strictly adhering to UX best practices.

### Implemented Golden Buttons:
1. **Explore Courses**
2. **Register for Course**
3. **View Details**
4. **Enroll Now**
5. **Save Course**
6. **Update Course**
7. **Add New Course**
8. **Search Courses**
9. **View My Courses**
10. **Login**
11. **Sign Up**
12. **Admin Dashboard**
13. **Confirm Registration**
14. **Cancel Enrollment**
15. **Back to Dashboard**

---

## 🗄️ Relational Database Schema (`course_registration`)

### 1. `students` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `student_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique student/user identifier |
| `full_name` | VARCHAR(100) | NOT NULL | Student's full name |
| `email` | VARCHAR(150) | NOT NULL, UNIQUE | Academic login email |
| `password_hash` | VARCHAR(255) | NOT NULL | Secure salted password hash |
| `role` | ENUM | 'student', 'administrator' | User access role |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Registration timestamp |

### 2. `courses` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `course_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique course identifier |
| `course_code` | VARCHAR(20) | NOT NULL, UNIQUE | Course code (e.g. CS101) |
| `course_title` | VARCHAR(150) | NOT NULL | Full course title |
| `description` | TEXT | NOT NULL | Course description & curriculum |
| `instructor` | VARCHAR(100) | NOT NULL | Lead professor or instructor |
| `max_seats` | INT | NOT NULL | Total capacity limit |
| `available_seats` | INT | NOT NULL, CHECK (0 <= available <= max) | Remaining open seats |
| `department` | VARCHAR(80) | DEFAULT 'Computer Science' | Academic department |
| `credits` | INT | DEFAULT 3 | Academic credits earned |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

### 3. `enrollments` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `enrollment_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Registration log entry ID |
| `student_id` | INT | FOREIGN KEY (students) ON DELETE CASCADE | Enrolled student reference |
| `course_id` | INT | FOREIGN KEY (courses) ON DELETE CASCADE | Target course reference |
| `enrollment_date` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Enrollment timestamp |
| `status` | ENUM | 'enrolled', 'cancelled' | Enrollment status |
| `UNIQUE KEY` | `(student_id, course_id)` | Prevents duplicate enrollments |

---

## ⚡ Concurrency & Transaction Management

Course enrollment logic is encapsulated in `services/enrollment_service.py` within an ACID transaction:
```python
with transaction() as (conn, cursor):
    # 1. Verify student exists
    # 2. Check if student is already enrolled (status = 'enrolled')
    # 3. Check course available_seats > 0
    # 4. Insert or update enrollment record
    # 5. Decrement available_seats atomically
    # 6. Commit or rollback on error
```
When cancellation occurs, `available_seats` is safely incremented back to release the seat.

---

## 🚀 Quickstart & Setup Instructions

### 1. Prerequisites
- Python 3.10+
- MySQL Server (optional; local SQLite fallback automatically engages if MySQL is not running)

### 2. Clone and Install Dependencies
```bash
git clone https://github.com/your-username/course-registration.git
cd "course-registration"
pip install -r requirements.txt
```

### 3. Configure Database (.env)
Copy `.env.example` to `.env` and configure your MySQL credentials:
```ini
DB_ENGINE=auto
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=course_registration
```

### 4. Initialize Database & Seed Sample Records
```bash
python database/init_db.py
```
This script creates tables and seeds demo students, administrators, and realistic courses.

### 5. Run the Application
```bash
python app.py
```
Open your browser and navigate to: `http://127.0.0.1:5000`

---

## 🔐 Default Demo Accounts for Evaluation

| Role | Email | Password | Access Level |
|---|---|---|---|
| **Administrator** | `admin@courseconnect.edu` | `Admin@123` | Full CRUD, capacity controls, enrollment audit logs |
| **Student** | `sarah.jenkins@student.edu` | `Student@123` | Course browsing, registration, My Courses dashboard |
| **Student** | `elena.rostova@student.edu` | `Student@123` | Course browsing, registration, cancellation |

---

## 🧪 Automated Testing

A full automated test suite is included in `tests/test_app.py`:
```bash
python -m unittest tests/test_app.py
```
Tests verify:
- Homepage rendering, statistics calculation, and hero CTA buttons
- Live course search & keyword filtering
- Input validation (short passwords, email formats, mismatch detection)
- Password hashing and authentication flows
- Role-based server access controls (guarding `/admin`)
- Course creation, duplicate code rejection, capacity limits
- Atomic seat decrement upon enrollment, duplicate enrollment blocking, and seat release on cancellation.
