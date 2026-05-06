from django.contrib import admin
from .models import ClassSection, User, Attendance, AttendanceLog, AccountRequest


@admin.register(ClassSection)
class ClassSectionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'teacher')
    list_filter = ('grade', 'section')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'class_section', 'is_student')
    list_filter = ('role', 'is_student', 'class_section')
    search_fields = ('username',)


class AttendanceLogInline(admin.TabularInline):
    model = AttendanceLog
    extra = 0
    readonly_fields = ('timestamp',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'class_section', 'status')
    list_filter = ('status', 'date', 'class_section')
    search_fields = ('student__username',)
    inlines = [AttendanceLogInline]


@admin.register(AccountRequest)
class AccountRequestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'status', 'created_at', 'reviewed_at')
    list_filter = ('status',)
