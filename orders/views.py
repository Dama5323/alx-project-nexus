# orders/views.py
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.views import APIView
from .models import Order
from .serializers import OrderSerializer
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import OrderCreateForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.views import View
from django.template.loader import get_template
import datetime
from xhtml2pdf import pisa
from products.models import Product
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import OrderItem

 
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all orders with optional status filtering",
        manual_parameters=[
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Filter by order status",
                type=openapi.TYPE_STRING,
                enum=[choice[0] for choice in Order.Status.choices]
            ),
        ],
        responses={
            200: OrderSerializer(many=True),
            401: "Unauthorized"
        },
        tags=['Orders']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new order",
        request_body=OrderSerializer,
        responses={
            201: OrderSerializer,
            400: "Invalid data",
            401: "Unauthorized"
        },
        tags=['Orders']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update order status",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=[choice[0] for choice in Order.Status.choices],
                    description="New status for the order"
                )
            }
        ),
        responses={
            200: OrderSerializer,
            400: "Invalid status transition",
            401: "Unauthorized",
            404: "Order not found"
        },
        tags=['Order Actions']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Process order payment",
        responses={
            200: openapi.Response(
                description="Payment successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'payment_date': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            ),
            400: "Payment cannot be processed",
            401: "Unauthorized"
        },
        tags=['Order Actions']
    )
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        order = self.get_object()
        order.mark_as_paid()
        return Response({
            'status': order.status,
            'payment_date': order.payment_date
        })

    @swagger_auto_schema(
        operation_description="Cancel an order",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'reason': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Reason for cancellation"
                ),
                'restock': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Whether to restock inventory",
                    default=True
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Cancellation successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'notes': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Order cannot be cancelled",
            401: "Unauthorized"
        },
        tags=['Order Actions']
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        reason = request.data.get('reason', '')
        restock = request.data.get('restock', True)
        order.cancel(reason=reason, restock=restock)
        return Response({
            'status': order.status,
            'notes': order.notes
        })
    

class StatusTransitionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get available status transitions for an order",
        responses={
            200: openapi.Response(
                description="Available transitions",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'current_status': openapi.Schema(type=openapi.TYPE_STRING),
                        'available_transitions': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING)
                        )
                    }
                )
            ),
            404: "Order not found"
        },
        tags=['Order Metadata']
    )
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        transitions = self._get_available_transitions(order)
        return Response({
            'current_status': order.status,
            'available_transitions': transitions
        })

    def _get_available_transitions(self, order):
        """Business logic for status transitions"""
        transitions = []
        if order.status == Order.Status.PENDING:
            transitions.extend([Order.Status.PAID, Order.Status.CANCELLED])
        elif order.status == Order.Status.PAID:
            transitions.extend([Order.Status.PROCESSING, Order.Status.CANCELLED])
        # Add more transition logic as needed
        return transitions
    

class OrderListView(ListView):
    model = Order
    template_name = 'orders/list.html' 
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)
        if status := self.request.GET.get('status'):
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')
    

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        """Only allow users to see their own orders"""
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        context.update({
            'can_cancel': order.status in ['PENDING', 'PAID'],
            'can_pay': order.status == 'PENDING',
            'items': order.items.all()
        })
        return context
    
    def get_form_kwargs(self):
        """Pass the user to the form"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Add success message"""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Order #{self.object.id} created successfully!"
        )
        return response
    

class OrderTemplateCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderCreateForm
    template_name = 'orders/create.html'
    success_url = reverse_lazy('orders:list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Order created successfully!")
        return response
    

class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderCreateForm
    template_name = 'orders/create.html'
    success_url = reverse_lazy('orders:list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Order #{self.object.id} created successfully!")
        return response


class OrderPayView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs['pk'], user=request.user)
        if order.status != Order.Status.PENDING:
            messages.error(request, "Only pending orders can be paid")
            return HttpResponseRedirect(reverse_lazy('orders:detail', kwargs={'pk': order.pk}))
            
        order.mark_as_paid()
        messages.success(request, "Payment processed successfully!")
        return HttpResponseRedirect(reverse_lazy('orders:detail', kwargs={'pk': order.pk}))
    

class OrderCancelView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs['pk'], user=request.user)
        if order.status not in [Order.Status.PENDING, Order.Status.PAID]:
            messages.error(request, "This order cannot be cancelled")
            return redirect('orders:detail', pk=order.pk)
            
        order.cancel(request.POST.get('reason', ''))
        messages.success(request, "Order has been cancelled")
        return redirect('orders:detail', pk=order.pk)
    

class OrderTrackView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/tracking.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        context['tracking_info'] = {
            'status': order.get_status_display(),
            'last_updated': order.updated_at,
            'estimated_delivery': self._calculate_estimated_delivery(order)
        }
        return context

    def _calculate_estimated_delivery(self, order):
        """Calculate estimated delivery date based on order status"""
        if order.status == Order.Status.SHIPPED:
            return order.shipping_date + datetime.timedelta(days=3)
        return "Not yet available"
    

class OrderInvoicePDFView(LoginRequiredMixin, View):
    """Generate PDF invoice for an order"""
    
    def get(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs['pk'], user=request.user)
        
        # Render HTML template
        template = get_template('orders/invoice_pdf.html')
        html = template.render({'order': order})
        
        # Create PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
        
        # Generate PDF
        pisa_status = pisa.CreatePDF(
            html,
            dest=response,
            encoding='UTF-8'
        )
        
        if pisa_status.err:
            return HttpResponse('PDF generation error', status=500)
        return response
    

class AddOrderItemView(LoginRequiredMixin, View):
    """View for adding items to existing orders"""
    
    def get(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs['order_id'], user=request.user)
        products = Product.objects.filter(is_available=True)
        return render(request, 'orders/add_item.html', {
            'order': order,
            'products': products
        })

    def post(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs['order_id'], user=request.user)
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        product = get_object_or_404(Product, pk=product_id)
        
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price,
            product_name=product.name,
            product_sku=product.sku
        )
        
        # Update order total
        order.total_price = sum(item.price * item.quantity for item in order.items.all())
        order.save()
        
        messages.success(request, "Item added to order successfully!")
        return redirect('orders:detail', pk=order.id)