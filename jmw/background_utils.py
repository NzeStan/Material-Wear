# jmw/background_utils.py
"""
Centralized background task and email utilities
Uses threading for quick tasks and django-background-tasks for heavy operations
Enhanced with Cloudinary PDF storage before emailing
"""
from threading import Thread
from background_task import background
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# EMAIL UTILITIES (Using Threading for Quick Async)
# ============================================================================

def send_email_async(subject, message, from_email, recipient_list, attachments=None, html_message=None):
    """
    Send email asynchronously using threading.
    Use for quick email sends (confirmations, notifications).
    
    Args:
        subject: Email subject
        message: Plain text message
        from_email: Sender email
        recipient_list: List of recipient emails
        attachments: Optional list of (filename, content, mimetype) tuples
        html_message: Optional HTML version of message
    """
    def _send():
        try:
            if html_message:
                email = EmailMessage(subject, html_message, from_email, recipient_list)
                email.content_subtype = "html"
            else:
                email = EmailMessage(subject, message, from_email, recipient_list)
            
            if attachments:
                for filename, content, mimetype in attachments:
                    email.attach(filename, content, mimetype)
            
            email.send()
            logger.info(f"Email sent successfully: {subject} to {recipient_list}")
        except Exception as e:
            logger.error(f"Error sending email '{subject}' to {recipient_list}: {str(e)}")
    
    thread = Thread(target=_send)
    thread.daemon = True
    thread.start()
    logger.info(f"Email queued for async sending: {subject}")


# ============================================================================
# ORDER APP - EMAIL & PDF TASKS (Two-Receipt System)
# ============================================================================

def send_order_confirmation_email_async(order_id):
    """
    Send order confirmation email after order creation (payment pending).
    Uses threading for quick async delivery.
    
    Args:
        order_id: UUID of the order
    """
    def _send():
        try:
            from order.models import BaseOrder

            order = BaseOrder.objects.select_related('user').prefetch_related('items').get(id=order_id)

            context = {
                'order': order,
                'company_name': settings.COMPANY_NAME,
                'company_address': settings.COMPANY_ADDRESS,
                'company_phone': settings.COMPANY_PHONE,
                'company_email': settings.COMPANY_EMAIL,
                'currency_symbol': '₦',
                'primary_color': '#064E3B',
                'accent_color': '#F59E0B',
            }

            html_message = render_to_string('order/order_confirmation_email.html', context)

            subject = f'Order Confirmation - JMW Order #{order.serial_number}'

            email = EmailMessage(subject, html_message, settings.DEFAULT_FROM_EMAIL, [order.email])
            email.content_subtype = "html"
            email.send()

            logger.info(f"Order confirmation email sent for order: #{order.serial_number}")

        except Exception as e:
            logger.error(f"Error sending order confirmation email for order_id {order_id}: {str(e)}")

    thread = Thread(target=_send)
    thread.daemon = True
    thread.start()
    logger.info(f"Order confirmation email queued for order_id: {order_id}")


@background(schedule=0)
def generate_order_confirmation_pdf_task(order_id):
    """
    Generate order confirmation PDF in background, store in Cloudinary, and email to customer.
    Heavy task - uses django-background-tasks.
    
    Args:
        order_id: UUID of the order
    """
    try:
        from order.models import BaseOrder
        from order.receipt_utils import generate_and_store_order_confirmation

        order = BaseOrder.objects.select_related('user').prefetch_related(
            'items__content_type'
        ).get(id=order_id)

        # Generate PDF and store in Cloudinary
        pdf_bytes, cloudinary_url = generate_and_store_order_confirmation(order)

        filename = f'JMW_Order_Confirmation_{order.serial_number}.pdf'

        # Prepare email context
        context = {
            'order': order,
            'cloudinary_url': cloudinary_url,
            'company_name': settings.COMPANY_NAME,
        }

        html_message = render_to_string('order/order_confirmation_pdf_email.html', context)

        subject = f'Order Confirmation Receipt - JMW Order #{order.serial_number}'
        message = f"Your order confirmation receipt for Order #{order.serial_number} is attached."

        send_email_async(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            attachments=[(filename, pdf_bytes, 'application/pdf')]
        )

        logger.info(f"Order confirmation PDF generated and sent for order: #{order.serial_number}")

    except Exception as e:
        logger.error(f"Error generating order confirmation PDF for order_id {order_id}: {str(e)}")


def send_payment_receipt_email_async(payment_id):
    """
    Send payment receipt email after payment verification.
    Uses threading for quick async delivery.
    
    Args:
        payment_id: UUID of the payment transaction
    """
    def _send():
        try:
            from payment.models import PaymentTransaction

            payment = PaymentTransaction.objects.prefetch_related('orders').get(id=payment_id)

            context = {
                'payment': payment,
                'orders': payment.orders.all(),
                'company_name': settings.COMPANY_NAME,
                'company_address': settings.COMPANY_ADDRESS,
                'company_phone': settings.COMPANY_PHONE,
                'company_email': settings.COMPANY_EMAIL,
                'currency_symbol': '₦',
                'primary_color': '#064E3B',
                'accent_color': '#F59E0B',
            }

            html_message = render_to_string('order/payment_receipt_email.html', context)

            subject = f'Payment Receipt - {payment.reference}'

            email = EmailMessage(subject, html_message, settings.DEFAULT_FROM_EMAIL, [payment.email])
            email.content_subtype = "html"
            email.send()

            logger.info(f"Payment receipt email sent for payment: {payment.reference}")

        except Exception as e:
            logger.error(f"Error sending payment receipt email for payment_id {payment_id}: {str(e)}")

    thread = Thread(target=_send)
    thread.daemon = True
    thread.start()
    logger.info(f"Payment receipt email queued for payment_id: {payment_id}")


