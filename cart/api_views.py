# # cart/api_views.py
# from rest_framework import views, status
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny
# from drf_spectacular.utils import extend_schema
# from .cart import Cart
# from .serializers import (
#     CartSerializer, AddToCartSerializer, UpdateCartItemSerializer, CartItemSerializer
# )
# import logging

# logger = logging.getLogger(__name__)


# @extend_schema(tags=['Cart'])
# class CartDetailView(views.APIView):
#     """
#     Get cart contents
#     Returns all items in the cart with product details
#     """
#     permission_classes = [AllowAny]
    
#     @extend_schema(
#         description="Retrieve cart contents with all items and totals",
#         responses={200: CartSerializer}
#     )
#     def get(self, request):
#         cart = Cart(request)
        
#         # Build cart items list
#         items = []
#         for item in cart:
#             # Find the item_key for this item
#             item_key = None
#             for key in cart.cart.keys():
#                 if str(item['product'].id) in key:
#                     # Verify it's the same item by checking extra_fields
#                     if cart.cart[key].get('extra_fields', {}) == item.get('extra_fields', {}):
#                         item_key = key
#                         break
            
#             items.append({
#                 'product_type': item['product'].product_type,
#                 'product_id': str(item['product'].id),
#                 'product': item['product'],
#                 'quantity': item['quantity'],
#                 'price': item['price'],
#                 'total_price': item['total_price'],
#                 'extra_fields': item.get('extra_fields', {}),
#                 'item_key': item_key
#             })
        
#         # Calculate totals
#         total_cost = sum(item['total_price'] for item in items)
        
#         # Group by product type
#         grouped = {}
#         for item in items:
#             ptype = item['product'].__class__.__name__
#             if ptype not in grouped:
#                 grouped[ptype] = []
#             grouped[ptype].append(item)
        
#         data = {
#             'items': items,
#             'total_items': len(cart),
#             'total_cost': total_cost,
#             'grouped_by_type': grouped
#         }
        
#         serializer = CartSerializer(data)
#         return Response(serializer.data)


# @extend_schema(tags=['Cart'])
# class AddToCartView(views.APIView):
#     """
#     Add item to cart
#     Handles all product types with their specific requirements
#     """
#     permission_classes = [AllowAny]
    
#     @extend_schema(
#         description="Add a product to the cart with required fields based on product type",
#         request=AddToCartSerializer,
#         responses={
#             200: {'description': 'Item added successfully', 'type': 'object'},
#             400: {'description': 'Validation error'}
#         }
#     )
#     def post(self, request):
#         serializer = AddToCartSerializer(data=request.data, context={'request': request})
        
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
#         validated_data = serializer.validated_data
#         cart = Cart(request)
        
#         try:
#             # Add to cart - unpack extra_fields as **kwargs
#             cart.add(
#                 product=validated_data['product'],
#                 quantity=validated_data['quantity'],
#                 override_quantity=validated_data['override'],
#                 **validated_data['extra_fields']  # Unpack extra_fields as kwargs
#             )
            
#             logger.info(
#                 f"Added to cart: {validated_data['product_type']} - "
#                 f"{validated_data['product_id']} - "
#                 f"Extra fields: {validated_data['extra_fields']}"
#             )
            
#             return Response({
#                 'message': f"{validated_data['product'].name} added to cart successfully",
#                 'cart_count': len(cart),
#                 'item': CartItemSerializer({
#                     'product_type': validated_data['product_type'],
#                     'product_id': validated_data['product_id'],
#                     'product': validated_data['product'],
#                     'quantity': validated_data['quantity'],
#                     'price': validated_data['product'].price,
#                     'extra_fields': validated_data['extra_fields']
#                 }).data
#             }, status=status.HTTP_200_OK)
            
#         except Exception as e:
#             logger.error(f"Error adding to cart: {str(e)}", exc_info=True)
#             return Response({
#                 'error': f'Failed to add item to cart: {str(e)}'
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @extend_schema(tags=['Cart'])
# class UpdateCartItemView(views.APIView):
#     """
#     Update cart item quantity or remove item
#     """
#     permission_classes = [AllowAny]
    
#     @extend_schema(
#         description="Update quantity of a cart item. Set quantity to 0 to remove item.",
#         request=UpdateCartItemSerializer,
#         responses={
#             200: {'description': 'Item updated successfully'},
#             404: {'description': 'Item not found in cart'}
#         }
#     )
#     def patch(self, request, item_key):
#         serializer = UpdateCartItemSerializer(data=request.data)
        
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
#         cart = Cart(request)
#         quantity = serializer.validated_data['quantity']
        
