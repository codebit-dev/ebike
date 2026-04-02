from django.db import models
from accounts.models import User
from inventory.models import DealerStock, WarehouseItem

class CustomerOrder(models.Model):
    """Customer order for purchasing products"""
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Payment Pending'),
        ('cod', 'Cash on Delivery'),
        ('completed', 'Payment Completed'),
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    dealer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='customer_orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_address = models.TextField()
    phone_number = models.CharField(max_length=15)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_number} - {self.customer.username}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            import uuid
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    @property
    def items_count(self):
        return self.order_items.count()

class OrderItem(models.Model):
    """Individual items in a customer order"""
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(WarehouseItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class Receipt(models.Model):
    """Receipt for completed orders"""
    order = models.OneToOneField(CustomerOrder, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=20, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, default='cod')
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Generate receipt number
            import uuid
            self.receipt_number = f"RCPT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Receipt {self.receipt_number} for {self.order.order_number}"

# Existing models remain unchanged...

class Sale(models.Model):
    SALE_STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    dealer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15)
    customer_email = models.EmailField(blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=SALE_STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sales')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Sale #{self.id} - {self.customer_name} ({self.total_amount})"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(WarehouseItem, on_delete=models.CASCADE)
    dealer_stock = models.ForeignKey(DealerStock, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.item.name} x {self.quantity}"

class Invoice(models.Model):
    sale = models.OneToOneField(Sale, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    issued_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='issued')  # issued, paid, overdue
    
    class Meta:
        ordering = ['-issued_date']
    
    def __str__(self):
        return f"Invoice {self.invoice_number} for Sale #{self.sale.id}"

class DealerPayout(models.Model):
    dealer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payouts')
    period_start = models.DateField()
    period_end = models.DateField()
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)  # percentage
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payout_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='calculated')  # calculated, paid, pending
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-period_end']
        unique_together = ['dealer', 'period_start', 'period_end']
    
    def calculate_payout(self):
        """Calculate commission and payout amount"""
        self.commission_amount = (self.total_sales * self.commission_rate) / 100
        self.payout_amount = self.total_sales - self.commission_amount
        self.save()
    
    def __str__(self):
        return f"Payout for {self.dealer.username}: {self.period_start} to {self.period_end}"
