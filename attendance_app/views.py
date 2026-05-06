from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from .models import User, Attendance, Department, AttendanceLog, AccountRequest, Roster, RosterEntry
from .forms import AttendanceForm, UserForm, AccountRequestForm


def is_admin(user):
    return user.is_authenticated and user.is_admin


def is_teacher(user):
    return user.is_authenticated and user.is_teacher


def send_verification_email(request_obj):
    token = request_obj.generate_verification_token()
    request_obj.save()

    verify_url = f"{settings.SITE_URL}/verify-email/{token}/"
    send_mail(
        'Verify Your Email - Attendance System',
        f'Hello {request_obj.full_name},\n\nPlease verify your email by clicking the link below:\n{verify_url}\n\nYour account request will be reviewed by the admin after verification.\n\nThank you.',
        settings.DEFAULT_FROM_EMAIL,
        [request_obj.email],
        fail_silently=False,
    )


def send_approval_email(request_obj, password=None):
    login_url = f"{settings.SITE_URL}/login/"
    body = f'Hello {request_obj.full_name},\n\nYour account request has been approved!\n\n'
    if password:
        body += f'Username: {request_obj.desired_username}\nPassword: {password}\n\n'
    body += f'You can login at: {login_url}\n\nThank you.'
    send_mail(
        'Account Approved - Attendance System',
        body,
        settings.DEFAULT_FROM_EMAIL,
        [request_obj.email],
        fail_silently=False,
    )


def send_rejection_email(request_obj):
    send_mail(
        'Account Request Rejected - Attendance System',
        f'Hello {request_obj.full_name},\n\nYour account request has been rejected.\n\nReason: {request_obj.review_notes}\n\nIf you believe this is an error, please contact the administrator.',
        settings.DEFAULT_FROM_EMAIL,
        [request_obj.email],
        fail_silently=False,
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active_record:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Your account has been deactivated.')
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
                email=form.cleaned_data['email'],
                status='pending'
            ).exists()

            if existing:
                messages.error(request, 'A pending request already exists for this email.')
            else:
                account_request = form.save(commit=False)
                account_request.save()
                try:
                    send_verification_email(account_request)
                    messages.success(request, 'Request submitted! Please check your email to verify your account.')
                except Exception:
                    messages.success(request, 'Request submitted! Your account is pending admin approval.')
                return redirect('request_status', token=account_request.verification_token)
    else:
        form = AccountRequestForm()

    return render(request, 'attendance_app/request_account.html', {'form': form})


def verify_email(request, token):
    account_request = get_object_or_404(AccountRequest, verification_token=token)

    if account_request.status != 'pending':
        messages.error(request, 'This request has already been processed.')
        return redirect('login')

    if account_request.email_verified:
        messages.info(request, 'Email already verified.')
    else:
        account_request.email_verified = True
        account_request.save()
        messages.success(request, 'Email verified successfully! Your request is now pending admin approval.')

    return redirect('request_status', token=token)


def request_status(request, token):
    account_request = get_object_or_404(AccountRequest, verification_token=token)
    return render(request, 'attendance_app/request_status.html', {'request': account_request})


@login_required
def dashboard(request):
    today = timezone.now().date()
    total_users = User.objects.filter(is_active_record=True).count()
    present_today = Attendance.objects.filter(date=today, status='present').count()
    absent_today = Attendance.objects.filter(date=today, status='absent').count()
    late_today = Attendance.objects.filter(date=today, status='late').count()

    if request.user.is_teacher:
        today_attendance = Attendance.objects.filter(date=today).select_related('user').order_by('-created_at')
    else:
        today_attendance = Attendance.objects.filter(user=request.user, date=today)

    recent_records = Attendance.objects.select_related('user').order_by('-created_at')[:10]

    pending_requests = AccountRequest.objects.filter(status='pending').count() if request.user.is_admin else 0

    context = {
        'total_users': total_users,
        'present_today': present_today,
        'absent_today': absent_today,
        'late_today': late_today,
        'today_attendance': today_attendance,
        'recent_records': recent_records,
        'pending_requests': pending_requests,
    }
    return render(request, 'attendance_app/dashboard.html', context)


