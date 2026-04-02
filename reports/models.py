from django.db import models
from accounts.models import User
from sales.models import Sale, DealerPayout
from inventory.models import WarehouseItem, DealerStock
from services.models import ServiceBooking

class SalesReport(models.Model):
    REPORT_TYPE_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_transactions = models.IntegerField(default=0)
    top_selling_items = models.JSONField(default=dict)  # Store item sales data
    top_performing_dealers = models.JSONField(default=dict)  # Store dealer performance data
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.report_type.title()} Sales Report: {self.start_date} to {self.end_date}"

class InventoryReport(models.Model):
    REPORT_TYPE_CHOICES = (
        ('current_stock', 'Current Stock'),
        ('low_stock', 'Low Stock Alert'),
        ('movement', 'Stock Movement'),
    )
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    generated_date = models.DateField(auto_now_add=True)
    warehouse_summary = models.JSONField(default=dict)  # Overall warehouse data
    dealer_stock_summary = models.JSONField(default=dict)  # Dealer-wise stock data
    low_stock_items = models.JSONField(default=dict)  # Items below threshold
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.report_type.title()} Report: {self.generated_date}"

class ServiceReportSummary(models.Model):
    REPORT_TYPE_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    )
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    total_bookings = models.IntegerField(default=0)
    completed_services = models.IntegerField(default=0)
    pending_services = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_service_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_type_breakdown = models.JSONField(default=dict)  # Service type statistics
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
        unique_together = ['report_type', 'start_date', 'end_date']
    
    def __str__(self):
        return f"{self.report_type.title()} Service Report: {self.start_date} to {self.end_date}"

class PerformanceReport(models.Model):
    TARGET_TYPE_CHOICES = (
        ('dealer', 'Dealer'),
        ('employee', 'Employee'),
        ('service_man', 'Service Man'),
    )
    
    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES)
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_reports')
    period_start = models.DateField()
    period_end = models.DateField()
    kpi_metrics = models.JSONField(default=dict)  # Key performance indicators
    targets_achieved = models.JSONField(default=dict)  # Target vs actual comparison
    ranking = models.IntegerField(null=True, blank=True)  # Performance ranking
    comments = models.TextField(blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
        unique_together = ['target_type', 'target_user', 'period_start', 'period_end']
    
    def __str__(self):
        return f"{self.target_type.title()} Performance Report: {self.target_user.username}"
