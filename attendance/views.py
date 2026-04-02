from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Attendance, AttendanceSummary
from accounts.models import User
from django.db.models import Count, Sum, Avg, Q
import calendar

@login_required
def mark_attendance_view(request):
    """Employee marks their daily attendance"""
    if request.user.user_type != 'employee':
        messages.error(request, "Access denied. Employee access required.")
        return redirect('dashboard:index')
    
    today = timezone.now().date()
    current_time = timezone.now().strftime('%H:%M')
    
    # Check if attendance already marked today
    todays_attendance = Attendance.objects.filter(
        employee=request.user,
        date=today
    ).first()
    
    if request.method == 'POST':
        if todays_attendance:
            messages.warning(request, "Attendance already marked for today.")
            return redirect('attendance:mark_attendance')
        
        try:
            status = request.POST.get('status')
            check_in_time = request.POST.get('check_in_time')
            notes = request.POST.get('notes', '')
            
            # Parse time if provided
            check_in_parsed = None
            if check_in_time:
                check_in_parsed = datetime.strptime(check_in_time, '%H:%M').time()
            
            Attendance.objects.create(
                employee=request.user,
                date=today,
                status=status,
                check_in_time=check_in_parsed,
                notes=notes
            )
            
            messages.success(request, "Attendance marked successfully!")
            return redirect('attendance:mark_attendance')
            
        except Exception as e:
            messages.error(request, f"Error marking attendance: {str(e)}")
    
    # Get recent attendance history
    recent_attendance = Attendance.objects.filter(
        employee=request.user
    ).order_by('-date')[:10]
    
    context = {
        'today': today,
        'current_time': current_time,
        'todays_attendance': todays_attendance,
        'recent_attendance': recent_attendance,
    }
    
    return render(request, 'attendance/mark_attendance.html', context)

@login_required
def attendance_history_view(request):
    """View attendance history"""
    if request.user.user_type not in ['employee', 'admin']:
        messages.error(request, "Access denied.")
        return redirect('dashboard:index')
    
    # For employees, only show their own attendance
    if request.user.user_type == 'employee':
        attendances = Attendance.objects.filter(employee=request.user)
    else:
        # For admin, show all attendances
        attendances = Attendance.objects.all()
        
        # Filter by employee if specified
        employee_id = request.GET.get('employee_id')
        if employee_id:
            attendances = attendances.filter(employee_id=employee_id)
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        attendances = attendances.filter(date__gte=start_date)
    if end_date:
        attendances = attendances.filter(date__lte=end_date)
    
    attendances = attendances.select_related('employee').order_by('-date')
    
    # Get employees for filter dropdown (admin only)
    employees = []
    if request.user.user_type == 'admin':
        employees = User.objects.filter(user_type='employee')
    
    # Calculate attendance statistics
    total_records = attendances.count()
    total_present = attendances.filter(status='present').count()
    total_absent = attendances.filter(status='absent').count()
    total_late = attendances.filter(status='late').count()
    
    # Calculate attendance rate
    attendance_rate = (total_present / total_records * 100) if total_records > 0 else 0
    
    # Calculate total hours worked
    total_hours = sum(att.hours_worked or 0 for att in attendances)
    
    # Get today's date for reference
    today = timezone.now().date()
    
    context = {
        'attendances': attendances,
        'employees': employees,
        'selected_employee': int(request.GET.get('employee_id')) if request.GET.get('employee_id') else None,
        'start_date': start_date,
        'end_date': end_date,
        'total_present': total_present,
        'total_absent': total_absent,
        'total_late': total_late,
        'total_records': total_records,
        'attendance_rate': attendance_rate,
        'total_hours': total_hours,
        'today': today,
    }
    
    return render(request, 'attendance/attendance_history.html', context)

@login_required
def dealer_employee_attendance_view(request):
    """Dealer views their employees' attendance"""
    if request.user.user_type != 'dealer':
        messages.error(request, "Access denied. Dealer access required.")
        return redirect('dashboard:index')
    
    # In a real system, dealers would have their own employees
    # For now, we'll show all employees
    attendances = Attendance.objects.filter(
        employee__user_type='employee'
    ).select_related('employee').order_by('-date')[:50]
    
    # Calculate attendance summary
    today = timezone.now().date()
    this_month = today.replace(day=1)
    
    monthly_stats = Attendance.objects.filter(
        employee__user_type='employee',
        date__gte=this_month
    ).values('status').annotate(count=Count('id'))
    
    stats_dict = {stat['status']: stat['count'] for stat in monthly_stats}
    
    context = {
        'attendances': attendances,
        'monthly_present': stats_dict.get('present', 0),
        'monthly_absent': stats_dict.get('absent', 0),
        'monthly_late': stats_dict.get('late', 0),
    }
    
    return render(request, 'attendance/dealer_employee_attendance.html', context)

@login_required
def attendance_summary_view(request):
    """Admin view of attendance summaries"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    # Get current month statistics
    today = timezone.now().date()
    this_month = today.replace(day=1)
    
    # Overall monthly stats
    monthly_stats = Attendance.objects.filter(
        date__gte=this_month
    ).values('status').annotate(count=Count('id'))
    
    stats_dict = {stat['status']: stat['count'] for stat in monthly_stats}
    
    # Top performers (most present)
    top_performers = Attendance.objects.filter(
        date__gte=this_month,
        status='present'
    ).values('employee__username').annotate(
        present_days=Count('id')
    ).order_by('-present_days')[:10]
    
    # Attendance by department (using user_type as proxy)
    department_stats = Attendance.objects.filter(
        date__gte=this_month
    ).values('employee__user_type').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent')),
        late=Count('id', filter=Q(status='late'))
    )
    
    context = {
        'monthly_present': stats_dict.get('present', 0),
        'monthly_absent': stats_dict.get('absent', 0),
        'monthly_late': stats_dict.get('late', 0),
        'top_performers': top_performers,
        'department_stats': department_stats,
        'current_month': today.strftime('%B %Y'),
    }
    
    return render(request, 'attendance/attendance_summary.html', context)

@login_required
def attendance_reports_view(request):
    """Generate attendance reports"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    # Get date range for report
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        # Default to last 30 days
        start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    # Generate report data
    attendances = Attendance.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('employee')
    
    # Group by employee
    employee_reports = attendances.values(
        'employee__username',
        'employee__user_type'
    ).annotate(
        total_days=Count('id'),
        present_days=Count('id', filter=Q(status='present')),
        absent_days=Count('id', filter=Q(status='absent')),
        late_days=Count('id', filter=Q(status='late')),
        avg_hours=Avg('hours_worked')
    ).order_by('employee__username')
    
    # Overall statistics
    total_records = attendances.count()
    present_records = attendances.filter(status='present').count()
    absent_records = attendances.filter(status='absent').count()
    late_records = attendances.filter(status='late').count()
    
    context = {
        'employee_reports': employee_reports,
        'total_records': total_records,
        'present_records': present_records,
        'absent_records': absent_records,
        'late_records': late_records,
        'attendance_rate': round((present_records / total_records * 100), 2) if total_records > 0 else 0,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'attendance/attendance_reports.html', context)
