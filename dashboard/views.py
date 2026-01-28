from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import User
from inventory.models import WarehouseItem

@login_required
def index(request):
    context = {
        'is_admin': request.user.user_type == 'admin' if hasattr(request.user, 'user_type') else False,
        'is_dealer': request.user.user_type == 'dealer' if hasattr(request.user, 'user_type') else False,
        'is_service': request.user.user_type == 'service' if hasattr(request.user, 'user_type') else False,
        'is_employee': request.user.user_type == 'employee' if hasattr(request.user, 'user_type') else False,
        'is_customer': request.user.user_type == 'customer' if hasattr(request.user, 'user_type') else False,
    }
    
    # Add admin statistics
    if context['is_admin']:
        context['dealer_count'] = User.objects.filter(user_type='dealer').count()
        context['employee_count'] = User.objects.filter(user_type='employee').count()
        context['total_users'] = User.objects.count()
        context['warehouse_count'] = WarehouseItem.objects.count()
    
    return render(request, "dashboard/index.html", context)
