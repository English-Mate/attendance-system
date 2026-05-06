from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from .models import User, Attendance, ClassSection, AttendanceLog, AccountRequest
from .forms import StudentForm, AccountRequestForm


def is_admin(user):
    return user.is_authenticated and user.is_admin


def is_teacher(user):
    return user.is_authenticated and user.is_teacher


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'attendance_app/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def request_account(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AccountRequestForm(request.POST)
        if form.is_valid():
            existing = AccountRequest.objects.filter(
                full_name=form.cleaned_data['full_name'],
                status='pending'
            ).exists()

            if existing:
                messages.error(request, 'A pending request already exists under this name.')
            else:
                account_request = form.save()
                messages.success(request, 'Request submitted! Wait for admin approval.')
                return redirect('request_status', token=account_request.verification_token)
    else:
        form = AccountRequestForm()

    return render(request, 'attendance_app/request_account.html', {'form': form})


def request_status(request, token):
    account_request = get_object_or_404(AccountRequest, verification_token=token)
    return render(request, 'attendance_app/request_status.html', {'request': account_request})


@login_required
def dashboard(request):
    today = timezone.now().date()

    if request.user.is_teacher:
        class_section = request.user.managed_classes.first()
        if class_section:
            students = User.objects.filter(class_section=class_section, is_student=True)
            total_students = students.count()
            present_today = Attendance.objects.filter(date=today, class_section=class_section, status='present').count()
            absent_today = Attendance.objects.filter(date=today, class_section=class_section, status='absent').count()
        else:
            students = User.objects.none()
            total_students = 0
            present_today = 0
            absent_today = 0
    elif request.user.is_admin:
        total_students = User.objects.filter(is_student=True).count()
        present_today = Attendance.objects.filter(date=today, status='present').count()
        absent_today = Attendance.objects.filter(date=today, status='absent').count()
        students = User.objects.filter(is_student=True).order_by('class_section__grade', 'class_section__section', 'username')[:20]
    else:
        total_students = 0
        present_today = 0
        absent_today = 0
        students = User.objects.none()

    pending_requests = AccountRequest.objects.filter(status='pending').count() if request.user.is_admin else 0

    context = {
        'total_students': total_students,
        'present_today': present_today,
        'absent_today': absent_today,
        'students': students,
        'pending_requests': pending_requests,
    }
    return render(request, 'attendance_app/dashboard.html', context)


@login_required
@user_passes_test(is_teacher)
def my_class(request):
    class_section = request.user.managed_classes.first()

    if not class_section:
        messages.error(request, 'No class assigned to you. Contact admin.')
        return redirect('dashboard')

    students = User.objects.filter(class_section=class_section, is_student=True).order_by('username')

    context = {
        'class_section': class_section,
        'students': students,
    }
    return render(request, 'attendance_app/my_class.html', context)


