from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class ClassSection(models.Model):
    CLASS_CHOICES = [(i, f'Class {i}') for i in range(6, 13)]
    SECTION_CHOICES = [('A', 'Section A'), ('B', 'Section B')]

    grade = models.IntegerField(choices=CLASS_CHOICES)
    section = models.CharField(max_length=1, choices=SECTION_CHOICES)
    teacher = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_classes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['grade', 'section']
        ordering = ['grade', 'section']

    def __str__(self):
        return f"Class {self.grade} - {self.section}"


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='teacher')
    class_section = models.ForeignKey(ClassSection, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    is_student = models.BooleanField(default=True)

    def __str__(self):
        if self.is_student:
            return f"{self.username} (Student)"
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_teacher(self):
        return self.role == 'teacher'


class AccountRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    full_name = models.CharField(max_length=150)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviewed_requests')
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    verification_token = models.CharField(max_length=64, unique=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.status}"

    def generate_verification_token(self):
        self.verification_token = uuid.uuid4().hex
        return self.verification_token


class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    notes = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='records_made')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        unique_together = ['student', 'date']

    def __str__(self):
        return f"{self.student.username} - {self.date} ({self.status})"


class AttendanceLog(models.Model):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=50)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} - {self.timestamp}"