@background(schedule=0)
def generate_payment_receipt_pdf_task(payment_id):
    """
    Generate payment receipt PDF in background, store in Cloudinary, and email to customer.
    Heavy task - uses django-background-tasks.
    
    Args:
        payment_id: UUID of the payment transaction
    """
    try:
        from payment.models import PaymentTransaction
        from order.receipt_utils import generate_and_store_payment_receipt

        payment = PaymentTransaction.objects.prefetch_related(
            'orders',
            'orders__items__content_type'
        ).get(id=payment_id)

        # Generate PDF and store in Cloudinary
        pdf_bytes, cloudinary_url = generate_and_store_payment_receipt(payment)

        filename = f'JMW_Payment_Receipt_{payment.reference}.pdf'

        # Prepare email context
        context = {
            'payment': payment,
            'cloudinary_url': cloudinary_url,
            'company_name': settings.COMPANY_NAME,
        }

        html_message = render_to_string('order/payment_receipt_pdf_email.html', context)

        subject = f'Payment Receipt - {payment.reference}'
        message = f"Your payment receipt for {payment.reference} is attached."

        send_email_async(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.email],
            attachments=[(filename, pdf_bytes, 'application/pdf')]
        )

        logger.info(f"Payment receipt PDF generated and sent for payment: {payment.reference}")

    except Exception as e:
        logger.error(f"Error generating payment receipt PDF for payment_id {payment_id}: {str(e)}")


# ============================================================================
# BULK ORDERS APP - EMAIL & PDF TASKS (Existing - Already Good)
# ============================================================================

def send_order_confirmation_email(order_entry):
    """Send order confirmation email after bulk order creation"""
    context = {
        'order': order_entry,
        'bulk_order': order_entry.bulk_order,
        'company_name': settings.COMPANY_NAME,
    }
    
    html_message = render_to_string('bulk_orders/emails/order_confirmation.html', context)
    
    subject = f"Order Confirmation - {order_entry.bulk_order.organization_name}"
    
    send_email_async(
        subject=subject,
        message=f"Thank you for your order! Your order number is #{order_entry.serial_number}",
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order_entry.email]
    )


def send_payment_receipt_email(order_entry):
    """Send payment receipt email after successful bulk order payment"""
    context = {
        'order': order_entry,
        'bulk_order': order_entry.bulk_order,
        'company_name': settings.COMPANY_NAME,
        'company_address': settings.COMPANY_ADDRESS,
        'company_phone': settings.COMPANY_PHONE,
        'company_email': settings.COMPANY_EMAIL,
    }
    
    html_message = render_to_string('bulk_orders/emails/payment_receipt.html', context)
    
    subject = f"Payment Receipt - Order #{order_entry.serial_number}"
    
    send_email_async(
        subject=subject,
        message=f"Payment received for order #{order_entry.serial_number}",
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order_entry.email]
    )


@background(schedule=0)
def generate_bulk_order_pdf_task(bulk_order_id, recipient_email):
    """Generate bulk order PDF in background and email it"""
    try:
        from bulk_orders.models import BulkOrderLink
        from bulk_orders.utils import generate_bulk_order_pdf
        
        bulk_order = BulkOrderLink.objects.get(id=bulk_order_id)
        
        pdf = generate_bulk_order_pdf(bulk_order)
        
        subject = f"Bulk Order Report - {bulk_order.organization_name}"
        message = f"Your bulk order report for {bulk_order.organization_name} is attached."
        
        send_email_async(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            attachments=[
                (f'bulk_order_{bulk_order.slug}.pdf', pdf, 'application/pdf')
            ]
        )
        
        logger.info(f"Background PDF generation completed for bulk order: {bulk_order_id}")
        
    except Exception as e:
        logger.error(f"Error in background PDF generation: {str(e)}")


@background(schedule=0)
def generate_payment_receipt_pdf_task_bulk(order_entry_id):
    """Generate individual payment receipt PDF in background for bulk orders"""
    try:
        from bulk_orders.models import OrderEntry
        from weasyprint import HTML
        from django.utils import timezone
        
        order_entry = OrderEntry.objects.select_related('bulk_order', 'coupon_used').get(id=order_entry_id)
        
        context = {
            'order': order_entry,
            'bulk_order': order_entry.bulk_order,
            'company_name': settings.COMPANY_NAME,
            'company_address': settings.COMPANY_ADDRESS,
            'company_phone': settings.COMPANY_PHONE,
            'company_email': settings.COMPANY_EMAIL,
            'generated_date': timezone.now(),
        }
        
        html_string = render_to_string('bulk_orders/receipt_template.html', context)
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        
        # Send receipt email with PDF
        subject = f"Payment Receipt - Order #{order_entry.serial_number}"
        message = f"Thank you for your payment! Please find your receipt attached."
        
        send_email_async(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order_entry.email],
            attachments=[
                (f'receipt_{order_entry.serial_number}.pdf', pdf, 'application/pdf')
            ]
        )
        
        logger.info(f"Payment receipt PDF generated for order entry: {order_entry_id}")

    except Exception as e:
        logger.error(f"Error generating payment receipt PDF: {str(e)}")


