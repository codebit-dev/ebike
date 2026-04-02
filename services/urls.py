from django.urls import path
from . import views

app_name = "services"

urlpatterns = [
    # Customer Service Booking
    path("customer/book/", views.book_service_view, name="book_service"),
    path("customer/my-bookings/", views.my_bookings_view, name="my_bookings"),
    
    # Service Man Dashboard
    path("man/jobs/", views.assigned_jobs_view, name="assigned_jobs"),
    path("man/jobs/<int:job_id>/update/", views.update_job_status_view, name="update_job_status"),
    path("man/jobs/<int:job_id>/report/", views.create_service_report_view, name="create_service_report"),
    
    # Admin Service Management
    path("admin/bookings/", views.admin_service_bookings_view, name="admin_service_bookings"),
    path("admin/bookings/<int:booking_id>/assign/", views.assign_service_man_view, name="assign_service_man"),
]
