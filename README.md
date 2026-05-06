# Attendance System

A secure, role-based attendance management system built with Django and PostgreSQL.

## Features

- **Role-based access control**: Admin, Teacher, and Student roles
- **Account request system**: Users can request accounts, email verification required
- **Admin approval workflow**: Admin reviews and approves/denies account requests
- **Email notifications**: Automatic emails for verification, approval, and rejection
- **Roster attendance**: Bulk attendance marking by department
- **Individual attendance**: Single student attendance tracking
- **Audit logging**: Track all attendance changes
- **Dashboard**: Overview of attendance statistics and pending requests

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd attendance-system
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` with your database credentials and Gmail app password.

5. Create the PostgreSQL database:
```bash
createdb attendance_db
```

6. Run migrations:
```bash
python manage.py migrate
```

7. Create the initial admin user:
```bash
python setup_admin.py
```

8. Run the development server:
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the system.

## Roles

| Role | Permissions |
|------|-------------|
| Admin | Full access: manage users, approve/deny account requests, mark attendance, view all records |
| Teacher | Mark attendance, create rosters, view/edit all records |
| Student | View own attendance records only |

## Account Request Flow

1. User visits `/request-account/` and submits a request
2. System sends a verification email to the user
3. User clicks the verification link
4. Admin reviews the request at `/account-requests/`
5. Admin approves or rejects the request
6. If approved, user receives an email with login credentials

## Security Features

- Password hashing via Django's built-in auth
- CSRF protection on all forms
- XSS filtering and content-type sniffing protection
- Environment variable-based configuration
- `.env` file excluded from version control
- Role-based authorization on all views
- Email verification before account activation

## API

Get attendance records via JSON:
```
GET /api/attendance/?date=2024-01-15
```
