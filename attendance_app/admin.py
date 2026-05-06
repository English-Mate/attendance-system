from django.contrib import admin
from .models import Department, User, Attendance, AttendanceLog, AccountRequest, Roster, RosterEntry


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'department', 'employee_id', 'is_active_record', 'email_verified')
    list_filter = ('role', 'department', 'is_active_record', 'email_verified')
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


@admin.register(AccountRequest)
class AccountRequestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'desired_username', 'role', 'status', 'email_verified', 'created_at')
    list_filter = ('status', 'role', 'email_verified')
    search_fields = ('full_name', 'email', 'desired_username')
    readonly_fields = ('created_at', 'reviewed_at')


class RosterEntryInline(admin.TabularInline):
    model = RosterEntry
    extra = 0


@admin.register(Roster)
class RosterAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'date', 'created_by')
    list_filter = ('department', 'date')
    inlines = [RosterEntryInline]
