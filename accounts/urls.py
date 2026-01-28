from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Landing Page
    path("", views.landing_view, name="landing"),
    
    # Admin URLs
    path("admin/login/", views.admin_login_view, name="admin_login"),
    path("admin/users/", views.admin_users_view, name="admin_users"),
    path("admin/users/create/", views.admin_user_create_view, name="admin_user_create"),
    path("admin/users/<int:user_id>/edit/", views.admin_user_edit_view, name="admin_user_edit"),
    path("admin/users/<int:user_id>/delete/", views.admin_user_delete_view, name="admin_user_delete"),
    
    # Dealer URLs
    path("dealer/register/", views.dealer_register_view, name="dealer_register"),
    path("dealer/login/", views.dealer_login_view, name="dealer_login"),
    
    # Service URLs
    path("service/register/", views.service_register_view, name="service_register"),
    path("service/login/", views.service_login_view, name="service_login"),
    
    # Employee URLs
    path("employee/register/", views.employee_register_view, name="employee_register"),
    path("employee/login/", views.employee_login_view, name="employee_login"),
    
    # Customer URLs
    path("customer/register/", views.customer_register_view, name="customer_register"),
    path("customer/login/", views.customer_login_view, name="customer_login"),
    
    # Legacy URLs
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]
