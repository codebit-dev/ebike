from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    # Sales Reports
    path("sales/generate/", views.generate_sales_report_view, name="generate_sales_report"),
    path("sales/view/<int:report_id>/", views.view_sales_report_view, name="view_sales_report"),
    
    # Inventory Reports
    path("inventory/generate/", views.generate_inventory_report_view, name="generate_inventory_report"),
    path("inventory/view/<int:report_id>/", views.view_inventory_report_view, name="view_inventory_report"),
    
    # Service Reports
    path("services/generate/", views.generate_service_report_view, name="generate_service_report"),
    path("services/view/<int:report_id>/", views.view_service_report_view, name="view_service_report"),
    
    # Performance Reports
    path("performance/generate/", views.generate_performance_report_view, name="generate_performance_report"),
    path("performance/view/<int:report_id>/", views.view_performance_report_view, name="view_performance_report"),
]
