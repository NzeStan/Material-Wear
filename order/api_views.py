# order/api_views.py
from rest_framework import views, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import BaseOrder, NyscKitOrder, NyscTourOrder, ChurchOrder, OrderItem
from .serializers import (
    BaseOrderSerializer,
    NyscKitOrderSerializer,
    NyscTourOrderSerializer,
    ChurchOrderSerializer,
    CheckoutSerializer,
    OrderListSerializer,
    OrderItemSerializer,
)
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from material.throttling import CheckoutRateThrottle
from decimal import Decimal
from cart.cart import Cart
from material.background_utils import (
    send_order_confirmation_email_async,
    generate_order_confirmation_pdf_task,
)
from payment.utils import get_vat_breakdown
import logging

logger = logging.getLogger(__name__)


@extend_schema(tags=["Order"])
class CheckoutView(views.APIView):
    """
    Checkout endpoint - converts cart to orders AND initializes payment
    ✅ UPDATED: Now returns Paystack payment URL immediately
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [CheckoutRateThrottle]

    @extend_schema(
        description="Create orders from cart items and initialize payment. Returns orders + payment URL.",
        request=CheckoutSerializer,
        responses={
            201: {"description": "Orders created and payment initialized"},
            400: {"description": "Validation error or empty cart"},
            503: {"description": "Orders created but payment initialization failed"},
        },
    )
    def post(self, request):
        cart = Cart(request)

        # Validate cart is not empty
        if not cart or len(cart) == 0:
            return Response(
                {"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Validate cart prices before checkout
        price_validation_errors = []
        for item in cart:
            product = item["product"]
            cart_price = Decimal(str(item["price"]))
            actual_price = product.price

            if cart_price != actual_price:
                price_validation_errors.append(
                    {
                        "product": product.name,
                        "cart_price": float(cart_price),
                        "actual_price": float(actual_price),
                    }
                )
                logger.warning(
                    f"Price mismatch detected - Product: {product.name}, "
                    f"Cart: {cart_price}, Actual: {actual_price}, "
                    f"User: {request.user.id}"
                )

        if price_validation_errors:
            # Clear cart to force re-add with correct prices
            cart.clear()
            return Response(
                {
                    "error": "Price mismatch detected. Your cart has been cleared. Please add items again.",
                    "details": price_validation_errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate request data with cart context
        serializer = CheckoutSerializer(
            data=request.data, context={"cart": cart, "request": request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        orders_created = []

        try:
            # ✅ Transaction block for database operations only
            with transaction.atomic():
                # Group cart items by product type
                grouped_items = {}
                for item in cart:
                    product_type = item["product"].__class__.__name__
                    if product_type not in grouped_items:
                        grouped_items[product_type] = []
                    grouped_items[product_type].append(item)

                # Order type mapping
                order_type_map = {
                    "NyscKit": NyscKitOrder,
                    "NyscTour": NyscTourOrder,
                    "Church": ChurchOrder,
                }

                # Create separate order for each product type
                for product_type, items in grouped_items.items():
                    order_model = order_type_map.get(product_type)

                    if not order_model:
                        logger.error(f"Unknown product type: {product_type}")
                        continue

                    # Build order data from validated checkout data
                    order_data = {
                        "user": request.user,
                        "first_name": validated_data["first_name"],
                        "middle_name": validated_data.get("middle_name", ""),
                        "last_name": validated_data["last_name"],
                        "phone_number": validated_data["phone_number"],
                    }

                    # Add type-specific fields
                    if order_model == NyscKitOrder:
                        order_data.update(
                            {
                                "call_up_number": validated_data["call_up_number"],
                                "state": validated_data["state"],
                                "local_government": validated_data["local_government"],
                            }
                        )
                    elif order_model == ChurchOrder:
                        order_data.update(
                            {
                                "pickup_on_camp": validated_data.get(
                                    "pickup_on_camp", True
                                ),
                                "delivery_state": validated_data.get(
                                    "delivery_state", ""
                                ),
                                "delivery_lga": validated_data.get("delivery_lga", ""),
                            }
                        )

                    # Create order
                    order = order_model.objects.create(**order_data)

                    # Create order items with FRESH prices from database
                    for item in items:
                        product = item["product"]

                        # ✅ CRITICAL: Always use fresh price from database
                        actual_price = product.price

                        # Get ContentType for the product
                        product_ct = ContentType.objects.get_for_model(product)

                        # Create OrderItem with correct GenericForeignKey setup
                        OrderItem.objects.create(
                            order=order,  # ✅ ForeignKey to the order
                            content_type=product_ct,  # ✅ ContentType for GenericForeignKey
                            object_id=product.id,  # ✅ Object ID for GenericForeignKey
                            price=actual_price,  # ✅ Use database price, not cart price
                            quantity=item["quantity"],
                            extra_fields=item.get("extra_fields", {}),
                        )

                    # ✅ Calculate total_cost from OrderItems
                    order.total_cost = sum(
                        item.get_cost() for item in order.items.all()
                    )
                    order.save()

                    orders_created.append(order)
                    logger.info(
                        f"Order created: {order.serial_number} - "
                        f"Type: {product_type} - User: {request.user.email}"
                    )

            # ✅ NEW: Initialize payment with Paystack immediately after order creation
            from payment.models import PaymentTransaction
            from payment.utils import initialize_payment

            # Calculate total amount with VAT
            subtotal = sum(order.total_cost for order in orders_created)
            vat_breakdown = get_vat_breakdown(subtotal)
            total_amount = vat_breakdown["total_amount"]
            first_order = orders_created[0]

            # Create payment transaction (store total with VAT)
            payment = PaymentTransaction.objects.create(
                amount=total_amount, email=first_order.email
            )
            payment.orders.set(orders_created)

            # Build callback URL for Paystack redirect
            callback_url = request.build_absolute_uri("/api/payment/verify/")

            # Initialize payment with Paystack
            paystack_response = initialize_payment(
                amount=payment.amount,
                email=payment.email,
                reference=payment.reference,
                callback_url=callback_url,
                metadata={
                    "orders": [str(order.id) for order in orders_created],
                    "customer_name": f"{first_order.first_name} {first_order.last_name}",
                    "user_id": str(request.user.id),
                    "subtotal": float(subtotal),
                    "vat_amount": float(vat_breakdown["vat_amount"]),
                    "vat_rate": vat_breakdown["vat_rate"],
                },
            )

            if not paystack_response or not paystack_response.get("status"):
                logger.error(
                    f"Payment initialization failed for user {request.user.id}. "
                    f"Orders created: {[str(o.id) for o in orders_created]}"
                )
                # Orders are created but payment failed - store in session for retry
                request.session["pending_orders"] = [
                    str(order.id) for order in orders_created
                ]

                return Response(
                    {
                        "error": "Orders created but payment initialization failed. Please try again.",
                        "order_ids": [str(order.id) for order in orders_created],
                        "retry_endpoint": "/api/payment/initiate/",
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # Store order IDs in session (for backup/retry scenarios)
            request.session["pending_orders"] = [
                str(order.id) for order in orders_created
            ]

            # Clear cart after successful payment initialization
            cart.clear()

            # ✅ Send emails AFTER transaction commits
            for order in orders_created:
                send_order_confirmation_email_async(str(order.id))
                generate_order_confirmation_pdf_task(str(order.id))

            logger.info(
                f"Checkout completed for user {request.user.email}. "
                f"Orders: {len(orders_created)}, Payment: {payment.reference}, "
                f"Amount: {total_amount}"
            )

            # ✅ Return orders + payment URL in single response
            return Response(
                {
                    "message": "Orders created successfully",
                    "subtotal": str(subtotal),
                    "vat_amount": str(vat_breakdown["vat_amount"]),
                    "vat_rate": vat_breakdown["vat_rate"],
                    "total_amount": str(total_amount),
                    "order_count": len(orders_created),
                    "orders": [
                        {
                            "id": str(order.id),
                            "order_type": order.__class__.__name__.replace(
                                "Order", ""
                            ).lower(),
                            "reference_number": f"MATERIAL-{order.__class__.__name__.replace('Order', '').upper()}-{order.created.strftime('%Y%m%d')}-{order.serial_number:05d}",
                            "total_price": str(order.total_cost),
                        }
                        for order in orders_created
                    ],
                    "payment": {
                        "reference": payment.reference,
                        "authorization_url": paystack_response["data"][
                            "authorization_url"
                        ],
                        "access_code": paystack_response["data"]["access_code"],
                    },
                    "payment_url": paystack_response["data"][
                        "authorization_url"
                    ],  # Direct link for convenience
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception(f"Error during checkout for user {request.user.id}")
            return Response(
                {
                    "error": "An error occurred while processing your order. Please try again."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema_view(
    list=extend_schema(description="List all orders for authenticated user"),
    retrieve=extend_schema(
        description="Get specific order details",
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="Order ID",
            )
        ],
    ),
)
@extend_schema(tags=["Order"])
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing orders
    Users can only view their own orders
    """

    permission_classes = [permissions.IsAuthenticated]
    queryset = (
        BaseOrder.objects.none()
    )  # ✅ ADD THIS LINE - Default for schema generation

    def get_queryset(self):
        """
        ✅ FIXED: Get orders for authenticated user with polymorphic type selection
        Uses select_related to fetch the specific order type (Church/NyscKit/NyscTour)
        """
        # ✅ ADD THIS CHECK
        if getattr(self, "swagger_fake_view", False):
            return BaseOrder.objects.none()

        # Regular queryset for authenticated users
        base_queryset = (
            BaseOrder.objects.filter(user=self.request.user)
            .prefetch_related("items", "items__content_type")
            .select_related(
                "churchorder",  # Fetch ChurchOrder relationship
                "nysckitorder",  # Fetch NyscKitOrder relationship
                "nysctourorder",  # Fetch NyscTourOrder relationship
            )
            .order_by("-created")
        )

        return base_queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on order type"""
        if self.action == "list":
            return OrderListSerializer

        # For retrieve, determine the specific order type
        if hasattr(self, "get_object"):
            try:
                obj = self.get_object()
                # ✅ FIXED: Get actual polymorphic type
                actual_type = self._get_actual_order_type(obj)

                if actual_type == "NyscKitOrder":
                    return NyscKitOrderSerializer
                elif actual_type == "NyscTourOrder":
                    return NyscTourOrderSerializer
                elif actual_type == "ChurchOrder":
                    return ChurchOrderSerializer
            except:
                pass

        return BaseOrderSerializer

    def _get_actual_order_type(self, order):
        """
        ✅ NEW: Helper method to determine the actual polymorphic order type
        """
        # Check if this is a specific order type
        if hasattr(order, "churchorder"):
            return "ChurchOrder"
        elif hasattr(order, "nysckitorder"):
            return "NyscKitOrder"
        elif hasattr(order, "nysctourorder"):
            return "NyscTourOrder"
        return "BaseOrder"

    def _get_actual_order_instance(self, order):
        """
        ✅ NEW: Helper method to get the actual polymorphic instance
        """
        # Return the specific order instance
        if hasattr(order, "churchorder"):
            return order.churchorder
        elif hasattr(order, "nysckitorder"):
            return order.nysckitorder
        elif hasattr(order, "nysctourorder"):
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

            orders_data.append(
                {
                    "id": str(order.id),
                    "serial_number": order.serial_number,
                    "order_type": order_type,  # ✅ NOW SHOWS CORRECT TYPE
                    "total_cost": float(order.total_cost),
                    "paid": order.paid,  # ✅ SHOWS ACTUAL PAID STATUS
                    "created": order.created,
                    "item_count": order.items.count(),
                }
            )

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
        serializer = serializer_class(actual_instance, context={"request": request})

        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def receipt(self, request, pk=None):
        """Get order receipt/confirmation"""
        order = self.get_object()
        actual_order = self._get_actual_order_instance(order)

        # Get correct serializer
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(actual_order, context={"request": request})

        return Response(
            {"order": serializer.data, "receipt_available": True, "paid": order.paid}
        )
