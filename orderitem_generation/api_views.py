# orderitem_generation/api_views.py
"""
Views for generating order PDFs by state/church
Handles NYSC Kit, NYSC Tour, and Church orders with proper measurement handling

FIXED: 
- Converted from DRF APIView to Django View
- Fixed query logic to use correct model fields
- Fixed template names to match actual template files
"""
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.db.models import Count, Sum, Q
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from weasyprint import HTML
from order.models import OrderItem, NyscKitOrder, NyscTourOrder, ChurchOrder
from measurement.models import Measurement
from products.models import NyscKit, NyscTour, Church
from products.constants import STATES, CHURCH_CHOICES
from collections import defaultdict
import logging
import cloudinary
import cloudinary.uploader
from django.utils import timezone

logger = logging.getLogger(__name__)


def upload_pdf_to_cloudinary(pdf_bytes, filename):
    """
    Upload PDF to Cloudinary for backup/storage
    
    Args:
        pdf_bytes: PDF content as bytes
        filename: Desired filename
        
    Returns:
        str: Cloudinary URL or None if upload fails
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


@method_decorator(staff_member_required, name='dispatch')
class NyscKitPDFView(View):
    """
    Generate PDF report for NYSC Kit orders by state
    Separates orders into Kakhi (with measurements), Vest, and Cap sections
    """
    
    def get(self, request):
        state = request.GET.get('state')
        
        if not state:
            return JsonResponse({
                'error': 'State parameter is required'
            }, status=400)
        
        # Query NyscKitOrder by state
        kit_orders = NyscKitOrder.objects.filter(
            paid=True,
            state=state
        ).select_related('baseorder_ptr').prefetch_related(
            'baseorder_ptr__items',
            'baseorder_ptr__items__content_type'
        )
        
        if not kit_orders.exists():
            return JsonResponse({
                'error': f'No paid orders found for {state}'
            }, status=404)
        
        # Get ContentType for NyscKit
        kit_type = ContentType.objects.get_for_model(NyscKit)
        
        # ✅ SEPARATE LISTS FOR EACH PRODUCT TYPE
        kakhi_orders = []
        vest_orders = []
        cap_orders = []
        
        kakhi_counter = 1
        vest_counter = 1
        cap_counter = 1
        
        for kit_order in kit_orders:
            base_order = kit_order.baseorder_ptr
            
            # Get order items for NyscKit products only
            order_items = base_order.items.filter(content_type=kit_type)
            
            for order_item in order_items:
                if not order_item.product:
                    continue
                
                # Get product type
                product = order_item.product
                product_type = product.type.lower()  # 'kakhi', 'vest', or 'cap'
                
                full_name = f"{base_order.last_name} {base_order.middle_name} {base_order.first_name}".strip().upper()
                
                # Base order data (common to all types)
                order_data = {
                    'full_name': full_name,
                    'call_up_number': kit_order.call_up_number,
                    'lga': kit_order.local_government,  # Template uses 'lga'
                    'product': product.name,
                    'quantity': order_item.quantity,
                }
                
                # ✅ SEPARATE BY PRODUCT TYPE
                if product_type == 'kakhi':
                    # Kakhi has measurements
                    measurement = None
                    try:
                        measurement = Measurement.objects.get(
                            user=base_order.user,
                            id=order_item.extra_fields.get('measurement_id')
                        )
                    except Measurement.DoesNotExist:
                        pass
                    
                    order_data.update({
                        'sn': kakhi_counter,
                        'measurement': measurement,
                    })
                    kakhi_orders.append(order_data)
                    kakhi_counter += 1
                    
                elif product_type == 'vest':
                    # Vest has size
                    order_data.update({
                        'sn': vest_counter,
                        'size': order_item.extra_fields.get('size', 'N/A'),
                    })
                    vest_orders.append(order_data)
                    vest_counter += 1
                    
                elif product_type == 'cap':
                    # Cap has size (usually "free size")
                    order_data.update({
                        'sn': cap_counter,
                        'size': order_item.extra_fields.get('size', 'Free Size'),
                    })
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
            
            tour_orders.append({
                'sn': counter,
                'full_name': full_name,
                'email': order.email,
                'phone': order.phone_number,
                'product': order_item.product.name,
                'quantity': order_item.quantity,
                'amount': order_item.price * order_item.quantity
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
            'order', 'content_type', 'order__churchorder'
        ).filter(
            order__paid=True,
            content_type=church_type,
            object_id__in=church_ids
        )
        
        if not order_items.exists():
            return JsonResponse({
                'error': f'No paid orders found for {church}'
            }, status=404)
        
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
            
            # Determine delivery method
            delivery_method = 'Pickup on Camp' if church_order.pickup_on_camp else f"{church_order.delivery_state}, {church_order.delivery_lga}"
            
            order_data = {
                'sn': counter,
                'full_name': full_name,
                'phone': order.phone_number,
                'email': order.email,
                'product': order_item.product.name,
                'size': size,
                'custom_name': custom_name,
                'quantity': order_item.quantity,
                'delivery': delivery_method,
                'pickup_on_camp': church_order.pickup_on_camp,
                'delivery_state': church_order.delivery_state if not church_order.pickup_on_camp else '',
                'delivery_lga': church_order.delivery_lga if not church_order.pickup_on_camp else '',
                'amount': order_item.price * order_item.quantity
            }
            
            orders_data.append(order_data)
            
            # Update summary
            key = f"{order_item.product.name}_{size}"
            summary_data[key]['product_name'] = order_item.product.name
            summary_data[key]['size'] = size
            summary_data[key]['total_quantity'] += order_item.quantity
            
            if church_order.pickup_on_camp:
                summary_data[key]['pickup_count'] += order_item.quantity
            else:
                summary_data[key]['delivery_count'] += order_item.quantity
            
            # Group by size for aggregation
            if custom_name:  # Only include if there's a custom name
                sizes_grouping[size].append({
                    'full_name': full_name,
                    'custom_name': custom_name,
                    'product': order_item.product.name,
                    'quantity': order_item.quantity
                })
            
            counter += 1
        
        # Render template (use correct template name!)
        context = {
            'church': church,
            'orders': orders_data,  # Changed from 'orders_data' to 'orders' to match template
            'summary': list(summary_data.values()),  # Changed from 'summary_data' to 'summary'
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