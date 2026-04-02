from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    # Employee Attendance
    path("employee/mark/", views.mark_attendance_view, name="mark_attendance"),
    path("employee/history/", views.attendance_history_view, name="attendance_history"),
    
    # Dealer View Employee Attendance
    path("dealer/employee-attendance/", views.dealer_employee_attendance_view, name="dealer_employee_attendance"),
    
    # Admin Attendance Management
    path("admin/summary/", views.attendance_summary_view, name="attendance_summary"),
    path("admin/reports/", views.attendance_reports_view, name="attendance_reports"),
]
