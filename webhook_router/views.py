# webhook_router/views.py
# UPDATE THIS SECTION

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.views.decorators.http import require_POST
import json
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def router_webhook(request):
    """
    Universal webhook router for Paystack webhooks
    Routes to appropriate handler based on reference format
    
    Reference formats:
    - Bulk orders: "ORDER-{bulk_order_id}-{order_entry_id}"
    - Excel bulk orders: "EXL-{unique_code}"  ← NEW
    - Regular orders: "{uuid}"
    """
    try:
        payload = json.loads(request.body)
        logger.info(f"Webhook received: {payload.get('event')}")
        
        # Only process successful charges
        if payload.get('event') != 'charge.success':
            logger.info(f"Ignoring event: {payload.get('event')}")
            return HttpResponse(status=200)
        
        data = payload.get('data', {})
        reference = data.get('reference', '')
        
        if not reference:
            logger.error("No reference in webhook payload")
            return HttpResponse(status=400)
        
        # Route based on reference format
        if reference.startswith('ORDER-'):
            # Bulk order webhook
            logger.info(f"Routing to bulk order webhook: {reference}")
            from bulk_orders.views import bulk_order_payment_webhook
            return bulk_order_payment_webhook(request)
        elif reference.startswith('EXL-'):
            # Excel bulk order webhook  ← NEW SECTION
            logger.info(f"Routing to excel bulk order webhook: {reference}")
            from excel_bulk_orders.views import excel_bulk_order_payment_webhook
            return excel_bulk_order_payment_webhook(request)
        else:
            # Regular order webhook
            logger.info(f"Routing to regular order webhook: {reference}")
            from payment.api_views import payment_webhook
            return payment_webhook(request)
            
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return HttpResponse(status=400)
    except Exception as e:
        logger.exception("Error routing webhook")
        return HttpResponse(status=500)