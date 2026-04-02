from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import SalesReport, InventoryReport, ServiceReportSummary, PerformanceReport
from sales.models import Sale
from inventory.models import WarehouseItem, DealerStock
from services.models import ServiceBooking
from accounts.models import User
from django.db.models import Count, Sum, Avg
import json

@login_required
def generate_sales_report_view(request):
    """Generate sales report"""
    if request.user.user_type not in ['admin', 'dealer']:
        messages.error(request, "Access denied.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        try:
            report_type = request.POST.get('report_type')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            
            start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Filter sales based on user type
            if request.user.user_type == 'dealer':
                sales = Sale.objects.filter(
                    dealer=request.user,
                    created_at__date__range=[start_date_parsed, end_date_parsed],
                    status='completed'
                )
            else:
                sales = Sale.objects.filter(
                    created_at__date__range=[start_date_parsed, end_date_parsed],
                    status='completed'
                )
            
            total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or 0
            total_transactions = sales.count()
            
            # Create report
            report = SalesReport.objects.create(
                report_type=report_type,
                start_date=start_date_parsed,
                end_date=end_date_parsed,
                total_sales=total_sales,
                total_transactions=total_transactions,
                generated_by=request.user
            )
            
            messages.success(request, "Sales report generated successfully.")
            return redirect('reports:view_sales_report', report_id=report.id)
            
        except Exception as e:
            messages.error(request, f"Error generating report: {str(e)}")
    
    context = {
        'default_start': (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'default_end': timezone.now().strftime('%Y-%m-%d'),
    }
    
    return render(request, 'reports/generate_sales_report.html', context)

@login_required
def view_sales_report_view(request, report_id):
    """View a specific sales report"""
    report = get_object_or_404(SalesReport, id=report_id)
    
    # Check access rights
    if request.user.user_type == 'dealer' and report.generated_by != request.user:
        messages.error(request, "Access denied. You can only view your own reports.")
        return redirect('dashboard:index')
    
    context = {
        'report': report,
    }
    
    return render(request, 'reports/view_sales_report.html', context)

@login_required
def generate_inventory_report_view(request):
    """Generate inventory report"""
    if request.user.user_type not in ['admin', 'dealer']:
        messages.error(request, "Access denied.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        try:
            report_type = request.POST.get('report_type')
            
            # Generate warehouse summary
            warehouse_items = WarehouseItem.objects.all()
            warehouse_summary = {
                'total_items': warehouse_items.count(),
                'total_value': float(sum(item.quantity * item.unit_price for item in warehouse_items)),
                'low_stock_count': warehouse_items.filter(quantity__lt=10).count()
            }
            
            # Generate dealer stock summary (for admin)
            dealer_summary = {}
            if request.user.user_type == 'admin':
                dealer_stocks = DealerStock.objects.all()
                dealer_summary = {
                    'total_dealers': User.objects.filter(user_type='dealer').count(),
                    'total_dealer_items': dealer_stocks.count(),
                    'total_dealer_value': float(sum(stock.quantity * stock.selling_price for stock in dealer_stocks))
                }
            
            # Create report
            report = InventoryReport.objects.create(
                report_type=report_type,
                warehouse_summary=warehouse_summary,
                dealer_stock_summary=dealer_summary,
                generated_by=request.user
            )
            
            messages.success(request, "Inventory report generated successfully.")
            return redirect('reports:view_inventory_report', report_id=report.id)
            
        except Exception as e:
            messages.error(request, f"Error generating report: {str(e)}")
    
    context = {}
    
    return render(request, 'reports/generate_inventory_report.html', context)

@login_required
def view_inventory_report_view(request, report_id):
    """View a specific inventory report"""
    report = get_object_or_404(InventoryReport, id=report_id)
    
    # Check access rights
    if request.user.user_type == 'dealer' and report.generated_by != request.user:
        messages.error(request, "Access denied. You can only view your own reports.")
        return redirect('dashboard:index')
    
    context = {
        'report': report,
    }
    
    return render(request, 'reports/view_inventory_report.html', context)

@login_required
def generate_service_report_view(request):
    """Generate service report"""
    if request.user.user_type not in ['admin', 'service']:
        messages.error(request, "Access denied.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        try:
            report_type = request.POST.get('report_type')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            
            start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Get service bookings
            bookings = ServiceBooking.objects.filter(
                created_at__date__range=[start_date_parsed, end_date_parsed]
            )
            
            completed_services = bookings.filter(status='completed').count()
            total_revenue = bookings.filter(status='completed').aggregate(
                total=Sum('actual_cost')
            )['total'] or 0
            
            # Create report
            report = ServiceReportSummary.objects.create(
                report_type=report_type,
                start_date=start_date_parsed,
                end_date=end_date_parsed,
                total_bookings=bookings.count(),
                completed_services=completed_services,
                pending_services=bookings.exclude(status='completed').count(),
                total_revenue=total_revenue,
                average_service_cost=float(total_revenue / completed_services) if completed_services > 0 else 0,
                generated_by=request.user
            )
            
            messages.success(request, "Service report generated successfully.")
            return redirect('reports:view_service_report', report_id=report.id)
            
        except Exception as e:
            messages.error(request, f"Error generating report: {str(e)}")
    
    context = {
        'default_start': (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'default_end': timezone.now().strftime('%Y-%m-%d'),
    }
    
    return render(request, 'reports/generate_service_report.html', context)

@login_required
def view_service_report_view(request, report_id):
    """View a specific service report"""
    report = get_object_or_404(ServiceReportSummary, id=report_id)
    
    # Check access rights
    if request.user.user_type == 'service' and report.generated_by != request.user:
        messages.error(request, "Access denied. You can only view your own reports.")
        return redirect('dashboard:index')
    
    context = {
        'report': report,
    }
    
    return render(request, 'reports/view_service_report.html', context)

@login_required
def generate_performance_report_view(request):
    """Generate performance report"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        try:
            target_type = request.POST.get('target_type')
            period_start = request.POST.get('period_start')
            period_end = request.POST.get('period_end')
            
            period_start_parsed = datetime.strptime(period_start, '%Y-%m-%d').date()
            period_end_parsed = datetime.strptime(period_end, '%Y-%m-%d').date()
            
            # For demo purposes, create a simple performance report
            report = PerformanceReport.objects.create(
                target_type=target_type,
                target_user=request.user,  # In real app, this would be the target user
                period_start=period_start_parsed,
                period_end=period_end_parsed,
                kpi_metrics={'demo': 'data'},
                targets_achieved={'demo': 'results'},
                generated_by=request.user
            )
            
            messages.success(request, "Performance report generated successfully.")
            return redirect('reports:view_performance_report', report_id=report.id)
            
        except Exception as e:
            messages.error(request, f"Error generating report: {str(e)}")
    
    context = {
        'default_start': (timezone.now().replace(day=1) - timedelta(days=1)).replace(day=1),
        'default_end': timezone.now().replace(day=1) - timedelta(days=1),
    }
    
    return render(request, 'reports/generate_performance_report.html', context)

@login_required
def view_performance_report_view(request, report_id):
    """View a specific performance report"""
    report = get_object_or_404(PerformanceReport, id=report_id)
    
    context = {
        'report': report,
    }
    
    return render(request, 'reports/view_performance_report.html', context)
