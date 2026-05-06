from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import User, Attendance, Department, AttendanceLog
from .forms import AttendanceForm, UserForm


def is_admin(user):
    return user.is_authenticated and user.is_admin


def is_manager(user):
    return user.is_authenticated and user.is_manager


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


@login_required
def dashboard(request):
    today = timezone.now().date()
    total_users = User.objects.filter(is_active_record=True).count()
    present_today = Attendance.objects.filter(date=today, status='present').count()
    absent_today = Attendance.objects.filter(date=today, status='absent').count()
    late_today = Attendance.objects.filter(date=today, status='late').count()

    if request.user.is_manager:
        today_attendance = Attendance.objects.filter(date=today).select_related('user').order_by('-created_at')
    else:
        today_attendance = Attendance.objects.filter(user=request.user, date=today)

    recent_records = Attendance.objects.select_related('user').order_by('-created_at')[:10]

    context = {
        'total_users': total_users,
        'present_today': present_today,
        'absent_today': absent_today,
        'late_today': late_today,
        'today_attendance': today_attendance,
        'recent_records': recent_records,
    }
    return render(request, 'attendance_app/dashboard.html', context)


@login_required
@user_passes_test(is_manager)
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
def attendance_records(request):
    if request.user.is_manager:
        records = Attendance.objects.all().select_related('user').order_by('-date', '-created_at')
    else:
        records = Attendance.objects.filter(user=request.user).order_by('-date', '-created_at')

    date_filter = request.GET.get('date')
    user_filter = request.GET.get('user')
    status_filter = request.GET.get('status')

    if date_filter:
        records = records.filter(date=date_filter)
    if user_filter and request.user.is_manager:
        records = records.filter(user_id=user_filter)
    if status_filter:
        records = records.filter(status=status_filter)

    context = {
        'records': records,
        'users': User.objects.filter(is_active_record=True) if request.user.is_manager else [],
    }
    return render(request, 'attendance_app/attendance_records.html', context)


@login_required
def attendance_detail(request, record_id):
    record = get_object_or_404(Attendance, pk=record_id)
    if not request.user.is_manager and record.user != request.user:
        messages.error(request, 'You do not have permission to view this record.')
        return redirect('dashboard')

    logs = record.logs.all()
    return render(request, 'attendance_app/attendance_detail.html', {'record': record, 'logs': logs})


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