@login_required
@user_passes_test(is_teacher)
def mark_attendance(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.recorded_by = request.user
            attendance.save()

            AttendanceLog.objects.create(
                attendance=attendance,
                action='Marked attendance',
                performed_by=request.user,
                details=f'Status: {attendance.status}'
            )
            messages.success(request, f'Attendance marked for {attendance.user.username}.')
            return redirect('dashboard')
    else:
        form = AttendanceForm()

    return render(request, 'attendance_app/mark_attendance.html', {'form': form})


@login_required
@user_passes_test(is_teacher)
def roster_attendance(request):
    if request.method == 'POST':
        roster_name = request.POST.get('roster_name')
        date = request.POST.get('date', timezone.now().date())
        department_id = request.POST.get('department')
        statuses = request.POST.getlist('status')
        notes = request.POST.getlist('notes')

        with transaction.atomic():
            roster = Roster.objects.create(
                name=roster_name,
                department_id=department_id,
                date=date,
                created_by=request.user
            )

            students = User.objects.filter(
                department_id=department_id,
                role='student',
                is_active_record=True
            ).order_by('username')

            for i, student in enumerate(students):
                status = statuses[i] if i < len(statuses) else 'present'
                student_notes = notes[i] if i < len(notes) else ''

                entry = RosterEntry.objects.create(
                    roster=roster,
                    student=student,
                    status=status,
                    notes=student_notes
                )

                Attendance.objects.update_or_create(
                    user=student,
                    date=date,
                    defaults={
                        'status': status,
                        'notes': student_notes,
                        'recorded_by': request.user,
                    }
                )

        messages.success(request, f'Roster "{roster_name}" saved successfully.')
        return redirect('attendance_records')

    departments = Department.objects.all()
    return render(request, 'attendance_app/roster_attendance.html', {'departments': departments})


@login_required
def attendance_records(request):
    if request.user.is_teacher:
        records = Attendance.objects.all().select_related('user').order_by('-date', '-created_at')
        rosters = Roster.objects.all().select_related('department').order_by('-date')
    else:
        records = Attendance.objects.filter(user=request.user).order_by('-date', '-created_at')
        rosters = []

    date_filter = request.GET.get('date')
    user_filter = request.GET.get('user')
    status_filter = request.GET.get('status')

    if date_filter:
        records = records.filter(date=date_filter)
    if user_filter and request.user.is_teacher:
        records = records.filter(user_id=user_filter)
    if status_filter:
        records = records.filter(status=status_filter)

    context = {
        'records': records,
        'rosters': rosters,
        'users': User.objects.filter(is_active_record=True) if request.user.is_teacher else [],
    }
    return render(request, 'attendance_app/attendance_records.html', context)


@login_required
def attendance_detail(request, record_id):
    record = get_object_or_404(Attendance, pk=record_id)
    if not request.user.is_teacher and record.user != request.user:
        messages.error(request, 'You do not have permission to view this record.')
        return redirect('dashboard')

    logs = record.logs.all()
    return render(request, 'attendance_app/attendance_detail.html', {'record': record, 'logs': logs})


@login_required
def roster_detail(request, roster_id):
    roster = get_object_or_404(Roster, pk=roster_id)
    entries = roster.entries.select_related('student').order_by('student__username')
    return render(request, 'attendance_app/roster_detail.html', {'roster': roster, 'entries': entries})


@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all().select_related('department').order_by('username')
    departments = Department.objects.all()
    return render(request, 'attendance_app/user_list.html', {'users': users, 'departments': departments})


@login_required
@user_passes_test(is_admin)
def create_user(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.email_verified = True
            user.save()
            messages.success(request, f'User {user.username} created successfully.')
            return redirect('user_list')
    else:
        form = UserForm()
    return render(request, 'attendance_app/user_form.html', {'form': form, 'title': 'Create User'})


@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            if form.cleaned_data.get('password'):
                user.set_password(form.cleaned_data['password'])
                user.save()
            messages.success(request, f'User {user.username} updated successfully.')
            return redirect('user_list')
    else:
        form = UserForm(instance=user)
    return render(request, 'attendance_app/user_form.html', {'form': form, 'title': f'Edit {user.username}'})


@login_required
@user_passes_test(is_admin)
def account_requests(request):
    pending = AccountRequest.objects.filter(status='pending').order_by('-created_at')
    processed = AccountRequest.objects.exclude(status='pending').order_by('-reviewed_at')[:20]
    return render(request, 'attendance_app/account_requests.html', {'pending': pending, 'processed': processed})


@login_required
@user_passes_test(is_admin)
def approve_request(request, request_id):
    account_request = get_object_or_404(AccountRequest, pk=request_id, status='pending')

    if not account_request.email_verified:
        messages.error(request, 'Email must be verified before approval.')
        return redirect('account_requests')

    if request.method == 'POST':
        with transaction.atomic():
            password = User.objects.make_random_password()
            user = User.objects.create_user(
                username=account_request.desired_username,
                email=account_request.email,
                password=password,
                role=account_request.role,
                department=account_request.department,
                email_verified=True,
            )

            account_request.status = 'approved'
            account_request.reviewed_by = request.user
            account_request.reviewed_at = timezone.now()
            account_request.review_notes = request.POST.get('review_notes', '')
            account_request.save()

        try:
            send_approval_email(account_request, password)
        except Exception:
            messages.warning(request, f'User created but email could not be sent. Password: {password}')
        else:
            messages.success(request, f'{user.username} approved and notified via email.')

        return redirect('account_requests')

    return render(request, 'attendance_app/approve_request.html', {'request': account_request})


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

        try:
            send_rejection_email(account_request)
        except Exception:
            pass

        messages.success(request, f'Request from {account_request.full_name} has been rejected.')
        return redirect('account_requests')

    return render(request, 'attendance_app/reject_request.html', {'request': account_request})


@require_http_methods(["GET"])
@login_required
def api_attendance(request):
    date = request.GET.get('date', timezone.now().date())
    records = Attendance.objects.filter(date=date).select_related('user')
    data = [
        {
            'user': r.user.username,
            'status': r.status,
            'check_in': str(r.check_in) if r.check_in else None,
            'check_out': str(r.check_out) if r.check_out else None,
        }
        for r in records
    ]
    return JsonResponse({'date': str(date), 'records': data})
