# CourseConnect — Premium Course Registration Platform (Django & MySQL)

> An enterprise-grade, full-stack academic course registration website built for a backend software engineering portfolio. Engineered using **Python (Django)**, **MySQL**, and **Vanilla HTML5, CSS3, & Modern JavaScript**, featuring an elegant metallic **Golden Button Design System** throughout the interface.

---

## 🌟 Key Engineering Highlights

- **Django ORM & Relational Architecture**: 3NF normalized schema with `User`, `StudentProfile`, `Course`, and `Enrollment` models, foreign key relationships, cascading deletes, and database-level `CheckConstraint` (`CHECK (available_seats >= 0 AND available_seats <= max_seats)`).
- **ACID Transaction Management**: Course registration and cancellation execute inside atomic database transactions (`transaction.atomic()`) with row locking (`select_for_update()`) to prevent race conditions and eliminate seat over-subscription.
- **Dual Administrator Interfaces**: Includes both a custom styled administrative dashboard (`/admin-portal/`) with analytics & capacity controls, and Django's built-in administration suite (`/admin/`).
- **Django Authentication & RBAC**: Enforced role-based access control protecting administrative routes (`@admin_required`) and student actions (`@login_required`).
- **CSRF & OWASP Security**: Native Django CSRF tokens on all POST forms, PBKDF2 password hashing, and parameterized query execution via the ORM.
- **Metallic Golden Button Design System**: Crafted with rich metallic gold gradients (`#B8860B`, `#D4AF37`, `#F5D76E`), subtle highlights, smooth cubic-bezier transitions, hover elevation, and pressed feedback.
- **Hybrid Database Connectivity**: Configured for MySQL with `pymysql` and intelligent auto-detection fallback to local SQLite when local MySQL service is offline.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, Modern CSS3 (Vanilla design system, no Tailwind), ES6 JavaScript |
| **Backend** | Python 3.12, Django 5.1 (Models, Views, Forms, Migrations, Django Templates) |
| **Database** | MySQL (via `pymysql` & Django MySQL engine) / SQLite fallback |
| **Security** | CSRF protection, PBKDF2 password hashing, Parameterized queries, Session management |
| **Testing** | Django `TestCase` test suite covering routes, auth, transactions, and RBAC |

---

## 🎨 Golden Button Design System

The application features a bespoke golden button design (`.btn-gold`, `.btn-gold:hover`, `.btn-gold:active`) tailored for high visual appeal and accessibility:
- **Gradient**: `linear-gradient(135deg, #B8860B 0%, #D4AF37 50%, #F5D76E 100%)`
- **Text Color**: Deep Navy Charcoal (`#060D17`) for contrast ratio compliance.
- **Highlight Sheen**: Specular diagonal reflection on hover.
- **Elevated Shadows**: Subtle multi-layered box-shadow with gold-tinted glow (`0 4px 14px rgba(184, 134, 11, 0.28)`).
- **Destructive Actions**: Course deletions use a dedicated warning styling (`.btn-danger`) rather than gold, strictly adhering to UX safety principles.

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

## 🗄️ Database Models & Relational Architecture

### 1. `StudentProfile` (`student_profiles`)
- Extends Django's `User` model via `OneToOneField`.
- Role-based flag: `role` (`student` or `administrator`).
- Timestamp: `created_at`.

### 2. `Course` (`courses`)
- `course_code`: Unique identifier (e.g. `CS101`, indexed).
- `course_title`, `description`, `instructor`, `department`, `credits`.
- `max_seats` & `available_seats`: Checked by `valid_seat_capacity` constraint (`0 <= available_seats <= max_seats`).

### 3. `Enrollment` (`enrollments`)
- `student`: Foreign key to `User` (cascading delete).
- `course`: Foreign key to `Course` (cascading delete).
- `status`: `enrolled` or `cancelled`.
- Unique together: `('student', 'course')` preventing duplicate active registrations.

---

## 🚀 Quickstart & Setup Instructions

### 1. Prerequisites
- Python 3.10+
- MySQL Server (optional; local SQLite fallback automatically engages if MySQL is offline)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Database (`.env`)
```ini
DB_ENGINE=auto
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=course_registration
```

### 4. Apply Migrations & Seed Sample Data
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data
```

### 5. Start the Development Server
```bash
python manage.py runserver 8000
```
Open your browser and navigate to: `http://127.0.0.1:8000`

---

## 🔐 Default Demo Accounts for Evaluation

| Role | Email / Username | Password | Permissions |
|---|---|---|---|
| **Administrator** | `admin@courseconnect.edu` | `Admin@123` | Course CRUD, capacity management, enrollment audit log, Django Admin access |
| **Student** | `sarah.jenkins@student.edu` | `Student@123` | Course search, registration, My Courses dashboard, cancellation |
| **Student** | `elena.rostova@student.edu` | `Student@123` | Course search, registration, cancellation |

---

## 🧪 Automated Testing

A full automated test suite is included in `courses/tests.py`:
```bash
python manage.py test
```
Tests verify:
- Homepage rendering, statistics calculation, and hero CTA buttons
- Live course search & keyword filtering
- Registration input validation and error messages
- Password hashing and session login/logout
- Role-based server access controls (guarding `/admin-portal/`)
- Course creation, duplicate code rejection, capacity limits
- Atomic seat decrement upon enrollment, duplicate enrollment blocking, and seat release on cancellation.
