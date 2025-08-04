from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from xhtml2pdf import pisa
import datetime

from .models import Order, OrderItem
from .serializers import OrderSerializer
from cart.models import Cart
from products.models import Product

# ======================
# Traditional Django Views
# ======================

class OrderListView(LoginRequiredMixin, ListView):
    """View for listing user's orders with filtering"""
    model = Order
    template_name = 'orders/list.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user).order_by('-created_at')
        if status := self.request.GET.get('status'):
            queryset = queryset.filter(status=status)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        return context

class OrderCreateView(LoginRequiredMixin, CreateView):
    """View for creating new orders from cart"""
    model = Order
    fields = ['shipping_address', 'billing_address', 'payment_method']
    template_name = 'orders/create.html'
    success_url = reverse_lazy('orders:list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if hasattr(self.request.user, 'profile'):
            profile = self.request.user.profile
            form.fields['shipping_address'].initial = profile.shipping_address
            form.fields['billing_address'].initial = profile.billing_address
        return form
    
    def form_valid(self, form):
        cart = get_object_or_404(Cart, user=self.request.user)
        if not cart.items.exists():
            form.add_error(None, "Your cart is empty")
            return self.form_invalid(form)
        
        order = form.save(commit=False)
        order.user = self.request.user
        order.total_price = sum(item.product.price * item.quantity for item in cart.items.all())
        order.save()
        
        for item in cart.items.all():
            order.items.create(
                product=item.product,
                price=item.product.price,
                quantity=item.quantity,
                product_name=item.product.name,
                product_sku=getattr(item.product, 'sku', '')
            )
        
        cart.items.all().delete()
        messages.success(self.request, "Order created successfully!")
        return super().form_valid(form)

class OrderDetailView(LoginRequiredMixin, DetailView):
    """View for order details with action controls"""
    model = Order
    template_name = 'orders/detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        context.update({
            'can_cancel': order.status in ['PENDING', 'PAID'],
            'can_pay': order.status == 'PENDING',
            'items': order.items.all()  # Include order items in context
        })
        return context

class AddOrderItemView(LoginRequiredMixin, View):
    """View for adding items to existing orders"""
    template_name = 'orders/add_item.html'
    
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        products = Product.objects.all()
        return render(request, self.template_name, {
            'order': order,
            'products': products
        })
    
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id)
        
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price,
            product_name=product.name,
            product_sku=getattr(product, 'sku', '')
        )
        
        # Update order total
        order.total_price = sum(item.price * item.quantity for item in order.items.all())
        order.save()
        
        messages.success(request, "Item added to order successfully!")
        return redirect('orders:detail', pk=order.id)

class OrderPayView(LoginRequiredMixin, View):
    """View for processing order payment"""
    def post(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs['pk'], user=request.user)
        if order.status != 'PENDING':
            messages.error(request, "Only pending orders can be paid")
            return redirect('orders:detail', pk=order.pk)
            
        order.mark_as_paid()
        messages.success(request, "Payment processed successfully!")
        return redirect('orders:detail', pk=order.pk)

class OrderCancelView(LoginRequiredMixin, View):
    """View for cancelling orders"""
    def post(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs['pk'], user=request.user)
        if order.status not in ['PENDING', 'PAID']:
            messages.error(request, "This order cannot be cancelled")
            return redirect('orders:detail', pk=order.pk)
            
        order.cancel(request.POST.get('reason', ''))
        messages.success(request, "Order has been cancelled")
        return redirect('orders:detail', pk=order.pk)

class OrderTrackView(LoginRequiredMixin, DetailView):
    """View for order tracking information"""
    model = Order
    template_name = 'orders/tracking.html'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tracking_info'] = {
            'status': self.object.status,
            'estimated_delivery': (datetime.date.today() + datetime.timedelta(days=3)).strftime("%B %d, %Y")
        }
        return context

class OrderInvoicePDFView(LoginRequiredMixin, View):
    """View for generating PDF invoices"""
    def get(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs['pk'], user=request.user)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'filename=invoice_{order.pk}.pdf'
        
        html = get_template('orders/invoice_pdf.html').render({'order': order})
        if pisa.CreatePDF(html, dest=response).err:
            return HttpResponse('Error generating PDF', status=500)
        return response

# ======================
# DRF API Views
# ======================

class OrderViewSet(viewsets.ModelViewSet):
    """API endpoint for order operations"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)
        if status := self.request.query_params.get('status'):
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            return Response(
                {'error': 'Cart is empty'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order = serializer.save(user=request.user)
        order.total_price = sum(item.product.price * item.quantity for item in cart.items.all())
        order.save()
        
        for item in cart.items.all():
            order.items.create(
                product=item.product,
                price=item.product.price,
                quantity=item.quantity,
                product_name=item.product.name,
                product_sku=getattr(item.product, 'sku', '')
            )
        
        cart.items.all().delete()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        order = self.get_object()
        if order.status != 'PENDING':
            return Response(
                {'error': 'Only pending orders can be paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.mark_as_paid()
        return Response({'status': 'paid'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status not in ['PENDING', 'PAID']:
            return Response(
                {'error': 'Order cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.cancel(request.data.get('reason', ''))
        return Response({'status': 'cancelled'})