#         # Check if item exists in cart
#         if item_key not in cart.cart:
#             return Response({
#                 'error': 'Item not found in cart'
#             }, status=status.HTTP_404_NOT_FOUND)
        
#         try:
#             if quantity == 0:
#                 # Remove item
#                 del cart.cart[item_key]
#                 cart.save()
#                 message = 'Item removed from cart'
#             else:
#                 # Update quantity
#                 cart.cart[item_key]['quantity'] = quantity
#                 cart.save()
#                 message = 'Quantity updated successfully'
            
#             return Response({
#                 'message': message,
#                 'cart_count': len(cart)
#             }, status=status.HTTP_200_OK)
            
#         except Exception as e:
#             logger.error(f"Error updating cart item: {str(e)}", exc_info=True)
#             return Response({
#                 'error': 'Failed to update cart item'
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @extend_schema(tags=['Cart'])
# class RemoveFromCartView(views.APIView):
#     """
#     Remove specific item from cart
#     """
#     permission_classes = [AllowAny]
    
#     @extend_schema(
#         description="Remove a specific item from the cart by item key",
#         responses={
#             200: {'description': 'Item removed successfully'},
#             404: {'description': 'Item not found in cart'}
#         }
#     )
#     def delete(self, request, item_key):
#         cart = Cart(request)
        
#         if item_key not in cart.cart:
#             return Response({
#                 'error': 'Item not found in cart'
#             }, status=status.HTTP_404_NOT_FOUND)
        
#         try:
#             del cart.cart[item_key]
#             cart.save()
            
#             logger.info(f"Removed item from cart: {item_key}")
            
#             return Response({
#                 'message': 'Item removed from cart',
#                 'cart_count': len(cart)
#             }, status=status.HTTP_200_OK)
            
#         except Exception as e:
#             logger.error(f"Error removing from cart: {str(e)}", exc_info=True)
#             return Response({
#                 'error': 'Failed to remove item from cart'
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @extend_schema(tags=['Cart'])
# class ClearCartView(views.APIView):
#     """
#     Clear all items from cart
#     """
#     permission_classes = [AllowAny]
    
#     @extend_schema(
#         description="Remove all items from the cart",
#         responses={200: {'description': 'Cart cleared successfully'}}
#     )
#     def post(self, request):
#         cart = Cart(request)
#         cart.clear()
        
#         logger.info("Cart cleared")
        
#         return Response({
#             'message': 'Cart cleared successfully',
#             'cart_count': 0
#         }, status=status.HTTP_200_OK)


# @extend_schema(tags=['Cart'])
# class CartSummaryView(views.APIView):
#     """
#     Get cart summary (count and total only)
#     Lightweight endpoint for header/navigation display
#     """
#     permission_classes = [AllowAny]
    
#     @extend_schema(
#         description="Get quick cart summary - item count and total cost only",
#         responses={
#             200: {
#                 'type': 'object',
#                 'properties': {
#                     'count': {'type': 'integer'},
#                     'total': {'type': 'number'}
#                 }
#             }
#         }
#     )
#     def get(self, request):
#         cart = Cart(request)
        
#         # Calculate total by iterating through cart
#         total_cost = sum(item['total_price'] for item in cart)
        
#         return Response({
#             'count': len(cart),
#             'total': float(total_cost)
#         }, status=status.HTTP_200_OK)

# cart/api_views_debug.py - DIAGNOSTIC VERSION
# Copy this over cart/api_views.py temporarily to debug
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from .cart import Cart
from .serializers import (
    CartSerializer, AddToCartSerializer, UpdateCartItemSerializer, CartItemSerializer
)
import logging

logger = logging.getLogger(__name__)


