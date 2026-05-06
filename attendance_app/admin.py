from django.contrib import admin
from .models import Department, User, Attendance, AttendanceLog


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'department', 'employee_id', 'is_active_record')
    list_filter = ('role', 'department', 'is_active_record')
    search_fields = ('username', 'email', 'employee_id')


class AttendanceLogInline(admin.TabularInline):
    model = AttendanceLog
    extra = 0
    readonly_fields = ('timestamp',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'status', 'check_in', 'check_out')
    list_filter = ('status', 'date')
    search_fields = ('user__username',)
    inlines = [AttendanceLogInline]
