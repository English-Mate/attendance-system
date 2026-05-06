# Attendance System

A secure, role-based attendance management system built with Django and PostgreSQL.

## Features

- **Role-based access control**: Admin, Manager, and Employee roles
- **Secure authentication**: Password hashing, CSRF protection, XSS filtering
- **Attendance tracking**: Mark attendance, view records, filter by date/status
- **Audit logging**: Track all attendance changes
- **Dashboard**: Overview of attendance statistics
- **User management**: Admin can create/edit users and assign roles

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
Edit `.env` with your database credentials and secret key.

5. Create the PostgreSQL database:
```bash
createdb attendance_db
```

6. Run migrations:
```bash
python manage.py migrate
```

7. Create a superuser:
```bash
python manage.py createsuperuser
```

8. Run the development server:
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the system.

## Roles

| Role | Permissions |
|------|-------------|
| Admin | Full access: manage users, mark attendance, view all records |
| Manager | Mark attendance, view/edit all records |
| Employee | View own attendance records only |

## Security Features

- Password hashing via Django's built-in auth
- CSRF protection on all forms
- XSS filtering and content-type sniffing protection
- Environment variable-based configuration
- `.env` file excluded from version control
- Role-based authorization on all views

## API

Get attendance records via JSON:
```
GET /api/attendance/?date=2024-01-15
```
