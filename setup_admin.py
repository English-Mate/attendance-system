import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from attendance_app.models import Department

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='yuvansood1234@gmail.com',
        password='YuvanBest',
        role='admin',
    )
    admin.email_verified = True
    admin.save()
    print('Admin user created successfully!')
    print('Username: admin')
    print('Email: yuvansood1234@gmail.com')
    print('Password: YuvanBest')
else:
    print('Admin user already exists.')

default_dept, _ = Department.objects.get_or_create(
    name='General',
    defaults={'description': 'Default department'}
)
print(f'Department "{default_dept.name}" ready.')
