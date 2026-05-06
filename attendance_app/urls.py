from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('request-account/', views.request_account, name='request_account'),
    path('request-status/<str:token>/', views.request_status, name='request_status'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('my-class/', views.my_class, name='my_class'),
    path('my-class/add-student/', views.add_student, name='add_student'),
    path('my-class/remove-student/<int:student_id>/', views.remove_student, name='remove_student'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/records/', views.attendance_records, name='attendance_records'),
    path('api/students/', views.api_students, name='api_students'),
    path('account-requests/', views.account_requests, name='account_requests'),
    path('account-requests/<int:request_id>/approve/', views.approve_request, name='approve_request'),
    path('account-requests/<int:request_id>/reject/', views.reject_request, name='reject_request'),
    path('manage-teachers/', views.manage_teachers, name='manage_teachers'),
    path('manage-teachers/<int:teacher_id>/assign/', views.assign_teacher, name='assign_teacher'),
    path('manage-classes/', views.manage_classes, name='manage_classes'),
]
