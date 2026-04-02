from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    # Dealer Stock Management
    path("dealer/stock/", views.dealer_stock_view, name="dealer_stock"),
    path("dealer/stock/request/", views.stock_request_view, name="stock_request"),
    
    # Admin Stock Management
    path("admin/stock/", views.admin_stock_view, name="admin_stock"),
    path("admin/products/", views.product_management_view, name="product_management"),
    path("admin/products/create/", views.product_create_view, name="product_create"),
    path("admin/products/<int:product_id>/edit/", views.product_edit_view, name="product_edit"),
    path("admin/requests/", views.stock_requests_view, name="stock_requests"),
    path("admin/requests/<int:request_id>/approve/", views.approve_stock_request_view, name="approve_request"),
]
