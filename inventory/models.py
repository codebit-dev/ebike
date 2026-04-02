from django.db import models
from accounts.models import User

class WarehouseItem(models.Model):
    CATEGORY_CHOICES = (
        ('ebike', 'E-Bike'),
        ('parts', 'Parts'),
        ('accessories', 'Accessories'),
    )
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    sku = models.CharField(max_length=50, unique=True)
    quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inventory_updates')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.sku}) - Qty: {self.quantity}"

class DealerStock(models.Model):
    dealer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dealer_stocks')
    item = models.ForeignKey(WarehouseItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    allocated_quantity = models.IntegerField(default=0)  # Quantity allocated for sales
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['dealer', 'item']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.dealer.username} - {self.item.name}: {self.quantity}"
    
    @property
    def available_quantity(self):
        return self.quantity - self.allocated_quantity

class StockRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('partially_approved', 'Partially Approved'),
        ('rejected', 'Rejected'),
    )
    
    dealer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_requests')
    item = models.ForeignKey(WarehouseItem, on_delete=models.CASCADE)
    quantity_requested = models.IntegerField()
    quantity_approved = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.dealer.username} - {self.item.name}: {self.quantity_requested} ({self.status})"
