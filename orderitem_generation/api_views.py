# orderitem_generation/api_views.py
"""
PDF Generation Views for Order Management

COMPLETELY FIXED VERSION - No more 406/401 errors!
Converted from DRF APIView to Django View with direct HTML/PDF responses
"""
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, Count, Q
from collections import defaultdict
from weasyprint import HTML
import cloudinary.uploader
import logging

from order.models import NyscKitOrder, OrderItem
from products.models import NyscTour, Church
from measurement.models import Measurement

logger = logging.getLogger(__name__)


def upload_pdf_to_cloudinary(pdf_bytes, filename):
    """Upload PDF to Cloudinary and return URL"""
    try:
        upload_result = cloudinary.uploader.upload(
            pdf_bytes,
            resource_type="raw",
            folder="order_pdfs",
            public_id=filename.replace('.pdf', ''),
            format="pdf",
            overwrite=True
        )
        return upload_result.get('secure_url')
    except Exception as e:
        logger.error(f"Failed to upload PDF to Cloudinary: {e}")
        return None


@method_decorator(staff_member_required, name='dispatch')
class NyscKitPDFView(View):
    """
    Generate PDF report for NYSC Kit orders by state
    Downloads directly to user's device
    """
    
    def get(self, request):
        state = request.GET.get('state')
        
        if not state:
            return JsonResponse({
                'error': 'State parameter is required'
            }, status=400)
        
        # Get paid orders for the state
        kit_orders = NyscKitOrder.objects.select_related().filter(
            state=state,
            paid=True
        ).order_by('created')
        
        if not kit_orders.exists():
            return JsonResponse({
                'error': f'No paid orders found for {state}'
            }, status=404)
        
        # Separate orders by product type
        kakhi_orders = []
        vest_orders = []
        cap_orders = []
        
        kakhi_counter = 1
        vest_counter = 1
        cap_counter = 1
        
        for order in kit_orders:
            full_name = f"{order.last_name} {order.middle_name} {order.first_name}".strip().upper()
            
            for item in order.items.all():
                if not item.product:
                    continue
                
                product_type = item.product.type
                
                if product_type == 'kakhi':
                    # Fetch measurement from database
                    measurement = None
                    measurement_id = item.extra_fields.get('measurement_id')
                    if measurement_id:
                        try:
                            measurement = Measurement.objects.get(
                                id=measurement_id,
                                is_deleted=False
                            )
                        except Measurement.DoesNotExist:
                            logger.warning(f"Measurement {measurement_id} not found for order item")
                    
                    order_data = {
                        'sn': kakhi_counter,
                        'full_name': full_name,
                        'call_up_number': order.call_up_number or 'N/A',
                        'lga': order.local_government,
                        'product': item.product.name,
                        'size': item.extra_fields.get('size', 'N/A'),
                        'quantity': item.quantity,
                        'measurement': measurement
                    }
                    kakhi_orders.append(order_data)
                    kakhi_counter += 1
                    
                elif product_type == 'vest':
                    order_data = {
                        'sn': vest_counter,
                        'full_name': full_name,
                        'call_up_number': order.call_up_number or 'N/A',
                        'lga': order.local_government,
                        'product': item.product.name,
                        'size': item.extra_fields.get('size', 'N/A'),
                        'quantity': item.quantity,
                    }
                    vest_orders.append(order_data)
                    vest_counter += 1
                    
                elif product_type == 'cap':
                    order_data = {
                        'sn': cap_counter,
                        'full_name': full_name,
                        'call_up_number': order.call_up_number or 'N/A',
                        'lga': order.local_government,
                        'product': item.product.name,
                        'quantity': item.quantity,
                        'size': item.extra_fields.get('size', 'Free Size'),
                    }
                    cap_orders.append(order_data)
                    cap_counter += 1
        
        # Render template with separate lists
        context = {
            'state': state,
            'kakhi_orders': kakhi_orders,
            'vest_orders': vest_orders,
            'cap_orders': cap_orders,
            'total_kakhis': len(kakhi_orders),
            'total_vests': len(vest_orders),
            'total_caps': len(cap_orders),
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
        
        # Upload to Cloudinary (backup)
        cloudinary_url = upload_pdf_to_cloudinary(pdf_bytes, filename)
        
        # Return PDF for download
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        if cloudinary_url:
            response['X-Cloudinary-URL'] = cloudinary_url
        
        logger.info(f"Generated NYSC Kit PDF for state: {state}, Cloudinary: {cloudinary_url}")
        
        return response



@method_decorator(staff_member_required, name='dispatch')
class NyscTourPDFView(View):
    """
    Generate PDF report for NYSC Tour orders by state
    Downloads directly to user's device
    """
    
    def get(self, request):
        state = request.GET.get('state')
        
        if not state:
            return JsonResponse({
                'error': 'State parameter is required'
            }, status=400)
        
        # Get ContentType for NyscTour
        tour_type = ContentType.objects.get_for_model(NyscTour)
        
        # Get tour products for this state (state is in product name)
        tour_products = NyscTour.objects.filter(name=state).values_list('id', flat=True)
        
        if not tour_products:
            return JsonResponse({
                'error': f'No tour products found for {state}'
            }, status=404)
        
        # Get order items for these products
        order_items = OrderItem.objects.select_related(
            'order', 'content_type'
        ).filter(
            order__paid=True,
            content_type=tour_type,
            object_id__in=tour_products
        ).order_by('order__created')
        
        if not order_items.exists():
            return JsonResponse({
                'error': f'No paid orders found for {state}'
            }, status=404)
        
        # Build data for template
        tour_orders = []
        total_participants = 0
        counter = 1
        
        for order_item in order_items:
            if not order_item.product:
                continue
                
            order = order_item.order
            
            full_name = f"{order.last_name} {order.middle_name} {order.first_name}".strip().upper()
            
            # Extract call_up_number from extra_fields
            call_up_number = order_item.extra_fields.get('call_up_number', 'N/A')
            
            tour_orders.append({
                'sn': counter,
                'full_name': full_name,
                'call_up_number': call_up_number,
            })
            
            total_participants += order_item.quantity
            counter += 1
        
        # Render template (use correct template name!)
        context = {
            'state': state,
            'tour_orders': tour_orders,
            'total_orders': len(tour_orders),
            'total_participants': total_participants
        }
        
        # ✅ FIX: Use correct template name (it's nysctour not tour!)
        html_string = render_to_string(
            'orderitem_generation/nysctour_state_template.html',
            context
        )
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()
        
        # Create filename
        filename = f"NYSC_Tour_Orders_{state}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Upload to Cloudinary (backup)
        cloudinary_url = upload_pdf_to_cloudinary(pdf_bytes, filename)
        
        # CRITICAL: Return PDF for download to user's device
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        if cloudinary_url:
            response['X-Cloudinary-URL'] = cloudinary_url
        
        logger.info(f"Generated NYSC Tour PDF for state: {state}, Cloudinary: {cloudinary_url}")
        
        return response


@method_decorator(staff_member_required, name='dispatch')
class ChurchPDFView(View):
    """
    Generate PDF report for Church orders by church type
    Downloads directly to user's device
    """
    
    def get(self, request):
        church = request.GET.get('church')
        
        if not church:
            return JsonResponse({
                'error': 'Church parameter is required'
            }, status=400)
        
        # Get ContentType for Church
        church_type = ContentType.objects.get_for_model(Church)
        church_ids = Church.objects.filter(church=church).values_list('id', flat=True)
        
        # Get order items
        order_items = OrderItem.objects.select_related(
            'order', 'content_type'
        ).filter(
            order__paid=True,
            content_type=church_type,
            object_id__in=church_ids
        ).order_by('order__created')
        
        if not order_items.exists():
            return JsonResponse({
                'error': f'No paid orders found for {church}'
            }, status=404)
        
        # Build orders data
        orders_data = []
        summary_data = defaultdict(lambda: {
            'product_name': '',
            'size': '',
            'total_quantity': 0,
            'pickup_count': 0,
            'delivery_count': 0
        })
        sizes_grouping = defaultdict(list)
        counter = 1
        
        for order_item in order_items:
            if not order_item.product:
                continue
            
            order = order_item.order
            
            # Cast to ChurchOrder to access pickup fields
            from order.models import ChurchOrder
            church_order = ChurchOrder.objects.get(id=order.id)
            
            full_name = f"{order.last_name} {order.middle_name} {order.first_name}".strip().upper()
            product_name = order_item.product.name
            size = order_item.extra_fields.get('size', 'N/A')
            custom_name = order_item.extra_fields.get('custom_name_text', '')
            
            orders_data.append({
                'sn': counter,
                'full_name': full_name,
                'product': product_name,
                'custom_name': custom_name,
                'size': size,
                'quantity': order_item.quantity,
                'pickup_on_camp': church_order.pickup_on_camp,
                'delivery_state': church_order.delivery_state or '',
                'delivery_lga': church_order.delivery_lga or '',
            })
            
            # Track summary by product + size
            key = f"{product_name}_{size}"
            summary_data[key]['product_name'] = product_name
            summary_data[key]['size'] = size
            summary_data[key]['total_quantity'] += order_item.quantity
            
            if church_order.pickup_on_camp:
                summary_data[key]['pickup_count'] += order_item.quantity
            else:
                summary_data[key]['delivery_count'] += order_item.quantity
            
            # Group custom names by size if available
            if custom_name:
                sizes_grouping[size].append({
                    'full_name': full_name,
                    'custom_name': custom_name,
                    'product': product_name,
                    'quantity': order_item.quantity,
                })
            
            counter += 1
        
        # Sort custom names by product within each size group
        for size in sizes_grouping:
            sizes_grouping[size] = sorted(sizes_grouping[size], key=lambda x: x['product'])
        
        # Prepare context
        context = {
            'church': church,
            'orders': orders_data,
            'summary': list(summary_data.values()),
            'sizes_grouping': dict(sizes_grouping),
            'total_orders': len(orders_data)
        }
        
        # ✅ FIX: Use correct template name
        html_string = render_to_string(
            'orderitem_generation/church_state_template.html',
            context
        )
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()
        
        # Create filename
        filename = f"Church_Orders_{church}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Upload to Cloudinary (backup)
        cloudinary_url = upload_pdf_to_cloudinary(pdf_bytes, filename)
        
        # CRITICAL: Return PDF for download to user's device
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        if cloudinary_url:
            response['X-Cloudinary-URL'] = cloudinary_url
        
        logger.info(f"Generated Church PDF for {church}, Cloudinary: {cloudinary_url}")
        
        return response


@method_decorator(staff_member_required, name='dispatch')
class AvailableStatesView(View):
    """
    Get list of states/churches that have orders
    Returns JSON for dynamic filtering
    """
    
    def get(self, request):
        """Get available filter options"""
        
        # Get states with NYSC Kit orders
        kit_states = NyscKitOrder.objects.filter(
            paid=True
        ).values_list('state', flat=True).distinct().order_by('state')
        
        # Get states with NYSC Tour orders (through products)
        tour_type = ContentType.objects.get_for_model(NyscTour)
        tour_product_ids = OrderItem.objects.filter(
            order__paid=True,
            content_type=tour_type
        ).values_list('object_id', flat=True).distinct()
        
        tour_states = NyscTour.objects.filter(
            id__in=tour_product_ids
        ).values_list('name', flat=True).distinct().order_by('name')
        
        # Get churches with orders
        church_type = ContentType.objects.get_for_model(Church)
        church_product_ids = OrderItem.objects.filter(
            order__paid=True,
            content_type=church_type
        ).values_list('object_id', flat=True).distinct()
        
        churches = Church.objects.filter(
            id__in=church_product_ids
        ).values_list('church', flat=True).distinct().order_by('church')
        
        return JsonResponse({
            'nysc_kit_states': list(kit_states),
            'nysc_tour_states': list(tour_states),
            'churches': list(churches)
        })