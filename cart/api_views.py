# cart/api_views.py
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, extend_schema_view
from .cart import Cart
from .serializers import (
    CartSerializer, AddToCartSerializer, UpdateCartItemSerializer, CartItemSerializer
)
import logging

logger = logging.getLogger(__name__)


@extend_schema(tags=['Cart'])
class CartDetailView(views.APIView):
    """
    Get cart contents
    Returns all items in the cart with product details
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        description="Retrieve cart contents with all items and totals",
        responses={200: CartSerializer}
    )
    def get(self, request):
        cart = Cart(request)
        
        # Build cart items list
        items = []
        for item in cart:
            # Extract the composite key parts
            item_key = next(
                (key for key in cart.cart.keys() 
                 if str(item['product'].id) in key), 
                None
            )
            
            items.append({
                'product_type': item['product'].product_type,
                'product_id': str(item['product'].id),
                'product': item['product'],
                'quantity': item['quantity'],
                'price': item['price'],
                'total_price': item['total_price'],
                'extra_fields': item.get('extra_fields', {}),
                'item_key': item_key
            })
        
        # Calculate totals
        total_cost = sum(item['total_price'] for item in items)
        
        # Group by product type
        grouped = {}
        for item in items:
            ptype = item['product'].__class__.__name__
            if ptype not in grouped:
                grouped[ptype] = []
            grouped[ptype].append(item)
        
        data = {
            'items': items,
            'total_items': len(cart),
            'total_cost': total_cost,
            'grouped_by_type': grouped
        }
        
        serializer = CartSerializer(data)
        return Response(serializer.data)


@extend_schema(tags=['Cart'])
class AddToCartView(views.APIView):
    """
    Add item to cart
    Handles all product types with their specific requirements
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        description="Add a product to the cart with required fields based on product type",
        request=AddToCartSerializer,
        responses={
            200: {'description': 'Item added successfully', 'type': 'object'},
            400: {'description': 'Validation error'}
        }
    )
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        cart = Cart(request)
        
        try:
            # Add to cart
            cart.add(
                product=validated_data['product'],
                quantity=validated_data['quantity'],
                override_quantity=validated_data['override'],
                extra_fields=validated_data['extra_fields']
            )
            
            logger.info(
                f"Added to cart: {validated_data['product_type']} - "
                f"{validated_data['product_id']}"
            )
            
            return Response({
                'message': f"{validated_data['product'].name} added to cart successfully",
                'cart_count': len(cart),
                'item': CartItemSerializer({
                    'product_type': validated_data['product_type'],
                    'product_id': validated_data['product_id'],
                    'product': validated_data['product'],
                    'quantity': validated_data['quantity'],
                    'price': validated_data['product'].price,
                    'extra_fields': validated_data['extra_fields']
                }).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error adding to cart: {str(e)}")
            return Response({
                'error': 'Failed to add item to cart'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Cart'])
class UpdateCartItemView(views.APIView):
    """
    Update cart item quantity or remove item
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        description="Update quantity of a cart item. Set quantity to 0 to remove item.",
        request=UpdateCartItemSerializer,
        responses={
            200: {'description': 'Item updated successfully'},
            404: {'description': 'Item not found in cart'}
        }
    )
    def patch(self, request, item_key):
        serializer = UpdateCartItemSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        cart = Cart(request)
        quantity = serializer.validated_data['quantity']
        
        # Check if item exists in cart
        if item_key not in cart.cart:
            return Response({
                'error': 'Item not found in cart'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            if quantity == 0:
                # Remove item
                del cart.cart[item_key]
                cart.save()
                message = 'Item removed from cart'
            else:
                # Update quantity
                cart.cart[item_key]['quantity'] = quantity
                cart.save()
                message = 'Quantity updated successfully'
            
            return Response({
                'message': message,
                'cart_count': len(cart)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating cart item: {str(e)}")
            return Response({
                'error': 'Failed to update cart item'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Cart'])
class RemoveFromCartView(views.APIView):
    """
    Remove specific item from cart
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        description="Remove a specific item from the cart by item key",
        responses={
            200: {'description': 'Item removed successfully'},
            404: {'description': 'Item not found in cart'}
        }
    )
    def delete(self, request, item_key):
        cart = Cart(request)
        
        if item_key not in cart.cart:
            return Response({
                'error': 'Item not found in cart'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            del cart.cart[item_key]
            cart.save()
            
            logger.info(f"Removed item from cart: {item_key}")
            
            return Response({
                'message': 'Item removed from cart',
                'cart_count': len(cart)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error removing from cart: {str(e)}")
            return Response({
                'error': 'Failed to remove item from cart'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Cart'])
class ClearCartView(views.APIView):
    """
    Clear all items from cart
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        description="Remove all items from the cart",
        responses={200: {'description': 'Cart cleared successfully'}}
    )
    def post(self, request):
        cart = Cart(request)
        cart.clear()
        
        logger.info("Cart cleared")
        
        return Response({
            'message': 'Cart cleared successfully',
            'cart_count': 0
        }, status=status.HTTP_200_OK)


@extend_schema(tags=['Cart'])
class CartSummaryView(views.APIView):
    """
    Get cart summary (count and total only)
    Lightweight endpoint for header/navigation display
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        description="Get quick cart summary - item count and total cost only",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'count': {'type': 'integer'},
                    'total': {'type': 'number'}
                }
            }
        }
    )
    def get(self, request):
        cart = Cart(request)
        
        total_cost = sum(item['total_price'] for item in cart)
        
        return Response({
            'count': len(cart),
            'total': float(total_cost)
        }, status=status.HTTP_200_OK)