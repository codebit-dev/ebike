from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, date
from .models import ApprovalWorkflow, ApprovalStep, DailySlotLimit
from accounts.models import User
from inventory.models import StockRequest
from services.models import ServiceBooking
import json

@login_required
def admin_approval_dashboard_view(request):
    """Admin dashboard for managing approvals"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    # Get pending approvals
    pending_workflows = ApprovalWorkflow.objects.filter(status='pending').select_related('requester')
    
    # Get recent approvals
    recent_approvals = ApprovalWorkflow.objects.exclude(status='pending').order_by('-updated_at')[:10]
    
    # Statistics
    total_pending = pending_workflows.count()
    total_approved = ApprovalWorkflow.objects.filter(status='approved').count()
    total_rejected = ApprovalWorkflow.objects.filter(status='rejected').count()
    
    # Calculate approval rate
    approval_rate = (total_approved / total_pending * 100) if total_pending > 0 else 0
    
    context = {
        'pending_workflows': pending_workflows,
        'recent_approvals': recent_approvals,
        'total_pending': total_pending,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'approval_rate': approval_rate,
    }
    
    return render(request, 'approvals/admin_dashboard.html', context)

@login_required
def approve_workflow_view(request, workflow_id):
    """Approve an approval workflow"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    workflow = get_object_or_404(ApprovalWorkflow, id=workflow_id)
    
    if request.method == 'POST':
        try:
            comments = request.POST.get('comments', '')
            
            workflow.status = 'approved'
            workflow.comments = comments
            workflow.approved_at = timezone.now()
            workflow.current_approver = request.user
            workflow.save()
            
            # Handle specific approval types
            if workflow.approval_type == 'stock_request':
                # Process stock request approval
                stock_request = get_object_or_404(StockRequest, id=workflow.reference_id)
                stock_request.status = 'approved'
                stock_request.approved_by = request.user
                stock_request.save()
            
            messages.success(request, "Approval granted successfully.")
            return redirect('approvals:admin_dashboard')
            
        except Exception as e:
            messages.error(request, f"Error approving workflow: {str(e)}")
    
    context = {
        'workflow': workflow,
    }
    
    return render(request, 'approvals/approve_workflow.html', context)

@login_required
def reject_workflow_view(request, workflow_id):
    """Reject an approval workflow"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    workflow = get_object_or_404(ApprovalWorkflow, id=workflow_id)
    
    if request.method == 'POST':
        try:
            comments = request.POST.get('comments', '')
            
            workflow.status = 'rejected'
            workflow.comments = comments
            workflow.rejected_at = timezone.now()
            workflow.current_approver = request.user
            workflow.save()
            
            # Handle specific rejection types
            if workflow.approval_type == 'stock_request':
                stock_request = get_object_or_404(StockRequest, id=workflow.reference_id)
                stock_request.status = 'rejected'
                stock_request.approved_by = request.user
                stock_request.save()
            
            messages.success(request, "Workflow rejected successfully.")
            return redirect('approvals:admin_dashboard')
            
        except Exception as e:
            messages.error(request, f"Error rejecting workflow: {str(e)}")
    
    context = {
        'workflow': workflow,
    }
    
    return render(request, 'approvals/reject_workflow.html', context)

@login_required
def check_daily_slot_limit_view(request):
    """Check if service man can accept more jobs for a given date"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            service_man_id = data.get('service_man_id')
            date_str = data.get('date')
            
            service_man = get_object_or_404(User, id=service_man_id, user_type='service')
            check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Get or create daily slot limit
            slot_limit, created = DailySlotLimit.objects.get_or_create(
                service_man=service_man,
                date=check_date,
                defaults={'max_slots': 5}
            )
            
            can_accept = slot_limit.can_assign_slot()
            
            return JsonResponse({
                'can_accept': can_accept,
                'current_slots': slot_limit.current_slots,
                'max_slots': slot_limit.max_slots
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def partial_approval_view(request):
    """Handle partial approval of requests"""
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            workflow_id = data.get('workflow_id')
            approved_amount = data.get('approved_amount')
            comments = data.get('comments', '')
            
            workflow = get_object_or_404(ApprovalWorkflow, id=workflow_id)
            
            # Update workflow for partial approval
            workflow.status = 'partially_approved'
            workflow.comments = comments
            workflow.approved_at = timezone.now()
            workflow.current_approver = request.user
            workflow.save()
            
            # Handle specific partial approval types
            if workflow.approval_type == 'stock_request':
                stock_request = get_object_or_404(StockRequest, id=workflow.reference_id)
                stock_request.quantity_approved = int(approved_amount)
                stock_request.status = 'partially_approved'
                stock_request.approved_by = request.user
                stock_request.save()
            
            return JsonResponse({'success': True, 'message': 'Partial approval processed'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
