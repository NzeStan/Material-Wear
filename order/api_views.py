# order/api_views.py
from rest_framework import views, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import BaseOrder, NyscKitOrder, NyscTourOrder, ChurchOrder, OrderItem
from .serializers import (
    BaseOrderSerializer, NyscKitOrderSerializer, NyscTourOrderSerializer,
    ChurchOrderSerializer, CheckoutSerializer, OrderListSerializer, OrderItemSerializer
)
from cart.cart import Cart
from jmw.background_utils import send_order_confirmation_email_async, generate_order_confirmation_pdf_task
import logging

logger = logging.getLogger(__name__)


@extend_schema(tags=['Order'])
class CheckoutView(views.APIView):
    """
    Checkout endpoint - converts cart to orders
    Creates separate orders for each product type in cart
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description="Create orders from cart items. Returns list of created order IDs.",
        request=CheckoutSerializer,
        responses={
            201: {'description': 'Orders created successfully'},
            400: {'description': 'Validation error or empty cart'}
        }
    )
    def post(self, request):
        cart = Cart(request)
        
        # Validate cart is not empty
        if not cart or len(cart) == 0:
            return Response({
                'error': 'Cart is empty'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate request data with cart context
        serializer = CheckoutSerializer(
            data=request.data,
            context={'cart': cart, 'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        
        try:
            with transaction.atomic():
                # Group cart items by product type
                grouped_items = {}
                for item in cart:
                    product_type = item['product'].__class__.__name__
                    if product_type not in grouped_items:
                        grouped_items[product_type] = []
                    grouped_items[product_type].append(item)
                
                # Order type mapping
                order_type_map = {
                    'NyscKit': NyscKitOrder,
                    'NyscTour': NyscTourOrder,
                    'Church': ChurchOrder,
                }
                
                orders_created = []
                
                # Create separate order for each product type
                for product_type, items in grouped_items.items():
                    order_model = order_type_map.get(product_type)
                    if not order_model:
                        continue
                    
                    # Base order data
                    order_data = {
                        'user': request.user,
                        'email': request.user.email,
                        'first_name': validated_data['first_name'],
                        'middle_name': validated_data.get('middle_name', ''),
                        'last_name': validated_data['last_name'],
                        'phone_number': validated_data['phone_number'],
                        'paid': False,  # ✅ EXPLICITLY SET TO FALSE
                    }
                    
                    # Add product-specific fields
                    if product_type == 'NyscKit':
                        order_data.update({
                            'call_up_number': validated_data['call_up_number'],
                            'state': validated_data['state'],
                            'local_government': validated_data['local_government'],
                        })
                    elif product_type == 'Church':
                        order_data.update({
                            'pickup_on_camp': validated_data.get('pickup_on_camp', True),
                            'delivery_state': validated_data.get('delivery_state', ''),
                            'delivery_lga': validated_data.get('delivery_lga', ''),
                        })
                    
                    # Create order
                    order = order_model.objects.create(**order_data)
                    
                    # Create order items
                    for item in items:
                        OrderItem.objects.create(
                            order=order,
                            content_type=ContentType.objects.get_for_model(item['product']),
                            object_id=item['product'].id,
                            price=item['price'],
                            quantity=item['quantity'],
                            extra_fields=item.get('extra_fields', {}),
                        )
                    
                    # Update order total cost
                    order.total_cost = sum(
                        order_item.get_cost() for order_item in order.items.all()
                    )
                    order.save(update_fields=['total_cost'])
                    
                    orders_created.append(order)
                    
                    logger.info(
                        f"Order created: {order.serial_number} - "
                        f"Type: {product_type} - User: {request.user.email}"
                    )
                
                # Store order IDs in session for payment
                request.session['pending_orders'] = [str(order.id) for order in orders_created]
                
                # Clear cart
                cart.clear()
                
                # Send order confirmation emails asynchronously
                # ✅ PASS THE ACTUAL ORDER TYPE, NOT STRING ID
                for order in orders_created:
                    send_order_confirmation_email_async(str(order.id), order.__class__.__name__)
                    generate_order_confirmation_pdf_task(str(order.id), order.__class__.__name__)
                
                # Return created orders
                order_ids = [str(order.id) for order in orders_created]
                total_amount = sum(order.total_cost for order in orders_created)
                
                return Response({
                    'message': f'{len(orders_created)} order(s) created successfully',
                    'order_ids': order_ids,
                    'total_amount': float(total_amount),
                    'orders': [
                        {
                            'id': str(order.id),
                            'serial_number': order.serial_number,
                            'type': order.__class__.__name__,
                            'total_cost': float(order.total_cost),
                            'paid': order.paid  # ✅ INCLUDE PAID STATUS
                        }
                        for order in orders_created
                    ]
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.exception("Error during checkout")
            return Response({
                'error': 'An error occurred while processing your order. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    list=extend_schema(description="List all orders for authenticated user"),
    retrieve=extend_schema(description="Get specific order details"),
)
@extend_schema(tags=['Order'])
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing orders
    Users can only view their own orders
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        ✅ FIXED: Get orders for authenticated user with polymorphic type selection
        Uses select_related to fetch the specific order type (Church/NyscKit/NyscTour)
        """
        base_queryset = BaseOrder.objects.filter(
            user=self.request.user
        ).prefetch_related(
            'items',
            'items__content_type'
        ).select_related(
            'churchorder',  # ✅ Fetch ChurchOrder relationship
            'nysckitorder',  # ✅ Fetch NyscKitOrder relationship
            'nysctourorder'  # ✅ Fetch NyscTourOrder relationship
        ).order_by('-created')
        
        return base_queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on order type"""
        if self.action == 'list':
            return OrderListSerializer
        
        # For retrieve, determine the specific order type
        if hasattr(self, 'get_object'):
            try:
                obj = self.get_object()
                # ✅ FIXED: Get actual polymorphic type
                actual_type = self._get_actual_order_type(obj)
                
                if actual_type == 'NyscKitOrder':
                    return NyscKitOrderSerializer
                elif actual_type == 'NyscTourOrder':
                    return NyscTourOrderSerializer
                elif actual_type == 'ChurchOrder':
                    return ChurchOrderSerializer
            except:
                pass
        
        return BaseOrderSerializer
    
    def _get_actual_order_type(self, order):
        """
        ✅ NEW: Helper method to determine the actual polymorphic order type
        """
        # Check if this is a specific order type
        if hasattr(order, 'churchorder'):
            return 'ChurchOrder'
        elif hasattr(order, 'nysckitorder'):
            return 'NyscKitOrder'
        elif hasattr(order, 'nysctourorder'):
            return 'NyscTourOrder'
        return 'BaseOrder'
    
    def _get_actual_order_instance(self, order):
        """
        ✅ NEW: Helper method to get the actual polymorphic instance
        """
        # Return the specific order instance
        if hasattr(order, 'churchorder'):
            return order.churchorder
        elif hasattr(order, 'nysckitorder'):
            return order.nysckitorder
        elif hasattr(order, 'nysctourorder'):
            return order.nysctourorder
        return order
    
    def list(self, request, *args, **kwargs):
        """
        ✅ FIXED: List orders with correct polymorphic types
        """
        queryset = self.get_queryset()
        
        # Build lightweight response with correct order types
        orders_data = []
        for order in queryset:
            # Get the actual polymorphic order type
            order_type = self._get_actual_order_type(order)
            actual_order = self._get_actual_order_instance(order)
            
            orders_data.append({
                'id': str(order.id),
                'serial_number': order.serial_number,
                'order_type': order_type,  # ✅ NOW SHOWS CORRECT TYPE
                'total_cost': float(order.total_cost),
                'paid': order.paid,  # ✅ SHOWS ACTUAL PAID STATUS
                'created': order.created,
                'item_count': order.items.count()
            })
        
        serializer = OrderListSerializer(orders_data, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """
        ✅ FIXED: Retrieve specific order with correct type
        """
        instance = self.get_object()
        
        # Get the actual polymorphic instance
        actual_instance = self._get_actual_order_instance(instance)
        
        # Get the correct serializer for this order type
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(actual_instance, context={'request': request})
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def receipt(self, request, pk=None):
        """Get order receipt/confirmation"""
        order = self.get_object()
        actual_order = self._get_actual_order_instance(order)
        
        # Get correct serializer
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(actual_order, context={'request': request})
        
        return Response({
            'order': serializer.data,
            'receipt_available': True,
            'paid': order.paid
        })