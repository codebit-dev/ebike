from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Sale, SaleItem, Invoice, DealerPayout
from inventory.models import DealerStock, WarehouseItem
from accounts.models import User
import json
import uuid

@login_required
def dealer_sales_view(request):
    """View dealer's sales history"""
    if request.user.user_type != 'dealer':
        messages.error(request, "Access denied. Dealer access required.")
        return redirect('dashboard:index')
    
    sales = Sale.objects.filter(dealer=request.user).prefetch_related('items__item')
    
    # Filter by status if specified
    status = request.GET.get('status')
    if status and status in ['draft', 'completed', 'cancelled']:
        sales = sales.filter(status=status)
    
    # Calculate totals
    total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    total_transactions = sales.count()
    
    context = {
        'sales': sales,
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'filter_status': status,
    }
    
    return render(request, 'sales/dealer_sales.html', context)

@login_required
def create_sale_view(request):
    """Create a new sale"""
    if request.user.user_type != 'dealer':
        messages.error(request, "Access denied. Dealer access required.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_name = data.get('customer_name')
            customer_phone = data.get('customer_phone')
            customer_email = data.get('customer_email', '')
            items = data.get('items', [])
            
            if not items:
                return JsonResponse({'success': False, 'error': 'No items selected'})
            
            # Create sale
            sale = Sale.objects.create(
                dealer=request.user,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                created_by=request.user
            )
            
            total_amount = 0
            
            # Add items to sale
            for item_data in items:
                item_id = item_data.get('item_id')
                quantity = int(item_data.get('quantity'))
                unit_price = float(item_data.get('unit_price'))
                
                dealer_stock = get_object_or_404(DealerStock, 
                    dealer=request.user, 
                    item_id=item_id,
                    quantity__gte=quantity
                )
                
                # Check if enough stock available
                if dealer_stock.available_quantity < quantity:
                    sale.delete()  # Clean up
                    return JsonResponse({
                        'success': False, 
                        'error': f'Insufficient stock for {dealer_stock.item.name}'
                    })
                
                # Create sale item
                SaleItem.objects.create(
                    sale=sale,
                    item=dealer_stock.item,
                    dealer_stock=dealer_stock,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=quantity * unit_price
                )
                
                total_amount += quantity * unit_price
                
                # Update allocated quantity
                dealer_stock.allocated_quantity += quantity
                dealer_stock.save()
            
            sale.total_amount = total_amount
            sale.status = 'completed'
            sale.save()
            
            return JsonResponse({
                'success': True, 
                'sale_id': sale.id,
                'message': 'Sale created successfully'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # GET request - show available stock
    available_stock = DealerStock.objects.filter(
        dealer=request.user,
        quantity__gt=0
    ).select_related('item')
    
    context = {
        'available_stock': available_stock,
    }
    
    return render(request, 'sales/create_sale.html', context)

@login_required
def sale_detail_view(request, sale_id):
    """View sale details"""
    sale = get_object_or_404(Sale, id=sale_id)
    
    # Check access rights
    if request.user.user_type == 'dealer' and sale.dealer != request.user:
        messages.error(request, "Access denied. You can only view your own sales.")
        return redirect('sales:dealer_sales')
    
    if request.user.user_type not in ['admin', 'dealer']:
        messages.error(request, "Access denied.")
        return redirect('dashboard:index')
    
    context = {
        'sale': sale,
        'items': sale.items.select_related('item'),
    }
    
    return render(request, 'sales/sale_detail.html', context)

@login_required
def generate_invoice_view(request, sale_id):
    """Generate invoice for a sale"""
    sale = get_object_or_404(Sale, id=sale_id)
    
    # Check access rights
    if request.user.user_type == 'dealer' and sale.dealer != request.user:
        messages.error(request, "Access denied. You can only generate invoices for your own sales.")
        return redirect('sales:dealer_sales')
    
    if request.user.user_type not in ['admin', 'dealer']:
        messages.error(request, "Access denied.")
        return redirect('dashboard:index')
    
    # Check if invoice already exists
    if hasattr(sale, 'invoice'):
        messages.info(request, "Invoice already generated for this sale.")
        return redirect('sales:sale_detail', sale_id=sale_id)
    
    if request.method == 'POST':
        try:
            tax_percentage = float(request.POST.get('tax_percentage', 0))
            discount_amount = float(request.POST.get('discount_amount', 0))
            
            # Calculate amounts
            subtotal = sale.total_amount
            tax_amount = (subtotal * tax_percentage) / 100
            grand_total = subtotal + tax_amount - discount_amount
            
            # Generate unique invoice number
            invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Create invoice
            invoice = Invoice.objects.create(
                sale=sale,
                invoice_number=invoice_number,
                due_date=timezone.now() + timedelta(days=30),
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                grand_total=grand_total
            )
            
            messages.success(request, f"Invoice {invoice_number} generated successfully.")
            return redirect('sales:sale_detail', sale_id=sale_id)
            
        except Exception as e:
            messages.error(request, f"Error generating invoice: {str(e)}")
    
    context = {
        'sale': sale,
    }
    
    return render(request, 'sales/generate_invoice.html', context)

@login_required
def dealer_sales_report_view(request):
    """Dealer view of their sales reports"""
    if request.user.user_type != 'dealer':
        messages.error(request, "Access denied. Dealer access required.")
        return redirect('dashboard:index')
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    sales = Sale.objects.filter(
        dealer=request.user,
        created_at__date__range=[start_date, end_date],
        status='completed'
    )
    
    total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    total_transactions = sales.count()
    
    # Top selling items
    top_items = SaleItem.objects.filter(
        sale__dealer=request.user,
        sale__created_at__date__range=[start_date, end_date]
    ).values('item__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_revenue')[:10]
    
    context = {
        'sales': sales,
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'top_items': top_items,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'sales/dealer_sales_report.html', context)

@login_required
def admin_sales_report_view(request):
    """Admin view of all sales reports"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    dealer_id = request.GET.get('dealer_id')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    sales = Sale.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='completed'
    ).select_related('dealer')
    
    # Filter by dealer if specified
    if dealer_id:
        sales = sales.filter(dealer_id=dealer_id)
    
    total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    total_transactions = sales.count()
    
    # Top dealers
    top_dealers = Sale.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='completed'
    ).values('dealer__username').annotate(
        total_sales=Sum('total_amount'),
        transaction_count=Count('id')
    ).order_by('-total_sales')[:10]
    
    # All dealers for filter dropdown
    dealers = User.objects.filter(user_type='dealer')
    
    context = {
        'sales': sales,
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'top_dealers': top_dealers,
        'dealers': dealers,
        'selected_dealer': int(dealer_id) if dealer_id else None,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'sales/admin_sales_report.html', context)

@login_required
def dealer_payouts_view(request):
    """Dealer view of their payouts"""
    if request.user.user_type != 'dealer':
        messages.error(request, "Access denied. Dealer access required.")
        return redirect('dashboard:index')
    
    payouts = DealerPayout.objects.filter(dealer=request.user).order_by('-period_end')
    
    context = {
        'payouts': payouts,
    }
    
    return render(request, 'sales/dealer_payouts.html', context)

@login_required
def admin_payouts_view(request):
    """Admin view of all dealer payouts"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    payouts = DealerPayout.objects.select_related('dealer').order_by('-period_end')
    
    # Filter by dealer if specified
    dealer_id = request.GET.get('dealer_id')
    if dealer_id:
        payouts = payouts.filter(dealer_id=dealer_id)
    
    total_commission = payouts.aggregate(total=Sum('commission_amount'))['total'] or 0
    total_payout = payouts.aggregate(total=Sum('payout_amount'))['total'] or 0
    
    dealers = User.objects.filter(user_type='dealer')
    
    context = {
        'payouts': payouts,
        'dealers': dealers,
        'selected_dealer': int(dealer_id) if dealer_id else None,
        'total_commission': total_commission,
        'total_payout': total_payout,
    }
    
    return render(request, 'sales/admin_payouts.html', context)

@login_required
def calculate_payouts_view(request):
    """Calculate dealer payouts for a period"""
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. Admin access required.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        try:
            period_start = datetime.strptime(request.POST.get('period_start'), '%Y-%m-%d').date()
            period_end = datetime.strptime(request.POST.get('period_end'), '%Y-%m-%d').date()
            commission_rate = float(request.POST.get('commission_rate', 5.0))
            
            # Get all dealers
            dealers = User.objects.filter(user_type='dealer')
            
            for dealer in dealers:
                # Calculate total sales for this dealer in the period
                total_sales = Sale.objects.filter(
                    dealer=dealer,
                    created_at__date__range=[period_start, period_end],
                    status='completed'
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                if total_sales > 0:
                    # Create or update payout record
                    payout, created = DealerPayout.objects.get_or_create(
                        dealer=dealer,
                        period_start=period_start,
                        period_end=period_end,
                        defaults={
                            'total_sales': total_sales,
                            'commission_rate': commission_rate,
                        }
                    )
                    
                    if not created:
                        payout.total_sales = total_sales
                        payout.commission_rate = commission_rate
                    
                    payout.calculate_payout()
            
            messages.success(request, "Payouts calculated successfully.")
            return redirect('sales:admin_payouts')
            
        except Exception as e:
            messages.error(request, f"Error calculating payouts: {str(e)}")
    
    context = {
        'default_start': (timezone.now().replace(day=1) - timedelta(days=1)).replace(day=1),
        'default_end': timezone.now().replace(day=1) - timedelta(days=1),
    }
    
    return render(request, 'sales/calculate_payouts.html', context)

# === CUSTOMER PURCHASING VIEWS ===

@login_required
def customer_browse_products(request):
    """Customer can browse available products"""
    if request.user.user_type != 'customer':
        messages.error(request, "Access denied. Customer access required.")
        return redirect('dashboard:index')
    
    # Get products available from warehouse
    products = WarehouseItem.objects.filter(quantity__gt=0)
    
    # Filter by category if specified
    category = request.GET.get('category')
    if category:
        products = products.filter(category=category)
    
    # Search functionality
    search_term = request.GET.get('search')
    if search_term:
        products = products.filter(
            models.Q(name__icontains=search_term) | 
            models.Q(description__icontains=search_term)
        )
    
    # Get categories for filter
    categories = WarehouseItem.CATEGORY_CHOICES
    
    context = {
        'products': products,
        'categories': categories,
        'filter_category': category,
        'search_term': search_term,
    }
    
    return render(request, 'sales/customer_browse.html', context)

@login_required
def customer_add_to_cart(request):
    """Add product to customer's cart"""
    if request.user.user_type != 'customer':
        return JsonResponse({'error': 'Customer access required'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            
            product = get_object_or_404(WarehouseItem, id=product_id)
            
            # Check if product has stock
            if product.quantity < quantity:
                return JsonResponse({'error': 'Insufficient stock available'}, status=400)
            
            # Get or create cart in session
            if 'cart' not in request.session:
                request.session['cart'] = {}
            
            cart = request.session['cart']
            
            # Add to cart
            product_key = str(product_id)
            if product_key in cart:
                cart[product_key]['quantity'] += quantity
            else:
                cart[product_key] = {
                    'product_id': product_id,
                    'name': product.name,
                    'price': float(product.unit_price),
                    'quantity': quantity,
                    'image': ''  # Add image field if available
                }
            
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to cart',
                'cart_count': sum(item['quantity'] for item in cart.values())
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def customer_view_cart(request):
    """View customer's shopping cart"""
    if request.user.user_type != 'customer':
        messages.error(request, "Access denied. Customer access required.")
        return redirect('dashboard:index')
    
    cart = request.session.get('cart', {})
    cart_items = []
    total_amount = 0
    
    for item_data in cart.values():
        try:
            product = WarehouseItem.objects.get(id=item_data['product_id'])
            item_total = item_data['quantity'] * item_data['price']
            total_amount += item_total
            
            cart_items.append({
                'product': product,
                'quantity': item_data['quantity'],
                'price': item_data['price'],
                'total': item_total
            })
        except WarehouseItem.DoesNotExist:
            # Remove invalid items from cart
            del cart[str(item_data['product_id'])]
            request.session.modified = True
    
    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'cart_count': len(cart_items)
    }
    
    return render(request, 'sales/customer_cart.html', context)

@login_required
def customer_remove_from_cart(request, product_id):
    """Remove item from cart"""
    if request.user.user_type != 'customer':
        messages.error(request, "Access denied. Customer access required.")
        return redirect('dashboard:index')
    
    cart = request.session.get('cart', {})
    product_key = str(product_id)
    
    if product_key in cart:
        del cart[product_key]
        request.session.modified = True
        messages.success(request, "Item removed from cart")
    else:
        messages.error(request, "Item not found in cart")
    
    return redirect('sales:customer_cart')

@login_required
def customer_checkout(request):
    """Customer checkout process with COD payment"""
    if request.user.user_type != 'customer':
        messages.error(request, "Access denied. Customer access required.")
        return redirect('dashboard:index')
    
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.error(request, "Your cart is empty")
        return redirect('sales:customer_browse')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                shipping_address = request.POST.get('shipping_address', '').strip()
                phone_number = request.POST.get('phone_number', '').strip()
                notes = request.POST.get('notes', '').strip()
                
                if not all([shipping_address, phone_number]):
                    messages.error(request, "Please fill in all required fields")
                    return render(request, 'sales/customer_checkout.html', {
                        'cart_items': [],
                        'total_amount': 0,
                        'customer': request.user
                    })
                
                # Validate phone number
                if len(phone_number) < 10:
                    messages.error(request, "Please enter a valid phone number")
                    return render(request, 'sales/customer_checkout.html', {
                        'cart_items': [],
                        'total_amount': 0,
                        'customer': request.user
                    })
                
                # Calculate total amount
                total_amount = 0
                cart_items = []
                
                for item_data in cart.values():
                    try:
                        product = WarehouseItem.objects.get(id=item_data['product_id'])
                        # Check if product still exists and has stock
                        if product.quantity < item_data['quantity']:
                            messages.error(request, f"Insufficient stock for {product.name}")
                            return render(request, 'sales/customer_checkout.html', {
                                'cart_items': [],
                                'total_amount': 0,
                                'customer': request.user
                            })
                        
                        item_total = item_data['quantity'] * item_data['price']
                        total_amount += item_total
                        
                        cart_items.append({
                            'product': product,
                            'quantity': item_data['quantity'],
                            'price': item_data['price'],
                            'total': item_total
                        })
                    except WarehouseItem.DoesNotExist:
                        messages.error(request, "One or more products are no longer available")
                        return render(request, 'sales/customer_checkout.html', {
                            'cart_items': [],
                            'total_amount': 0,
                            'customer': request.user
                        })
                
                if total_amount <= 0:
                    messages.error(request, "Cart total must be greater than zero")
                    return render(request, 'sales/customer_checkout.html', {
                        'cart_items': [],
                        'total_amount': 0,
                        'customer': request.user
                    })
                
                # Create customer order
                # Assign a dealer to the order (for demo, assign the first dealer or create temp assignment)
                dealer = User.objects.filter(user_type='dealer').first()
                if not dealer:
                    # If no dealer exists, create a temporary assignment
                    # In production, you'd have proper dealer assignment logic
                    dealer = request.user  # Temporarily assign to current user for demo
                
                order = CustomerOrder.objects.create(
                    customer=request.user,
                    dealer=dealer,  # Assign dealer to order
                    order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                    status='pending',
                    payment_status='cod',
                    total_amount=total_amount,
                    shipping_address=shipping_address,
                    phone_number=phone_number,
                    notes=notes
                )
                
                # Create order items
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        quantity=item['quantity'],
                        unit_price=item['price'],
                        total_price=item['total']
                    )
                
                # Clear cart
                del request.session['cart']
                request.session.modified = True
                
                messages.success(request, f"Order placed successfully! Order Number: {order.order_number}")
                return redirect('sales:customer_order_detail', order_id=order.id)
                
        except Exception as e:
            messages.error(request, f"Error placing order: {str(e)}")
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Checkout error: {str(e)}", exc_info=True)
            return render(request, 'sales/customer_checkout.html', {
                'cart_items': [],
                'total_amount': 0,
                'customer': request.user
            })
    
    # GET request - show checkout form
    cart_items = []
    total_amount = 0
    
    for item_data in cart.values():
        try:
            product = WarehouseItem.objects.get(id=item_data['product_id'])
            item_total = item_data['quantity'] * item_data['price']
            total_amount += item_total
            
            cart_items.append({
                'product': product,
                'quantity': item_data['quantity'],
                'price': item_data['price'],
                'total': item_total
            })
        except WarehouseItem.DoesNotExist:
            # Remove invalid items from cart
            del cart[str(item_data['product_id'])]
            request.session.modified = True
    
    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'customer': request.user
    }
    
    return render(request, 'sales/customer_checkout.html', context)

@login_required
def customer_order_detail(request, order_id):
    """View order details"""
    if request.user.user_type != 'customer':
        messages.error(request, "Access denied. Customer access required.")
        return redirect('dashboard:index')
    
    order = get_object_or_404(CustomerOrder, id=order_id, customer=request.user)
    
    context = {
        'order': order,
        'order_items': order.order_items.all()
    }
    
    return render(request, 'sales/customer_order_detail.html', context)

@login_required
def customer_order_history(request):
    """View customer's order history"""
    if request.user.user_type != 'customer':
        messages.error(request, "Access denied. Customer access required.")
        return redirect('dashboard:index')
    
    orders = CustomerOrder.objects.filter(customer=request.user).order_by('-created_at')
    
    context = {
        'orders': orders
    }
    
    return render(request, 'sales/customer_order_history.html', context)

# Dealer views for order approval
@login_required
def dealer_order_list(request):
    """Dealer views orders assigned to them"""
    if request.user.user_type != 'dealer':
        messages.error(request, "Access denied. Dealer access required.")
        return redirect('dashboard:index')
    
    # For demo purposes, show all orders to all dealers
    # In production, you'd filter by assigned dealer or region
    orders = CustomerOrder.objects.all().order_by('-created_at')
    
    # Filter by status if specified
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    context = {
        'orders': orders,
        'status_filter': status
    }
    
    return render(request, 'sales/dealer_order_list.html', context)

@login_required
def dealer_approve_order(request, order_id):
    """Dealer approves customer order"""
    if request.user.user_type != 'dealer':
        messages.error(request, "Access denied. Dealer access required.")
        return redirect('dashboard:index')
    
    # For demo purposes, allow any dealer to approve any order
    # In production, you'd check if this dealer is assigned to the order
    order = get_object_or_404(CustomerOrder, id=order_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update order status
                order.status = 'approved'
                order.approved_at = timezone.now()
                # Assign the approving dealer
                order.dealer = request.user
                order.save()
                
                # Create receipt
                Receipt.objects.create(
                    order=order,
                    amount_paid=order.total_amount,
                    payment_method='cod',
                    issued_by=request.user
                )
                
                # Reduce stock from warehouse (in real system, would reduce from dealer stock)
                for order_item in order.order_items.all():
                    order_item.product.quantity -= order_item.quantity
                    order_item.product.save()
                
                messages.success(request, f"Order {order.order_number} approved successfully!")
                return redirect('sales:dealer_order_list')
                
        except Exception as e:
            messages.error(request, f"Error approving order: {str(e)}")
    
    context = {
        'order': order
    }
    
    return render(request, 'sales/dealer_approve_order.html', context)
