from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('request-account/', views.request_account, name='request_account'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('request-status/<str:token>/', views.request_status, name='request_status'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/roster/', views.roster_attendance, name='roster_attendance'),
    path('attendance/records/', views.attendance_records, name='attendance_records'),
    path('attendance/record/<int:record_id>/', views.attendance_detail, name='attendance_detail'),
    path('roster/<int:roster_id>/', views.roster_detail, name='roster_detail'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('account-requests/', views.account_requests, name='account_requests'),
    path('account-requests/<int:request_id>/approve/', views.approve_request, name='approve_request'),
    path('account-requests/<int:request_id>/reject/', views.reject_request, name='reject_request'),
    path('api/attendance/', views.api_attendance, name='api_attendance'),
]
