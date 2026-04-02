from django.db import models
from accounts.models import User
from inventory.models import StockRequest

class ApprovalWorkflow(models.Model):
    APPROVAL_TYPE_CHOICES = (
        ('stock_request', 'Stock Request'),
        ('price_change', 'Price Change'),
        ('new_product', 'New Product'),
        ('dealer_registration', 'Dealer Registration'),
    )
    
    REQUEST_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    approval_type = models.CharField(max_length=30, choices=APPROVAL_TYPE_CHOICES)
    reference_id = models.IntegerField()  # ID of the related object
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_requests')
    current_approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pending_approvals')
    status = models.CharField(max_length=20, choices=REQUEST_STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.approval_type} - {self.requester.username} ({self.status})"

class ApprovalStep(models.Model):
    workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.CASCADE, related_name='steps')
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_steps')
    step_order = models.IntegerField()
    status = models.CharField(max_length=20, default='pending')  # pending, approved, rejected
    comments = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['step_order']
        unique_together = ['workflow', 'step_order']
    
    def __str__(self):
        return f"Step {self.step_order} for {self.workflow.approval_type}"

class DailySlotLimit(models.Model):
    service_man = models.ForeignKey(User, on_delete=models.CASCADE, related_name='slot_limits')
    date = models.DateField()
    max_slots = models.IntegerField(default=5)  # Maximum service jobs per day
    current_slots = models.IntegerField(default=0)  # Current booked slots
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['service_man', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.service_man.username} - {self.date}: {self.current_slots}/{self.max_slots}"
    
    def can_assign_slot(self):
        """Check if service man can accept more jobs for this date"""
        return self.current_slots < self.max_slots
    
    def assign_slot(self):
        """Increment slot count if within limit"""
        if self.can_assign_slot():
            self.current_slots += 1
            self.save()
            return True
        return False