@extend_schema(tags=['Cart'])
class CartSummaryView(views.APIView):
    """Get cart summary (count and total only)"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        logger.info("=" * 80)
        logger.info("CART SUMMARY REQUEST")
        logger.info(f"Session key: {request.session.session_key}")
        logger.info(f"Session data: {dict(request.session)}")
        
        cart = Cart(request)
        logger.info(f"Cart object created. Cart.cart contents: {cart.cart}")
        logger.info(f"Cart __len__: {len(cart)}")
        
        try:
            cart_items = list(cart)  # Try to iterate
            logger.info(f"Cart items from iteration: {len(cart_items)} items")
            for idx, item in enumerate(cart_items):
                logger.info(f"  Item {idx}: product={item.get('product')}, qty={item.get('quantity')}")
            
            total_cost = sum(item['total_price'] for item in cart)
            logger.info(f"Total cost calculated: {total_cost}")
            
            response_data = {
                'count': len(cart),
                'total': float(total_cost)
            }
            logger.info(f"Response data: {response_data}")
            logger.info("=" * 80)
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in cart summary: {str(e)}", exc_info=True)
            logger.info("=" * 80)
            return Response({
                'count': 0,
                'total': 0.0,
                'error': str(e)
            }, status=status.HTTP_200_OK)


@extend_schema(tags=['Cart'])
class AddToCartView(views.APIView):
    """Add item to cart"""
    permission_classes = [AllowAny]
    
    @extend_schema(
        description="Add a product to the cart",
        request=AddToCartSerializer,
        responses={200: {'description': 'Item added'}}
    )
    def post(self, request):
        logger.info("=" * 80)
        logger.info("ADD TO CART REQUEST")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Session key: {request.session.session_key}")
        logger.info(f"Session before: {dict(request.session)}")
        
        serializer = AddToCartSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            logger.error(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        logger.info(f"Validated data: {validated_data}")
        logger.info(f"Extra fields: {validated_data.get('extra_fields')}")
        
        cart = Cart(request)
        logger.info(f"Cart initialized. Current cart.cart: {cart.cart}")
        
        try:
            # Try the cart.add() call
            logger.info("Calling cart.add()...")
            cart.add(
                product=validated_data['product'],
                quantity=validated_data['quantity'],
                override_quantity=validated_data['override'],
                extra_fields=validated_data['extra_fields']
            )
            logger.info("cart.add() completed successfully")
            
            logger.info(f"Cart after add. cart.cart: {cart.cart}")
            logger.info(f"Cart length: {len(cart)}")
            logger.info(f"Session after add: {dict(request.session)}")
            logger.info(f"Session modified flag: {request.session.modified}")
            
            # Try to save session explicitly
            request.session.save()
            logger.info("Session saved explicitly")
            logger.info(f"Session after save: {dict(request.session)}")
            
            response_data = {
                'message': f"{validated_data['product'].name} added to cart",
                'cart_count': len(cart),
                'cart_contents': cart.cart,  # Include raw cart data for debugging
                'session_key': request.session.session_key
            }
            
            logger.info(f"Response: {response_data}")
            logger.info("=" * 80)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error adding to cart: {str(e)}", exc_info=True)
            logger.info("=" * 80)
            return Response({
                'error': f'Failed to add: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Cart'])
class CartDetailView(views.APIView):
    """Get full cart contents"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        logger.info("=" * 80)
        logger.info("CART DETAIL REQUEST")
        logger.info(f"Session key: {request.session.session_key}")
        logger.info(f"Session data: {dict(request.session)}")
        
        cart = Cart(request)
        logger.info(f"Cart.cart raw: {cart.cart}")
        
        items = []
        try:
            for item in cart:
                logger.info(f"Processing cart item: {item}")
                item_key = None
                for key in cart.cart.keys():
                    if str(item['product'].id) in key:
                        if cart.cart[key].get('extra_fields', {}) == item.get('extra_fields', {}):
                            item_key = key
                            break
                
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
            
            logger.info(f"Processed {len(items)} items")
            
            total_cost = sum(item['total_price'] for item in items)
            
            data = {
                'items': items,
                'total_items': len(cart),
                'total_cost': total_cost,
                'grouped_by_type': {},
                'debug_session': dict(request.session)
            }
            
            serializer = CartSerializer(data)
            logger.info("=" * 80)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error getting cart details: {str(e)}", exc_info=True)
            logger.info("=" * 80)
            return Response({
                'items': [],
                'total_items': 0,
                'total_cost': 0,
                'grouped_by_type': {},
                'error': str(e),
                'debug_session': dict(request.session)
            })


@extend_schema(tags=['Cart'])
class ClearCartView(views.APIView):
    """Clear cart"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        cart = Cart(request)
        cart.clear()
        return Response({'message': 'Cart cleared', 'cart_count': 0})


@extend_schema(tags=['Cart'])
class UpdateCartItemView(views.APIView):
    """Update cart item"""
    permission_classes = [AllowAny]
    
    def patch(self, request, item_key):
        # Existing implementation
        pass


@extend_schema(tags=['Cart'])
class RemoveFromCartView(views.APIView):
    """Remove from cart"""
    permission_classes = [AllowAny]
    
    def delete(self, request, item_key):
        # Existing implementation
        pass