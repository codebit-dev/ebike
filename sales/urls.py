from django.urls import path
from . import views

app_name = "sales"

urlpatterns = [
    # Dealer Sales
    path("dealer/sales/", views.dealer_sales_view, name="dealer_sales"),
    path("dealer/sales/create/", views.create_sale_view, name="create_sale"),
    path("dealer/sales/<int:sale_id>/", views.sale_detail_view, name="sale_detail"),
    path("dealer/sales/<int:sale_id>/generate-invoice/", views.generate_invoice_view, name="generate_invoice"),
    
    # Reports
    path("dealer/reports/sales/", views.dealer_sales_report_view, name="dealer_sales_report"),
    path("admin/reports/sales/", views.admin_sales_report_view, name="admin_sales_report"),
    
    # Payouts
    path("dealer/payouts/", views.dealer_payouts_view, name="dealer_payouts"),
    path("admin/payouts/", views.admin_payouts_view, name="admin_payouts"),
    path("admin/payouts/calculate/", views.calculate_payouts_view, name="calculate_payouts"),
    
    # Customer Purchasing
    path("customer/products/", views.customer_browse_products, name="customer_browse"),
    path("customer/cart/", views.customer_view_cart, name="customer_cart"),
    path("customer/cart/add/", views.customer_add_to_cart, name="customer_add_to_cart"),
    path("customer/cart/remove/<int:product_id>/", views.customer_remove_from_cart, name="customer_remove_from_cart"),
    path("customer/checkout/", views.customer_checkout, name="customer_checkout"),
    path("customer/orders/<int:order_id>/", views.customer_order_detail, name="customer_order_detail"),
    path("customer/orders/history/", views.customer_order_history, name="customer_order_history"),
    
    # Dealer Order Management
    path("dealer/orders/", views.dealer_order_list, name="dealer_order_list"),
    path("dealer/orders/<int:order_id>/approve/", views.dealer_approve_order, name="dealer_approve_order"),
]
