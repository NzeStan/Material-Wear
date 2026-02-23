# webhook_router/views.py
"""
Central webhook router for all payment callbacks.

Routes payment webhooks to appropriate app handlers based on reference format:
- MATERIAL-xxxx → payment.api_views.payment_webhook (regular orders)
- ORDER-xxx-xxx → bulk_orders.views.bulk_order_payment_webhook
- IMG-BULK-xxxx → image_bulk_orders.views.image_bulk_order_payment_webhook
- EXL-xxxx → excel_bulk_orders.views.excel_bulk_order_payment_webhook (FIXED)
"""
import json
import logging
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def router_webhook(request: HttpRequest):
    """
    Route webhooks to appropriate handler based on reference format.

    Reference formats:
    - MATERIAL-xxxx → Regular orders (payment app)
    - ORDER-xxx-xxx → Bulk orders
    - IMG-BULK-xxxx → Image bulk orders
    - EXL-xxxx → Excel bulk orders (FIXED import name)
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        # Parse webhook payload
        payload = json.loads(request.body)
        event = payload.get("event")

        if event != "charge.success":
            return JsonResponse({"status": "ignored"}, status=200)

        data = payload.get("data", {})
        reference = data.get("reference", "")

        logger.info(f"Router received webhook for reference: {reference}")

        # Route based on reference format
        if reference.startswith("IMG-BULK-"):
            # Image bulk orders
            from image_bulk_orders.views import image_bulk_order_payment_webhook

            return image_bulk_order_payment_webhook(request)

        elif reference.startswith("ORDER-"):
            # Regular bulk orders
            from bulk_orders.views import bulk_order_payment_webhook

            return bulk_order_payment_webhook(request)

        elif reference.startswith("EXL-"):
            # Excel bulk orders - FIXED: Use correct function name
            from excel_bulk_orders.views import excel_bulk_order_payment_webhook

            return excel_bulk_order_payment_webhook(request)

        elif reference.startswith("MATERIAL-"):
            # Regular payment app orders
            from payment.api_views import payment_webhook

            return payment_webhook(request)

        else:
            logger.error(f"Unknown reference format: {reference}")
            return JsonResponse({"error": "Unknown reference format"}, status=400)

    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    except Exception as e:
        logger.error(f"Webhook router error: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)
