from django.db import models
from accounts.models import User

class Attendance(models.Model):
    ATTENDANCE_STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('leave', 'Leave'),
    )
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=ATTENDANCE_STATUS_CHOICES, default='present')
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.employee.username} - {self.date} ({self.status})"
    
    def calculate_hours(self):
        """Calculate hours worked based on check-in and check-out times"""
        if self.check_in_time and self.check_out_time:
            from datetime import datetime, date
            check_in = datetime.combine(date.today(), self.check_in_time)
            check_out = datetime.combine(date.today(), self.check_out_time)
            duration = check_out - check_in
            self.hours_worked = duration.total_seconds() / 3600
            self.save()

class AttendanceSummary(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_summaries')
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    total_present = models.IntegerField(default=0)
    total_absent = models.IntegerField(default=0)
    total_late = models.IntegerField(default=0)
    total_leave = models.IntegerField(default=0)
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['employee', 'month', 'year']
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"{self.employee.username} - {self.month}/{self.year}: {self.total_present} days"