@login_required
@user_passes_test(is_teacher)
def add_student(request):
    class_section = request.user.managed_classes.first()
    if not class_section:
        messages.error(request, 'No class assigned.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.class_section = class_section
            student.is_student = True
            student.set_password(form.cleaned_data['password'])
            student.save()
            messages.success(request, f'Student {student.username} added.')
            return redirect('my_class')
    else:
        form = StudentForm()

    return render(request, 'attendance_app/add_student.html', {'form': form, 'class_section': class_section})


@login_required
@user_passes_test(is_teacher)
def remove_student(request, student_id):
    student = get_object_or_404(User, pk=student_id, is_student=True)
    class_section = request.user.managed_classes.first()

    if student.class_section != class_section:
        messages.error(request, 'This student is not in your class.')
        return redirect('my_class')

    if request.method == 'POST':
        name = student.username
        student.delete()
        messages.success(request, f'Student {name} removed.')
        return redirect('my_class')

    return render(request, 'attendance_app/confirm_remove.html', {'student': student})


@login_required
@user_passes_test(is_teacher)
def mark_attendance(request):
    class_section = request.user.managed_classes.first()
    if not class_section:
        messages.error(request, 'No class assigned.')
        return redirect('dashboard')

    today = timezone.now().date()
    date = request.GET.get('date', str(today))
    students = User.objects.filter(class_section=class_section, is_student=True).order_by('username')

    attendance_map = {}
    for a in Attendance.objects.filter(date=date, class_section=class_section):
        attendance_map[a.student_id] = a.status

    if request.method == 'POST':
        with transaction.atomic():
            for student in students:
                status = request.POST.get(f'status_{student.id}', 'present')
                notes = request.POST.get(f'notes_{student.id}', '')

                Attendance.objects.update_or_create(
                    student=student,
                    date=date,
                    class_section=class_section,
                    defaults={
                        'status': status,
                        'notes': notes,
                        'marked_by': request.user,
                    }
                )

        messages.success(request, f'Attendance saved for {date}.')
        return redirect('attendance_records')

    return render(request, 'attendance_app/mark_attendance.html', {
        'students': students,
        'class_section': class_section,
        'date': date,
        'attendance_map': attendance_map,
    })


@login_required
def attendance_records(request):
    today = timezone.now().date()

    if request.user.is_teacher:
        class_section = request.user.managed_classes.first()
        if class_section:
            records = Attendance.objects.filter(class_section=class_section).select_related('student').order_by('-date', 'student__username')
        else:
            records = Attendance.objects.none()
    else:
        records = Attendance.objects.all().select_related('student', 'class_section').order_by('-date', 'student__username')

    date_filter = request.GET.get('date')
    status_filter = request.GET.get('status')
    student_filter = request.GET.get('student')

    if date_filter:
        records = records.filter(date=date_filter)
    if status_filter:
        records = records.filter(status=status_filter)
    if student_filter and request.user.is_admin:
        records = records.filter(student_id=student_filter)

    context = {
        'records': records[:100],
        'students': User.objects.filter(is_student=True).order_by('username') if request.user.is_admin else [],
    }
    return render(request, 'attendance_app/attendance_records.html', context)


@login_required
@user_passes_test(is_admin)
def account_requests(request):
    pending = AccountRequest.objects.filter(status='pending').order_by('created_at')
    processed = AccountRequest.objects.exclude(status='pending').order_by('-reviewed_at')[:20]
    return render(request, 'attendance_app/account_requests.html', {'pending': pending, 'processed': processed})


@login_required
@user_passes_test(is_admin)
def approve_request(request, request_id):
    account_request = get_object_or_404(AccountRequest, pk=request_id, status='pending')

    if request.method == 'POST':
        password = User.objects.make_random_password(length=8)
        class_sections = ClassSection.objects.all()
        assigned_class = request.POST.get('class_section')

        user = User.objects.create_user(
            username=account_request.full_name.lower().replace(' ', '_'),
            password=password,
            role='teacher',
            is_student=False,
        )

        if assigned_class:
            try:
                cs = ClassSection.objects.get(pk=assigned_class)
                cs.teacher = user
                cs.save()
            except ClassSection.DoesNotExist:
                pass

        account_request.status = 'approved'
        account_request.reviewed_by = request.user
        account_request.reviewed_at = timezone.now()
        account_request.review_notes = request.POST.get('review_notes', '')
        account_request.save()

        messages.success(request, f'Approved! Username: {user.username} | Password: {password}')
        return redirect('account_requests')

    return render(request, 'attendance_app/approve_request.html', {
        'request': account_request,
        'class_sections': ClassSection.objects.filter(teacher__isnull=True),
    })


@login_required
@user_passes_test(is_admin)
def reject_request(request, request_id):
    account_request = get_object_or_404(AccountRequest, pk=request_id, status='pending')

    if request.method == 'POST':
        account_request.status = 'rejected'
        account_request.reviewed_by = request.user
        account_request.reviewed_at = timezone.now()
        account_request.review_notes = request.POST.get('review_notes', '')
        account_request.save()
        messages.success(request, f'Request from {account_request.full_name} rejected.')
        return redirect('account_requests')

    return render(request, 'attendance_app/reject_request.html', {'request': account_request})


@login_required
@user_passes_test(is_admin)
def manage_teachers(request):
    teachers = User.objects.filter(role='teacher', is_student=False).order_by('username')
    class_sections = ClassSection.objects.all()
    return render(request, 'attendance_app/manage_teachers.html', {
        'teachers': teachers,
        'class_sections': class_sections,
    })


@login_required
@user_passes_test(is_admin)
def assign_teacher(request, teacher_id):
    teacher = get_object_or_404(User, pk=teacher_id, role='teacher')
    class_section_id = request.POST.get('class_section')

    if class_section_id:
        try:
            cs = ClassSection.objects.get(pk=class_section_id)
            cs.teacher = teacher
            cs.save()
            messages.success(request, f'{teacher.username} assigned to {cs}.')
        except ClassSection.DoesNotExist:
            messages.error(request, 'Invalid class.')
    else:
        old_classes = ClassSection.objects.filter(teacher=teacher)
        for cs in old_classes:
            cs.teacher = None
            cs.save()
        messages.success(request, f'{teacher.username} unassigned from all classes.')

    return redirect('manage_teachers')


@login_required
@user_passes_test(is_admin)
def manage_classes(request):
    class_sections = ClassSection.objects.all().select_related('teacher')
    return render(request, 'attendance_app/manage_classes.html', {'class_sections': class_sections})


@require_http_methods(["GET"])
@login_required
@user_passes_test(is_teacher)
def api_students(request):
    class_section = request.user.managed_classes.first()
    if not class_section:
        return JsonResponse({'students': []})
    students = User.objects.filter(class_section=class_section, is_student=True).values('id', 'username')
    return JsonResponse({'students': list(students)})
