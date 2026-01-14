# orderitem_generation/api_views.py
from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.http import HttpResponse, FileResponse
from django.db.models import Count, Sum, Q
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema, OpenApiParameter
from weasyprint import HTML
from order.models import OrderItem, NyscKitOrder
from measurement.models import Measurement
from products.models import NyscKit, NyscTour, Church
from products.constants import STATES, CHURCH_CHOICES
import logging
import io

logger = logging.getLogger(__name__)


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
        
        # Get order items
        order_items = OrderItem.objects.select_related(
            'order', 'content_type', 'order__nysckitorder'
        ).filter(
            order__paid=True,
            order__nysckitorder__state=state
        ).order_by(
            'order__nysckitorder__local_government',
            'content_type',
            'object_id',
            'extra_fields__size'
        )
        
        if not order_items.exists():
            return Response({
                'error': f'No paid orders found for {state}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Build data for template
        kakhi_measurements = []
        counter = 1
        
        for order_item in order_items:
            if (order_item.content_type == nysc_kit_type and 
                order_item.product and order_item.product.type == 'kakhi'):
                
                # Get measurement if exists
                measurement = None
                try:
                    user = order_item.order.user
                    measurement = Measurement.objects.filter(user=user).first()
                except:
                    pass
                
                kakhi_measurements.append({
                    'sn': counter,
                    'order': order_item.order,
                    'item': order_item,
                    'measurement': measurement
                })
                counter += 1
        
        # Render template
        context = {
            'state': state,
            'kakhi_measurements': kakhi_measurements,
            'total_kakhis': len(kakhi_measurements)
        }
        
        html_string = render_to_string(
            'orderitem_generation/nysckit_state_template.html',
            context
        )
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        
        # Return PDF response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="NYSC_Kit_Orders_{state}.pdf"'
        
        logger.info(f"Generated NYSC Kit PDF for state: {state}")
        
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
                description='State to filter tour orders',
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
        nysc_tour_type = ContentType.objects.get_for_model(NyscTour)

        # Get NyscTour products for this state
        tour_ids = NyscTour.objects.filter(name=state).values_list('id', flat=True)

        # Get order items
        order_items = OrderItem.objects.select_related(
            'order', 'content_type'
        ).filter(
            order__paid=True,
            content_type=nysc_tour_type,
            object_id__in=tour_ids
        ).order_by('order__created')
        
        if not order_items.exists():
            return Response({
                'error': f'No paid tour orders found for {state}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Build data
        orders_data = []
        counter = 1
        
        for item in order_items:
            orders_data.append({
                'sn': counter,
                'full_name': f"{item.order.first_name} {item.order.middle_name} {item.order.last_name}".strip(),
                'state': item.product.name,
                'call_up_number': item.extra_fields.get('call_up_number', 'N/A')
            })
            counter += 1
        
        # Render template
        context = {
            'state': state,
            'orders': orders_data,
            'total_participants': sum(item.quantity for item in order_items)
        }
        
        html_string = render_to_string(
            'orderitem_generation/tour_state_template.html',
            context
        )
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="NYSC_Tour_Orders_{state}.pdf"'
        
        logger.info(f"Generated NYSC Tour PDF for state: {state}")
        
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
        
        # Build data - sorted by product name, size, pickup
        order_items_list = list(order_items)
        order_items_list.sort(
            key=lambda x: (
                x.product.name,
                x.extra_fields.get('size', ''),
                x.order.churchorder.pickup_on_camp
            )
        )
        
        orders_data = []
        counter = 1
        summary_data = {}
        
        for item in order_items_list:
            orders_data.append({
                'sn': counter,
                'full_name': f"{item.order.first_name} {item.order.middle_name} {item.order.last_name}".strip(),
                'church': item.product.church,
                'product': item.product.name,
                'size': item.extra_fields.get('size', 'N/A'),
                'quantity': item.quantity,
                'pickup_on_camp': item.order.churchorder.pickup_on_camp,
                'delivery_state': item.order.churchorder.delivery_state if not item.order.churchorder.pickup_on_camp else 'N/A',
                'delivery_lga': item.order.churchorder.delivery_lga if not item.order.churchorder.pickup_on_camp else 'N/A'
            })
            counter += 1
            
            # Build summary
            key = (item.product.name, item.extra_fields.get('size', 'N/A'))
            if key not in summary_data:
                summary_data[key] = {
                    'product_name': item.product.name,
                    'size': item.extra_fields.get('size', 'N/A'),
                    'total_quantity': 0,
                    'pickup_count': 0,
                    'delivery_count': 0
                }
            
            summary_data[key]['total_quantity'] += item.quantity
            if item.order.churchorder.pickup_on_camp:
                summary_data[key]['pickup_count'] += item.quantity
            else:
                summary_data[key]['delivery_count'] += item.quantity
        
        # Render template
        context = {
            'church': church,
            'orders': orders_data,
            'summary': list(summary_data.values()),
            'total_orders': len(orders_data)
        }
        
        html_string = render_to_string(
            'orderitem_generation/church_state_template.html',
            context
        )
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Church_Orders_{church}.pdf"'
        
        logger.info(f"Generated Church PDF for: {church}")
        
        return response


@extend_schema(tags=['Order Generation'])
class AvailableStatesView(views.APIView):
    """
    Get list of available states for filtering
    """
    permission_classes = [permissions.IsAdminUser]
    
    @extend_schema(
        description="Get list of states that have orders",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'states': {'type': 'array', 'items': {'type': 'string'}},
                    'churches': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        }
    )
    def get(self, request):
        # Get states with NYSC Kit orders
        nysc_states = NyscKitOrder.objects.filter(
            paid=True
        ).values_list('state', flat=True).distinct()
        
        # Get churches with orders
        church_type = ContentType.objects.get_for_model(Church)
        churches_with_orders = OrderItem.objects.filter(
            order__paid=True,
            content_type=church_type
        ).values_list('product__church', flat=True).distinct()
        
        return Response({
            'states': list(set(nysc_states)),
            'churches': list(set(churches_with_orders)),
            'all_states': [state[0] for state in STATES],
            'all_churches': [church[0] for church in CHURCH_CHOICES]
        })