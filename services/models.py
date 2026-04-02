from django.db import models
from accounts.models import User
from inventory.models import WarehouseItem

class ServiceBooking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    SERVICE_TYPE_CHOICES = (
        ('repair', 'Repair'),
        ('maintenance', 'Maintenance'),
        ('inspection', 'Inspection'),
        ('warranty', 'Warranty Claim'),
    )
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_bookings')
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_service_man = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_services')
    scheduled_date = models.DateTimeField()
    completed_date = models.DateTimeField(null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Service #{self.id} - {self.customer.username} ({self.service_type})"

class ServiceItem(models.Model):
    booking = models.ForeignKey(ServiceBooking, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(WarehouseItem, on_delete=models.CASCADE)
    quantity_used = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.total_cost = self.quantity_used * self.unit_cost
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.item.name} x {self.quantity_used}"

class ServiceReport(models.Model):
    booking = models.OneToOneField(ServiceBooking, on_delete=models.CASCADE, related_name='report')
    technician_notes = models.TextField()
    parts_replaced = models.TextField(blank=True)
    labor_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    warranty_period = models.IntegerField(default=0)  # months
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_total(self):
        """Calculate total cost including labor and parts"""
        self.total_cost = self.labor_cost + self.parts_cost
        self.save()
    
    def __str__(self):
        return f"Report for Service #{self.booking.id}"