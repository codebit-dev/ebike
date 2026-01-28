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
