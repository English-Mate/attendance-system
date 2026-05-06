import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from attendance_app.models import ClassSection

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='yuvansood1234@gmail.com',
        password='YuvanBest',
        role='admin',
        is_student=False,
    )
    print('Admin created!')
    print('Username: admin')
    print('Password: YuvanBest')
else:
    print('Admin already exists.')

for grade in range(6, 13):
    for section in ['A', 'B']:
        cs, created = ClassSection.objects.get_or_create(grade=grade, section=section)
        if created:
            print(f'Created: {cs}')

print('All classes 6-12 (A & B) ready.')
