from django.urls import path
from . import views

app_name = "approvals"

urlpatterns = [
    # Admin Approval Dashboard
    path("admin/dashboard/", views.admin_approval_dashboard_view, name="admin_dashboard"),
    path("admin/workflows/<int:workflow_id>/approve/", views.approve_workflow_view, name="approve_workflow"),
    path("admin/workflows/<int:workflow_id>/reject/", views.reject_workflow_view, name="reject_workflow"),
    
    # Shared Features
    path("check-slot-limit/", views.check_daily_slot_limit_view, name="check_slot_limit"),
    path("partial-approval/", views.partial_approval_view, name="partial_approval"),
]
