from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import WarehouseItem, DealerStock, StockRequest
from accounts.models import User
from django.db.models import Sum
import json

@login_required
def dealer_stock_view(request):
    """View dealer's stock inventory"""
    if request.user.user_type != 'dealer':
        messages.error(request, "Access denied. Dealer access required.")
        return redirect('dashboard:index')
    
    dealer_stocks = DealerStock.objects.filter(dealer=request.user).select_related('item')
    
    # Calculate statistics and add total_value to each stock item
    for stock in dealer_stocks:
        stock.total_value = stock.quantity * stock.selling_price
    
    total_items = dealer_stocks.count()
    total_value = sum(stock.total_value for stock in dealer_stocks)
    total_available = sum(stock.available_quantity for stock in dealer_stocks)
    
    # Low stock alerts
    low_stock_items = [stock for stock in dealer_stocks if stock.available_quantity < 5]
    
    # Recently updated items
    recent_items = dealer_stocks.order_by('-updated_at')[:5]
    
    context = {
        'dealer_stocks': dealer_stocks,
        'total_items': total_items,
        'total_value': total_value,
        'total_available': total_available,
        'low_stock_items': low_stock_items,
        'recent_items': recent_items,
    }
    
    return render(request, 'inventory/dealer_stock.html', context)

@login_required
def stock_request_view(request):
    """Request stock from admin"""
    if request.user.user_type != 'dealer':
        messages.error(request, "Access denied. Dealer access required.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            quantity = int(data.get('quantity'))
            reason = data.get('reason', '')
            
            item = get_object_or_404(WarehouseItem, id=item_id)
            
            # Check if request already exists
            existing_request = StockRequest.objects.filter(
                dealer=request.user, 
                item=item, 
                status='pending'
            ).first()
            
            if existing_request:
                existing_request.quantity_requested = quantity
                existing_request.reason = reason
                existing_request.save()
                messages.success(request, "Stock request updated successfully.")
            else:
                StockRequest.objects.create(
                    dealer=request.user,
                    item=item,
                    quantity_requested=quantity,
                    reason=reason
                )
                messages.success(request, "Stock request submitted successfully.")
                
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # GET request - show available items
    warehouse_items = WarehouseItem.objects.filter(quantity__gt=0)
    pending_requests = StockRequest.objects.filter(
        dealer=request.user, 
        status='pending'
    ).select_related('item')
    
    context = {
        'warehouse_items': warehouse_items,
        'pending_requests': pending_requests,
    }
    
    return render(request, 'inventory/stock_request.html', context)

@login_required
def admin_stock_view(request):
    """Admin view of warehouse stock"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    warehouse_items = WarehouseItem.objects.all()
    
    # Calculate total value and add total_value property to each item
    for item in warehouse_items:
        item.total_value = item.quantity * item.unit_price
    
    total_value = sum(item.total_value for item in warehouse_items)
    
    # Low stock alerts
    low_stock_items = warehouse_items.filter(quantity__lt=10)
    
    # Additional statistics
    stock_requests_count = StockRequest.objects.filter(status='pending').count()
    
    # Calculate averages and insights
    avg_item_value = total_value / warehouse_items.count() if warehouse_items.count() > 0 else 0
    highest_value_item = max([item.unit_price for item in warehouse_items]) if warehouse_items.exists() else 0
    
    # Most stocked category
    from django.db.models import Count
    category_counts = warehouse_items.values('category').annotate(count=Count('id')).order_by('-count')
    most_stocked_category = category_counts.first()['category'] if category_counts.exists() else None
    
    context = {
        'warehouse_items': warehouse_items,
        'total_items': warehouse_items.count(),
        'total_value': total_value,
        'low_stock_items': low_stock_items,
        'stock_requests_count': stock_requests_count,
        'avg_item_value': avg_item_value,
        'highest_value_item': highest_value_item,
        'most_stocked_category': most_stocked_category,
    }
    
    return render(request, 'inventory/admin_stock.html', context)

@login_required
def product_management_view(request):
    """Manage products in warehouse"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    products = WarehouseItem.objects.all()
    
    # Add total_value to each product
    for product in products:
        product.total_value = product.quantity * product.unit_price
    
    # Filter by category if specified
    category = request.GET.get('category')
    if category:
        products = products.filter(category=category)
    
    # Search functionality
    search_term = request.GET.get('search')
    if search_term:
        products = products.filter(
            models.Q(name__icontains=search_term) | 
            models.Q(sku__icontains=search_term) |
            models.Q(description__icontains=search_term)
        )
    
    # Additional statistics
    from django.db.models import Avg, Count
    avg_price = products.aggregate(Avg('unit_price'))['unit_price__avg'] or 0
    out_of_stock = products.filter(quantity=0)
    
    # Category distribution
    category_distribution = []
    for value, label in WarehouseItem.CATEGORY_CHOICES:
        count = products.filter(category=value).count()
        percentage = (count / products.count() * 100) if products.count() > 0 else 0
        category_distribution.append({
            'name': label,
            'count': count,
            'percentage': round(percentage, 1)
        })
    
    context = {
        'products': products,
        'categories': WarehouseItem.CATEGORY_CHOICES,
        'filter_category': category,
        'avg_price': avg_price,
        'out_of_stock': out_of_stock,
        'category_distribution': category_distribution,
    }
    
    return render(request, 'inventory/product_management.html', context)

@login_required
def product_create_view(request):
    """Create new product"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            category = request.POST.get('category')
            sku = request.POST.get('sku')
            quantity = int(request.POST.get('quantity', 0))
            unit_price = float(request.POST.get('unit_price', 0))
            description = request.POST.get('description', '')
            
            # Check if SKU already exists
            if WarehouseItem.objects.filter(sku=sku).exists():
                messages.error(request, "SKU already exists.")
                return redirect('inventory:product_create')
            
            WarehouseItem.objects.create(
                name=name,
                category=category,
                sku=sku,
                quantity=quantity,
                unit_price=unit_price,
                description=description,
                updated_by=request.user
            )
            
            messages.success(request, "Product created successfully.")
            return redirect('inventory:product_management')
        except Exception as e:
            messages.error(request, f"Error creating product: {str(e)}")
    
    context = {
        'categories': WarehouseItem.CATEGORY_CHOICES,
    }
    
    return render(request, 'inventory/product_form.html', context)

@login_required
def product_edit_view(request, product_id):
    """Edit existing product"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    product = get_object_or_404(WarehouseItem, id=product_id)
    
    if request.method == 'POST':
        try:
            product.name = request.POST.get('name')
            product.category = request.POST.get('category')
            product.sku = request.POST.get('sku')
            product.quantity = int(request.POST.get('quantity', 0))
            product.unit_price = float(request.POST.get('unit_price', 0))
            product.description = request.POST.get('description', '')
            product.updated_by = request.user
            product.save()
            
            messages.success(request, "Product updated successfully.")
            return redirect('inventory:product_management')
        except Exception as e:
            messages.error(request, f"Error updating product: {str(e)}")
    
    context = {
        'product': product,
        'categories': WarehouseItem.CATEGORY_CHOICES,
    }
    
    return render(request, 'inventory/product_form.html', context)

@login_required
def stock_requests_view(request):
    """Admin view of stock requests"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    requests = StockRequest.objects.select_related('dealer', 'item').order_by('-created_at')
    
    # Filter by status if specified
    status = request.GET.get('status')
    if status and status in ['pending', 'approved', 'rejected']:
        requests = requests.filter(status=status)
    
    context = {
        'requests': requests,
        'filter_status': status,
    }
    
    return render(request, 'inventory/stock_requests.html', context)

@login_required
def approve_stock_request_view(request, request_id):
    """Approve/reject stock request"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    stock_request = get_object_or_404(StockRequest, id=request_id)
    
    if request.method == 'POST':
        try:
            action = request.POST.get('action')  # 'approve' or 'reject'
            quantity_approved = request.POST.get('quantity_approved')
            comments = request.POST.get('comments', '')
            
            if action == 'approve':
                if quantity_approved:
                    approved_qty = int(quantity_approved)
                    stock_request.quantity_approved = approved_qty
                    stock_request.status = 'partially_approved' if approved_qty < stock_request.quantity_requested else 'approved'
                else:
                    stock_request.quantity_approved = stock_request.quantity_requested
                    stock_request.status = 'approved'
                
                # Update warehouse stock
                stock_request.item.quantity -= stock_request.quantity_approved
                stock_request.item.save()
                
                # Update or create dealer stock
                dealer_stock, created = DealerStock.objects.get_or_create(
                    dealer=stock_request.dealer,
                    item=stock_request.item,
                    defaults={
                        'quantity': stock_request.quantity_approved,
                        'selling_price': stock_request.item.unit_price * 1.2  # 20% markup
                    }
                )
                
                if not created:
                    dealer_stock.quantity += stock_request.quantity_approved
                    dealer_stock.save()
                
            else:  # reject
                stock_request.status = 'rejected'
            
            stock_request.approved_by = request.user
            stock_request.save()
            
            messages.success(request, f"Stock request {action}d successfully.")
            return redirect('inventory:stock_requests')
        except Exception as e:
            messages.error(request, f"Error processing request: {str(e)}")
    
    context = {
        'stock_request': stock_request,
    }
    
    return render(request, 'inventory/approve_request.html', context)
