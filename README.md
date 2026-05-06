# Attendance System

A simple, secure school attendance system built with Django and PostgreSQL.

## Features

- **Admin only**: You are the only admin
- **Teacher accounts**: Teachers request access, admin approves
- **Class management**: Classes 6-12, sections A & B
- **Student management**: Teachers add/remove students in their class
- **Attendance**: Teachers mark present/absent for their entire class
- **Records**: View and filter attendance history

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy and edit env:
```bash
copy .env.example .env
```

3. Create PostgreSQL database:
```bash
createdb attendance_db
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create admin + classes:
```bash
python setup_admin.py
```

6. Run server:
```bash
python manage.py runserver
```

Login at `http://localhost:8000` with:
- Username: `admin`
- Password: `YuvanBest`

## Roles

| Role | What they can do |
|------|------------------|
| Admin | Approve teacher requests, assign classes, view all records |
| Teacher | Add/remove students in their class, mark attendance |
| Student | No login - just gets marked by teachers |

## How It Works

1. Someone requests teacher access at `/request-account/`
2. You review and approve at `/account-requests/`
3. You assign them a class (6A, 6B, 7A, 7B... 12A, 12B)
4. They log in, add students, and mark attendance daily
