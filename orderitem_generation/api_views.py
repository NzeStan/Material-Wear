# orderitem_generation/api_views.py
from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import Count, Sum, Q
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema, OpenApiParameter
from weasyprint import HTML
from order.models import OrderItem, NyscKitOrder, NyscTourOrder, ChurchOrder
from measurement.models import Measurement
from products.models import NyscKit, NyscTour, Church
from products.constants import STATES, CHURCH_CHOICES
from collections import defaultdict
import logging
import io
import cloudinary
import cloudinary.uploader
from django.utils import timezone

logger = logging.getLogger(__name__)


def upload_pdf_to_cloudinary(pdf_bytes, filename):
    """
    Upload PDF to Cloudinary
    
    Args:
        pdf_bytes: PDF content as bytes
        filename: Desired filename
        
    Returns:
        str: Cloudinary URL
    """
    try:
        result = cloudinary.uploader.upload(
            pdf_bytes,
            folder='order_generation_pdfs',
            resource_type='raw',
            public_id=filename.replace('.pdf', ''),
            format='pdf'
        )
        logger.info(f"PDF uploaded to Cloudinary: {result['secure_url']}")
        return result['secure_url']
    except Exception as e:
        logger.error(f"Error uploading to Cloudinary: {str(e)}")
        return None


