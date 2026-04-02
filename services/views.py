from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ServiceBooking, ServiceItem, ServiceReport
from inventory.models import WarehouseItem
from accounts.models import User
from django.db.models import Count, Sum
import json

@login_required
def book_service_view(request):
    """Customer books a service appointment"""
    if request.user.user_type != 'customer':
        messages.error(request, "Access denied. Customer access required.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        try:
            service_type = request.POST.get('service_type')
            description = request.POST.get('description')
            scheduled_date_str = request.POST.get('scheduled_date')
            estimated_cost = request.POST.get('estimated_cost')
            urgency = request.POST.get('urgency', 'normal')
            
            # Parse scheduled date
            scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%dT%H:%M')
            
            # Validate future date
            if scheduled_date <= timezone.now():
                messages.error(request, "Scheduled date must be in the future.")
                return redirect('services:book_service')
            
            # Create service booking
            booking = ServiceBooking.objects.create(
                customer=request.user,
                service_type=service_type,
                description=description,
                scheduled_date=scheduled_date,
                estimated_cost=float(estimated_cost) if estimated_cost else None,
                status='pending'
            )
            
            messages.success(request, "Service booking created successfully! We'll contact you soon to confirm.")
            return redirect('services:my_bookings')
            
        except Exception as e:
            messages.error(request, f"Error creating booking: {str(e)}")
    
    # Calculate minimum datetime for scheduling
    min_datetime = (timezone.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    
    context = {
        'min_datetime': min_datetime,
    }
    
    return render(request, 'services/book_service.html', context)

@login_required
def my_bookings_view(request):
    """Customer views their service bookings"""
    if request.user.user_type != 'customer':
        messages.error(request, "Access denied. Customer access required.")
        return redirect('dashboard:index')
    
    bookings = ServiceBooking.objects.filter(customer=request.user).order_by('-created_at')
    
    # Filter by status if specified
    status = request.GET.get('status')
    if status and status in ['pending', 'assigned', 'in_progress', 'completed', 'cancelled']:
        bookings = bookings.filter(status=status)
    
    context = {
        'bookings': bookings,
        'filter_status': status,
    }
    
    return render(request, 'services/my_bookings.html', context)

@login_required
def assigned_jobs_view(request):
    """Service man views their assigned jobs"""
    if request.user.user_type != 'service':
        messages.error(request, "Access denied. Service access required.")
        return redirect('dashboard:index')
    
    jobs = ServiceBooking.objects.filter(
        assigned_service_man=request.user
    ).exclude(status='completed').order_by('scheduled_date')
    
    context = {
        'jobs': jobs,
    }
    
    return render(request, 'services/assigned_jobs.html', context)

@login_required
def update_job_status_view(request, job_id):
    """Service man updates job status"""
    if request.user.user_type != 'service':
        messages.error(request, "Access denied. Service access required.")
        return redirect('dashboard:index')
    
    job = get_object_or_404(ServiceBooking, id=job_id)
    
    # Check if job is assigned to this service man
    if job.assigned_service_man != request.user:
        messages.error(request, "Access denied. This job is not assigned to you.")
        return redirect('services:assigned_jobs')
    
    if request.method == 'POST':
        try:
            new_status = request.POST.get('status')
            notes = request.POST.get('notes', '')
            
            job.status = new_status
            
            # If completing job, set completion date
            if new_status == 'completed':
                job.completed_date = timezone.now()
            
            job.save()
            
            messages.success(request, f"Job status updated to {new_status}.")
            return redirect('services:assigned_jobs')
            
        except Exception as e:
            messages.error(request, f"Error updating job status: {str(e)}")
    
    context = {
        'job': job,
    }
    
    return render(request, 'services/update_job_status.html', context)

@login_required
def create_service_report_view(request, job_id):
    """Service man creates service report"""
    if request.user.user_type != 'service':
        messages.error(request, "Access denied. Service access required.")
        return redirect('dashboard:index')
    
    job = get_object_or_404(ServiceBooking, id=job_id)
    
    # Check if job is assigned to this service man
    if job.assigned_service_man != request.user:
        messages.error(request, "Access denied. This job is not assigned to you.")
        return redirect('services:assigned_jobs')
    
    # Check if job is completed
    if job.status != 'completed':
        messages.error(request, "Can only create report for completed jobs.")
        return redirect('services:update_job_status', job_id=job_id)
    
    # Check if report already exists
    if hasattr(job, 'report'):
        messages.info(request, "Report already exists for this job.")
        return redirect('services:assigned_jobs')
    
    if request.method == 'POST':
        try:
            technician_notes = request.POST.get('technician_notes')
            parts_replaced = request.POST.get('parts_replaced', '')
            labor_hours = float(request.POST.get('labor_hours', 0))
            labor_cost = float(request.POST.get('labor_cost', 0))
            parts_cost = float(request.POST.get('parts_cost', 0))
            warranty_period = int(request.POST.get('warranty_period', 0))
            
            # Create service report
            report = ServiceReport.objects.create(
                booking=job,
                technician_notes=technician_notes,
                parts_replaced=parts_replaced,
                labor_hours=labor_hours,
                labor_cost=labor_cost,
                parts_cost=parts_cost,
                warranty_period=warranty_period
            )
            
            report.calculate_total()
            
            messages.success(request, "Service report created successfully.")
            return redirect('services:assigned_jobs')
            
        except Exception as e:
            messages.error(request, f"Error creating service report: {str(e)}")
    
    # Get available parts for selection
    available_parts = WarehouseItem.objects.filter(quantity__gt=0)
    
    context = {
        'job': job,
        'available_parts': available_parts,
    }
    
    return render(request, 'services/create_service_report.html', context)

@login_required
def admin_service_bookings_view(request):
    """Admin views all service bookings"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    bookings = ServiceBooking.objects.all().select_related('customer', 'assigned_service_man').order_by('-created_at')
    
    # Filter by status if specified
    status = request.GET.get('status')
    if status:
        bookings = bookings.filter(status=status)
    
    # Filter by service man if specified
    service_man_id = request.GET.get('service_man_id')
    if service_man_id:
        bookings = bookings.filter(assigned_service_man_id=service_man_id)
    
    # Get service men for filter dropdown
    service_men = User.objects.filter(user_type='service')
    
    context = {
        'bookings': bookings,
        'service_men': service_men,
        'selected_service_man': int(service_man_id) if service_man_id else None,
        'filter_status': status,
    }
    
    return render(request, 'services/admin_service_bookings.html', context)

@login_required
def assign_service_man_view(request, booking_id):
    """Admin assigns service man to booking"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    booking = get_object_or_404(ServiceBooking, id=booking_id)
    
    if request.method == 'POST':
        try:
            service_man_id = request.POST.get('service_man_id')
            service_man = get_object_or_404(User, id=service_man_id, user_type='service')
            
            booking.assigned_service_man = service_man
            booking.status = 'assigned'
            booking.save()
            
            messages.success(request, f"Service man {service_man.username} assigned to booking.")
            return redirect('services:admin_service_bookings')
            
        except Exception as e:
            messages.error(request, f"Error assigning service man: {str(e)}")
    
    # Get available service men
    service_men = User.objects.filter(user_type='service')
    
    context = {
        'booking': booking,
        'service_men': service_men,
    }
    
    return render(request, 'services/assign_service_man.html', context)
