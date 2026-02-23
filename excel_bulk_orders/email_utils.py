# excel_bulk_orders/email_utils.py
"""
Email utilities for Excel Bulk Orders.
Handles styled HTML email sending with project branding.
"""
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from material.background_utils import send_email_async
import logging

logger = logging.getLogger(__name__)


def send_bulk_order_confirmation_email(bulk_order, participants_count):
    """
    Send styled confirmation email to coordinator after successful payment.

    Args:
        bulk_order: ExcelBulkOrder instance
        participants_count: Number of participants created
    """
    try:
        # Prepare context for email template
        context = {
            "bulk_order": bulk_order,
            "coordinator_name": bulk_order.coordinator_name,
            "participants_count": participants_count,
            "amount_paid": f"{bulk_order.total_amount:,.2f}",
            "payment_date": timezone.now().strftime("%B %d, %Y at %I:%M %p"),
            "company_name": settings.COMPANY_NAME,
            "company_email": settings.COMPANY_EMAIL,
        }

        # Render HTML template
        html_message = render_to_string(
            "excel_bulk_orders/emails/bulk_order_confirmation.html", context
        )

        # Plain text fallback
        plain_message = f"""
Dear {bulk_order.coordinator_name},

Thank you for your payment!

Order Details:
- Reference: {bulk_order.reference}
- Campaign: {bulk_order.title}
- Participants: {participants_count}
- Amount Paid: ₦{bulk_order.total_amount:,.2f}

Your order has been successfully processed.

Best regards,
{settings.COMPANY_NAME}
{settings.COMPANY_EMAIL}
        """.strip()

        # Email subject
        subject = f"Payment Confirmed - {bulk_order.title} ({bulk_order.reference})"

        # Send email
        send_email_async(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[bulk_order.coordinator_email],
        )

        logger.info(
            f"Confirmation email sent to {bulk_order.coordinator_email} "
            f"for order {bulk_order.reference}"
        )

    except Exception as e:
        logger.error(
            f"Failed to send confirmation email for {bulk_order.reference}: {str(e)}"
        )