@extend_schema(tags=['Order Generation'])
class NyscKitPDFView(views.APIView):
    """
    Generate PDF report for NYSC Kit orders by state
    Includes measurements for kakhi orders
    """
    permission_classes = [permissions.IsAdminUser]
    
    @extend_schema(
        description="Generate PDF report for NYSC Kit orders filtered by state",
        parameters=[
            OpenApiParameter(
                name='state',
                type=str,
                location=OpenApiParameter.QUERY,
                description='State to filter orders',
                required=True
            ),
        ],
        responses={
            200: {'description': 'PDF file'},
            400: {'description': 'Invalid state or no orders found'}
        }
    )
    def get(self, request):
        state = request.query_params.get('state')
        
        if not state:
            return Response({
                'error': 'State parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get ContentType for NyscKit
        nysc_kit_type = ContentType.objects.get_for_model(NyscKit)
        
        # Get all order items for this state
        order_items = OrderItem.objects.select_related(
            'order', 'content_type', 'order__nysckitorder'
        ).filter(
            order__paid=True,
            order__nysckitorder__state=state,
            content_type=nysc_kit_type
        ).order_by('order__nysckitorder__local_government')
        
        if not order_items.exists():
            return Response({
                'error': f'No paid orders found for {state}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Separate orders by product type
        kakhi_orders = []
        vest_orders = []
        cap_orders = []
        
        kakhi_counter = 1
        vest_counter = 1
        cap_counter = 1
        
        for order_item in order_items:
            if not order_item.product:
                continue
                
            product = order_item.product
            order = order_item.order
            nysc_order = order.nysckitorder
            
            full_name = f"{order.last_name} {order.middle_name} {order.first_name}".strip().upper()
            
            if product.type == 'kakhi':
                # Get measurement if exists
                measurement = None
                try:
                    measurement = Measurement.objects.filter(user=order.user).first()
                except:
                    pass
                
                kakhi_orders.append({
                    'sn': kakhi_counter,
                    'full_name': full_name,
                    'call_up_number': nysc_order.call_up_number,
                    'lga': nysc_order.local_government,
                    'quantity': order_item.quantity,
                    'measurement': measurement
                })
                kakhi_counter += 1
                
            elif product.type == 'vest':
                vest_orders.append({
                    'sn': vest_counter,
                    'full_name': full_name,
                    'call_up_number': nysc_order.call_up_number,
                    'lga': nysc_order.local_government,
                    'size': order_item.extra_fields.get('size', 'N/A'),
                    'quantity': order_item.quantity,
                    'product': product.name
                })
                vest_counter += 1
                
            elif product.type == 'cap':
                cap_orders.append({
                    'sn': cap_counter,
                    'full_name': full_name,
                    'call_up_number': nysc_order.call_up_number,
                    'lga': nysc_order.local_government,
                    'size': order_item.extra_fields.get('size', 'Free Size'),
                    'quantity': order_item.quantity,
                    'product': product.name
                })
                cap_counter += 1
        
        # Render template
        context = {
            'state': state,
            'kakhi_orders': kakhi_orders,
            'vest_orders': vest_orders,
            'cap_orders': cap_orders,
            'total_kakhis': len(kakhi_orders),
            'total_vests': len(vest_orders),
            'total_caps': len(cap_orders)
        }
        
        html_string = render_to_string(
            'orderitem_generation/nysckit_state_template.html',
            context
        )
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()
        
        # Create filename
        filename = f"NYSC_Kit_Orders_{state}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Upload to Cloudinary
        cloudinary_url = upload_pdf_to_cloudinary(pdf_bytes, filename)
        
        # Return PDF for instant download
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        if cloudinary_url:
            response['X-Cloudinary-URL'] = cloudinary_url
        
        logger.info(f"Generated NYSC Kit PDF for state: {state}, Cloudinary: {cloudinary_url}")
        
        return response


@extend_schema(tags=['Order Generation'])
class NyscTourPDFView(views.APIView):
    """
    Generate PDF report for NYSC Tour orders by state
    """
    permission_classes = [permissions.IsAdminUser]
    
    @extend_schema(
        description="Generate PDF report for NYSC Tour orders filtered by state",
        parameters=[
            OpenApiParameter(
                name='state',
                type=str,
                location=OpenApiParameter.QUERY,
                description='State to filter orders',
                required=True
            ),
        ],
        responses={
            200: {'description': 'PDF file'},
            404: {'description': 'No orders found'}
        }
    )
    def get(self, request):
        state = request.query_params.get('state')
        
        if not state:
            return Response({
                'error': 'State parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get ContentType for NyscTour
        tour_type = ContentType.objects.get_for_model(NyscTour)
        
        # Get order items
        order_items = OrderItem.objects.select_related(
            'order', 'content_type', 'order__nysctourorder'
        ).filter(
            order__paid=True,
            order__nysctourorder__state=state,
            content_type=tour_type
        ).order_by('order__nysctourorder__local_government')
        
        if not order_items.exists():
            return Response({
                'error': f'No paid orders found for {state}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Build data for template
        tour_orders = []
        total_participants = 0
        counter = 1
        
        for order_item in order_items:
            if not order_item.product:
                continue
                
            order = order_item.order
            tour_order = order.nysctourorder
            
            full_name = f"{order.last_name} {order.middle_name} {order.first_name}".strip().upper()
            
            tour_orders.append({
                'sn': counter,
                'full_name': full_name,
                'call_up_number': tour_order.call_up_number,
                'lga': tour_order.local_government,
                'product': order_item.product.name,
                'quantity': order_item.quantity,
                'amount': order_item.price * order_item.quantity
            })
            
            # Total participants is the sum of quantities (each quantity = number of people)
            total_participants += order_item.quantity
            counter += 1
        
        # Render template
        context = {
            'state': state,
            'tour_orders': tour_orders,
            'total_orders': len(tour_orders),
            'total_participants': total_participants
        }
        
        html_string = render_to_string(
            'orderitem_generation/tour_state_template.html',
            context
        )
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()
        
        # Create filename
        filename = f"NYSC_Tour_Orders_{state}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Upload to Cloudinary
        cloudinary_url = upload_pdf_to_cloudinary(pdf_bytes, filename)
        
        # Return PDF for instant download
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        if cloudinary_url:
            response['X-Cloudinary-URL'] = cloudinary_url
        
        logger.info(f"Generated NYSC Tour PDF for state: {state}, Cloudinary: {cloudinary_url}")
        
        return response


@extend_schema(tags=['Order Generation'])
class ChurchPDFView(views.APIView):
    """
    Generate PDF report for Church orders by church type
    """
    permission_classes = [permissions.IsAdminUser]
    
    @extend_schema(
        description="Generate PDF report for Church orders filtered by church",
        parameters=[
            OpenApiParameter(
                name='church',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Church to filter orders',
                required=True
            ),
        ],
        responses={
            200: {'description': 'PDF file'},
            404: {'description': 'No orders found'}
        }
    )
    def get(self, request):
        church = request.query_params.get('church')
        
        if not church:
            return Response({
                'error': 'Church parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get ContentType for Church
        church_type = ContentType.objects.get_for_model(Church)
        church_ids = Church.objects.filter(church=church).values_list('id', flat=True)
        
        # Get order items
        order_items = OrderItem.objects.select_related(
            'order', 'content_type', 'order__churchorder'
        ).filter(
            order__paid=True,
            content_type=church_type,
            object_id__in=church_ids
        )
        
        if not order_items.exists():
            return Response({
                'error': f'No paid orders found for {church}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Build data for template
        orders_data = []
        summary_data = defaultdict(lambda: {
            'product_name': '',
            'size': '',
            'total_quantity': 0,
            'pickup_count': 0,
            'delivery_count': 0
        })
        
        # For grouping by size
        sizes_grouping = defaultdict(list)
        
        counter = 1
        
        for order_item in order_items:
            if not order_item.product:
                continue
                
            order = order_item.order
            church_order = order.churchorder
            
            full_name = f"{order.last_name} {order.middle_name} {order.first_name}".strip().upper()
            size = order_item.extra_fields.get('size', 'N/A')
            custom_name = order_item.extra_fields.get('custom_name_text', '')
            
            orders_data.append({
                'sn': counter,
                'full_name': full_name,
                'product': order_item.product.name,
                'custom_name': custom_name,
                'size': size,
                'quantity': order_item.quantity,
                'pickup_on_camp': church_order.pickup_on_camp,
                'delivery_state': church_order.delivery_state if not church_order.pickup_on_camp else 'N/A',
                'delivery_lga': church_order.delivery_lga if not church_order.pickup_on_camp else 'N/A'
            })
            
            # Add to size grouping if custom name exists
            if custom_name:
                sizes_grouping[size].append({
                    'full_name': full_name,
                    'custom_name': custom_name,
                    'product': order_item.product.name,
                    'quantity': order_item.quantity
                })
            
            # Update summary
            key = f"{order_item.product.name}_{size}"
            summary_data[key]['product_name'] = order_item.product.name
            summary_data[key]['size'] = size
            summary_data[key]['total_quantity'] += order_item.quantity
            
            if church_order.pickup_on_camp:
                summary_data[key]['pickup_count'] += order_item.quantity
            else:
                summary_data[key]['delivery_count'] += order_item.quantity
            
            counter += 1
        
        # Render template
        context = {
            'church': church,
            'orders': orders_data,
            'summary': list(summary_data.values()),
            'total_orders': len(orders_data),
            'sizes_grouping': dict(sizes_grouping) if sizes_grouping else None
        }
        
        html_string = render_to_string(
            'orderitem_generation/church_state_template.html',
            context
        )
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()
        
        # Create filename
        filename = f"Church_Orders_{church}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Upload to Cloudinary
        cloudinary_url = upload_pdf_to_cloudinary(pdf_bytes, filename)
        
        # Return PDF for instant download
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        if cloudinary_url:
            response['X-Cloudinary-URL'] = cloudinary_url
        
        logger.info(f"Generated Church PDF for: {church}, Cloudinary: {cloudinary_url}")
        
        return response


@extend_schema(tags=['Order Generation'])
class AvailableStatesView(views.APIView):
    """
    Get list of available states and churches for filtering
    """
    permission_classes = [permissions.IsAdminUser]
    
    @extend_schema(
        description="Get list of states and churches that have orders",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'nysc_kit_states': {'type': 'array', 'items': {'type': 'string'}},
                    'nysc_tour_states': {'type': 'array', 'items': {'type': 'string'}},
                    'churches': {'type': 'array', 'items': {'type': 'string'}},
                    'all_states': {'type': 'array', 'items': {'type': 'string'}},
                    'all_churches': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        }
    )
    def get(self, request):
        # Get states with NYSC Kit orders
        nysc_kit_states = NyscKitOrder.objects.filter(
            paid=True
        ).values_list('state', flat=True).distinct()
        
        # Get states with NYSC Tour orders
        nysc_tour_states = NyscTourOrder.objects.filter(
            paid=True
        ).values_list('state', flat=True).distinct()
        
        # Get churches with orders
        church_type = ContentType.objects.get_for_model(Church)
        churches_with_orders = OrderItem.objects.filter(
            order__paid=True,
            content_type=church_type
        ).values_list('product__church', flat=True).distinct()
        
        return Response({
            'nysc_kit_states': list(set(nysc_kit_states)),
            'nysc_tour_states': list(set(nysc_tour_states)),
            'churches': list(set(churches_with_orders)),
            'all_states': [state[0] for state in STATES],
            'all_churches': [church[0] for church in CHURCH_CHOICES]
        })