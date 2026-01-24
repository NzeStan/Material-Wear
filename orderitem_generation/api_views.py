# orderitem_generation/api_views.py
"""
PDF Generation Views with Generation Tracking - CORRECTED VERSION

✅ Uses ACTUAL model fields:
- NyscKitOrder: call_up_number, state, local_government (NO pickup fields!)
- ChurchOrder: pickup_on_camp, delivery_state, delivery_lga
- Template names: nysckit_state_template.html, church_state_template.html
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

from order.models import NyscKitOrder, OrderItem, BaseOrder
from products.models import NyscTour, Church
from measurement.models import Measurement

logger = logging.getLogger(__name__)


def upload_pdf_to_cloudinary(pdf_bytes, filename, pdf_category='general'):
    """
    Upload PDF to Cloudinary in organized directories
    
    Args:
        pdf_bytes: PDF binary content
        filename: Name of the file
        pdf_category: Category of PDF - 'nysc_kit', 'nysc_tour', 'church', or 'general'
        
    Returns:
        str: Cloudinary secure URL or None on failure
    """
    try:
        # ✅ FIXED: Organize PDFs into subdirectories based on category
        folder_map = {
            'nysc_kit': 'order_pdfs/nysc_kit',
            'nysc_tour': 'order_pdfs/nysc_tour',
            'church': 'order_pdfs/church',
            'general': 'order_pdfs/general'
        }
        
        folder = folder_map.get(pdf_category, 'order_pdfs/general')
        
        upload_result = cloudinary.uploader.upload(
            pdf_bytes,
            resource_type="raw",
            folder=folder,  # ✅ FIXED: Organized subdirectories
            public_id=filename.replace('.pdf', ''),
            format="pdf",
            overwrite=True
        )
        
        logger.info(f"PDF uploaded to Cloudinary ({pdf_category}): {upload_result.get('secure_url')}")
        return upload_result.get('secure_url')
        
    except Exception as e:
        logger.error(f"Failed to upload PDF to Cloudinary ({pdf_category}): {e}")
        return None



@method_decorator(staff_member_required, name='dispatch')
class NyscKitPDFView(View):
    """
    Generate PDF report for NYSC Kit orders by state
    ✅ Now tracks generated orders to prevent duplicates
    """
    
    def get(self, request):
        state = request.GET.get('state')
        regenerate = request.GET.get('regenerate', 'false').lower() == 'true'
        
        if not state:
            return JsonResponse({
                'error': 'State parameter is required'
            }, status=400)
        
        # ✅ FIXED: Only get paid orders that haven't been generated
        kit_orders_query = NyscKitOrder.objects.select_related().filter(
            state=state,
            paid=True
        )
        
        # Filter based on regenerate flag
        if not regenerate:
            kit_orders_query = kit_orders_query.filter(items_generated=False)
        
        kit_orders = kit_orders_query.order_by('created')
        
        if not kit_orders.exists():
            message = f'No {"ungenerated" if not regenerate else ""} paid orders found for {state}'
            return JsonResponse({'error': message}, status=404)
        
        # Separate orders by product type
        kakhi_orders = []
        vest_orders = []
        cap_orders = []
        
        kakhi_counter = 1
        vest_counter = 1
        cap_counter = 1
        
        # For summary calculations
        lga_summary = defaultdict(lambda: {'count': 0, 'quantity': 0, 'product': '', 'size': '', 'lga': ''})
        product_summary = defaultdict(lambda: {'count': 0, 'quantity': 0, 'product': '', 'size': ''})
        
        for order in kit_orders:
            full_name = f"{order.last_name} {order.middle_name} {order.first_name}".strip().upper()
            
            for item in order.items.all():
                if not item.product:
                    continue
                
                product_type = item.product.type
                product_name = item.product.name
                size = item.extra_fields.get('size', 'N/A')
                lga = order.local_government  # ✅ CORRECT: NyscKitOrder field
                quantity = item.quantity
                
                # Build summary key
                summary_key = f"{product_name}|{size}"
                lga_key = f"{product_name}|{size}|{lga}"
                
                # Update summaries
                lga_summary[lga_key]['count'] += 1
                lga_summary[lga_key]['quantity'] += quantity
                lga_summary[lga_key]['product'] = product_name
                lga_summary[lga_key]['size'] = size
                lga_summary[lga_key]['lga'] = lga
                
                product_summary[summary_key]['count'] += 1
                product_summary[summary_key]['quantity'] += quantity
                product_summary[summary_key]['product'] = product_name
                product_summary[summary_key]['size'] = size
                
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
                            pass
                    
                    kakhi_orders.append({
                        'sn': kakhi_counter,
                        'full_name': full_name,
                        'call_up_number': order.call_up_number,  # ✅ CORRECT: NyscKitOrder field
                        'lga': lga,
                        'product': product_name,
                        'size': size,
                        'quantity': quantity,
                        'measurement': measurement,
                    })
                    kakhi_counter += 1
                    
                elif product_type == 'vest':
                    vest_orders.append({
                        'sn': vest_counter,
                        'full_name': full_name,
                        'call_up_number': order.call_up_number,  # ✅ CORRECT: NyscKitOrder field
                        'lga': lga,
                        'product': product_name,
                        'size': size,
                        'quantity': quantity,
                    })
                    vest_counter += 1
                    
                elif product_type == 'cap':
                    cap_orders.append({
                        'sn': cap_counter,
                        'full_name': full_name,
                        'call_up_number': order.call_up_number,  # ✅ CORRECT: NyscKitOrder field
                        'lga': lga,
                        'product': product_name,
                        'size': size,
                        'quantity': quantity,
                    })
                    cap_counter += 1
        
        # Sort summaries
        lga_summary_list = sorted(
            [
                {
                    'product': v['product'],
                    'size': v['size'],
                    'count': v['count'],
                    'quantity': v['quantity'],
                    'lga': v['lga']
                }
                for v in lga_summary.values()
            ],
            key=lambda x: (x['product'], x['size'], x['lga'])
        )
        
        product_summary_list = sorted(
            [
                {
                    'product': v['product'],
                    'size': v['size'],
                    'count': v['count'],
                    'quantity': v['quantity']
                }
                for v in product_summary.values()
            ],
            key=lambda x: (x['product'], x['size'])
        )
        
        # Calculate grand totals
        grand_total_count = sum(item['count'] for item in product_summary_list)
        grand_total_quantity = sum(item['quantity'] for item in product_summary_list)
        
        # Render template
        context = {
            'state': state,
            'kakhi_orders': kakhi_orders,
            'vest_orders': vest_orders,
            'cap_orders': cap_orders,
            'total_kakhis': len(kakhi_orders),
            'total_vests': len(vest_orders),
            'total_caps': len(cap_orders),
            'lga_summary': lga_summary_list,
            'product_summary': product_summary_list,
            'grand_total_count': grand_total_count,
            'grand_total_quantity': grand_total_quantity,
        }
        
        html_string = render_to_string(
            'orderitem_generation/nysckit_state_template.html',  # ✅ CORRECT template name
            context
        )
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()
        
        # Create filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"NYSC_Kit_Orders_{state}_{timestamp}.pdf"
        
        # Upload to Cloudinary (backup)
        cloudinary_url = upload_pdf_to_cloudinary(pdf_bytes, filename)
        
        # ✅ CRITICAL: Mark orders as generated
        kit_orders.update(
            items_generated=True,
            generated_at=timezone.now(),
            generated_by=request.user
        )
        
        logger.info(
            f"Generated NYSC Kit PDF for {state}: {kit_orders.count()} orders marked as generated "
            f"by {request.user.username}, Cloudinary: {cloudinary_url}"
        )
        
        # Return PDF for download
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        if cloudinary_url:
            response['X-Cloudinary-URL'] = cloudinary_url
        
        return response


@method_decorator(staff_member_required, name='dispatch')
class NyscTourPDFView(View):
    """
    Generate PDF report for NYSC Tour orders by state
    ✅ Now tracks generated orders to prevent duplicates
    """
    
    def get(self, request):
        state = request.GET.get('state')
        regenerate = request.GET.get('regenerate', 'false').lower() == 'true'
        
        if not state:
            return JsonResponse({
                'error': 'State parameter is required'
            }, status=400)
        
        # Get ContentType for NyscTour
        tour_type = ContentType.objects.get_for_model(NyscTour)
        
        # Get tour products for this state
        tour_products = NyscTour.objects.filter(name=state).values_list('id', flat=True)
        
        if not tour_products:
            return JsonResponse({
                'error': f'No tour products found for {state}'
            }, status=404)
        
        # ✅ FIXED: Get order items with generation tracking
        order_items_query = OrderItem.objects.select_related(
            'order', 'content_type'
        ).filter(
            order__paid=True,
            content_type=tour_type,
            object_id__in=tour_products
        )
        
        # Filter based on regenerate flag
        if not regenerate:
            order_items_query = order_items_query.filter(order__items_generated=False)
        
        order_items = order_items_query.order_by('order__created')
        
        if not order_items.exists():
            message = f'No {"ungenerated" if not regenerate else ""} paid orders found for {state}'
            return JsonResponse({'error': message}, status=404)
        
        # Build data for template
        tour_orders = []
        total_participants = 0
        counter = 1
        processed_order_ids = set()
        
        for order_item in order_items:
            if not order_item.product:
                continue
                
            order = order_item.order
            processed_order_ids.add(order.id)
            
            full_name = f"{order.last_name} {order.middle_name} {order.first_name}".strip().upper()
            call_up_number = order_item.extra_fields.get('call_up_number', 'N/A')
            
            tour_orders.append({
                'sn': counter,
                'full_name': full_name,
                'call_up_number': call_up_number,
            })
            
            total_participants += order_item.quantity
            counter += 1
        
        # Render template
        context = {
            'state': state,
            'tour_orders': tour_orders,
            'total_orders': len(tour_orders),
            'total_participants': total_participants,
        }
        
        html_string = render_to_string(
            'orderitem_generation/nysctour_state_template.html',  # ✅ CORRECT template name
            context
        )
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()
        
        # Create filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"NYSC_Tour_Orders_{state}_{timestamp}.pdf"
        
        # Upload to Cloudinary (backup)
        cloudinary_url = upload_pdf_to_cloudinary(pdf_bytes, filename)
        
        # ✅ CRITICAL: Mark orders as generated
        BaseOrder.objects.filter(id__in=processed_order_ids).update(
            items_generated=True,
            generated_at=timezone.now(),
            generated_by=request.user
        )
        
        logger.info(
            f"Generated NYSC Tour PDF for {state}: {len(processed_order_ids)} orders marked as generated "
            f"by {request.user.username}, Cloudinary: {cloudinary_url}"
        )
        
        # Return PDF for download
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        if cloudinary_url:
            response['X-Cloudinary-URL'] = cloudinary_url
        
        return response


@method_decorator(staff_member_required, name='dispatch')
class ChurchPDFView(View):
    """
    Generate PDF report for Church orders by church type
    ✅ Now tracks generated orders to prevent duplicates
    """
    
    def get(self, request):
        church = request.GET.get('church')
        regenerate = request.GET.get('regenerate', 'false').lower() == 'true'
        
        if not church:
            return JsonResponse({
                'error': 'Church parameter is required'
            }, status=400)
        
        # Get ContentType for Church
        church_type = ContentType.objects.get_for_model(Church)
        church_ids = Church.objects.filter(church=church).values_list('id', flat=True)
        
        # ✅ FIXED: Get order items with generation tracking
        order_items_query = OrderItem.objects.select_related(
            'order', 'content_type'
        ).filter(
            order__paid=True,
            content_type=church_type,
            object_id__in=church_ids
        )
        
        # Filter based on regenerate flag
        if not regenerate:
            order_items_query = order_items_query.filter(order__items_generated=False)
        
        order_items = order_items_query.order_by('order__created')
        
        if not order_items.exists():
            message = f'No {"ungenerated" if not regenerate else ""} paid orders found for {church}'
            return JsonResponse({'error': message}, status=404)
        
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
        processed_order_ids = set()
        
        for order_item in order_items:
            if not order_item.product:
                continue
            
            order = order_item.order
            processed_order_ids.add(order.id)
            
            # ✅ CORRECT: Cast to ChurchOrder to access pickup fields
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
                'pickup_on_camp': church_order.pickup_on_camp,  # ✅ CORRECT: ChurchOrder field
                'delivery_state': church_order.delivery_state or '',  # ✅ CORRECT: ChurchOrder field
                'delivery_lga': church_order.delivery_lga or '',  # ✅ CORRECT: ChurchOrder field
            })
            
            # Track summary
            key = f"{product_name}_{size}"
            summary_data[key]['product_name'] = product_name
            summary_data[key]['size'] = size
            summary_data[key]['total_quantity'] += order_item.quantity
            
            if church_order.pickup_on_camp:
                summary_data[key]['pickup_count'] += order_item.quantity
            else:
                summary_data[key]['delivery_count'] += order_item.quantity
            
            # Group custom names
            if custom_name:
                sizes_grouping[size].append({
                    'full_name': full_name,
                    'custom_name': custom_name,
                    'product': product_name,
                    'quantity': order_item.quantity,
                })
            
            counter += 1
        
        # Sort custom names
        for size in sizes_grouping:
            sizes_grouping[size] = sorted(sizes_grouping[size], key=lambda x: x['product'])
        
        # Render template
        context = {
            'church': church,
            'orders': orders_data,
            'summary': list(summary_data.values()),
            'sizes_grouping': dict(sizes_grouping),
            'total_orders': len(orders_data)
        }
        
        html_string = render_to_string(
            'orderitem_generation/church_state_template.html',  # ✅ CORRECT template name
            context
        )
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()
        
        # Create filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Church_Orders_{church}_{timestamp}.pdf"
        
        # Upload to Cloudinary (backup)
        cloudinary_url = upload_pdf_to_cloudinary(pdf_bytes, filename)
        
        # ✅ CRITICAL: Mark orders as generated
        BaseOrder.objects.filter(id__in=processed_order_ids).update(
            items_generated=True,
            generated_at=timezone.now(),
            generated_by=request.user
        )
        
        logger.info(
            f"Generated Church PDF for {church}: {len(processed_order_ids)} orders marked as generated "
            f"by {request.user.username}, Cloudinary: {cloudinary_url}"
        )
        
        # Return PDF for download
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        if cloudinary_url:
            response['X-Cloudinary-URL'] = cloudinary_url
        
        return response


@method_decorator(staff_member_required, name='dispatch')
class AvailableStatesView(View):
    """
    Get list of states/churches that have UNGENERATED orders
    Returns JSON for dynamic filtering
    """
    
    def get(self, request):
        """Get available filter options for ungenerated orders"""
        
        # Get states with UNGENERATED NYSC Kit orders
        kit_states = NyscKitOrder.objects.filter(
            paid=True,
            items_generated=False  # ✅ Only ungenerated
        ).values_list('state', flat=True).distinct().order_by('state')
        
        # Get states with UNGENERATED NYSC Tour orders
        tour_type = ContentType.objects.get_for_model(NyscTour)
        tour_product_ids = OrderItem.objects.filter(
            order__paid=True,
            order__items_generated=False,  # ✅ Only ungenerated
            content_type=tour_type
        ).values_list('object_id', flat=True).distinct()
        
        tour_states = NyscTour.objects.filter(
            id__in=tour_product_ids
        ).values_list('name', flat=True).distinct().order_by('name')
        
        # Get churches with UNGENERATED orders
        church_type = ContentType.objects.get_for_model(Church)
        church_product_ids = OrderItem.objects.filter(
            order__paid=True,
            order__items_generated=False,  # ✅ Only ungenerated
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