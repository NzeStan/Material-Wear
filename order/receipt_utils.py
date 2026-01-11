# order/receipt_utils.py
"""
Receipt generation utilities with two-receipt system:
1. Order Confirmation Receipt - Sent after order creation (payment pending)
2. Payment Receipt - Sent after successful payment
"""
from weasyprint import HTML
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import cloudinary
import cloudinary.uploader
import logging
import io

logger = logging.getLogger(__name__)


def upload_pdf_to_cloudinary(pdf_content, filename):
    """
    Upload PDF to Cloudinary and return URL
    
    Args:
        pdf_content: PDF bytes
        filename: Name for the PDF file
        
    Returns:
        str: Cloudinary URL or None if upload fails
    """
    try:
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            pdf_content,
            resource_type='raw',
            public_id=f'receipts/{filename}',
            folder='jmw_receipts',
            overwrite=True,
            invalidate=True
        )
        
        logger.info(f"PDF uploaded to Cloudinary: {result['secure_url']}")
        return result['secure_url']
        
    except Exception as e:
        logger.error(f"Failed to upload PDF to Cloudinary: {str(e)}")
        return None


def generate_order_confirmation_pdf(order):
    """
    Generate Order Confirmation PDF (sent after order creation, payment pending)
    
    Args:
        order: Order instance (BaseOrder subclass)
        
    Returns:
        bytes: PDF content
    """
    try:
        context = {
            'order': order,
            'company_name': settings.COMPANY_NAME,
            'company_logo': settings.COMPANY_LOGO_URL,
            'company_email': settings.COMPANY_EMAIL,
            'company_phone': settings.COMPANY_PHONE,
            'company_address': settings.COMPANY_ADDRESS,
            'generated_date': timezone.now(),
            'primary_color': '#064E3B',
            'background_color': '#FFFBEB',
            'accent_color': '#F59E0B',
            'text_color': '#1F2937',
            'receipt_type': 'ORDER_CONFIRMATION',
        }
        
        # Render template
        html_string = render_to_string('order/order_confirmation_pdf.html', context)
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()
        
        logger.info(f"Order confirmation PDF generated for order: {order.serial_number}")
        
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"Error generating order confirmation PDF: {str(e)}")
        raise


def generate_payment_receipt_pdf(payment):
    """
    Generate Payment Receipt PDF (sent after successful payment)
    
    Args:
        payment: PaymentTransaction instance
        
    Returns:
        bytes: PDF content
    """
    try:
        # Get all orders for this payment
        orders = payment.orders.prefetch_related('items', 'items__content_type').all()
        
        context = {
            'payment': payment,
            'orders': orders,
            'company_name': settings.COMPANY_NAME,
            'company_logo': settings.COMPANY_LOGO_URL,
            'company_email': settings.COMPANY_EMAIL,
            'company_phone': settings.COMPANY_PHONE,
            'company_address': settings.COMPANY_ADDRESS,
            'generated_date': timezone.now(),
            'primary_color': '#064E3B',
            'background_color': '#FFFBEB',
            'accent_color': '#F59E0B',
            'text_color': '#1F2937',
            'receipt_type': 'PAYMENT_RECEIPT',
            'currency_symbol': '₦',
        }
        
        # Render template
        html_string = render_to_string('order/payment_receipt_pdf.html', context)
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()
        
        logger.info(f"Payment receipt PDF generated for payment: {payment.reference}")
        
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"Error generating payment receipt PDF: {str(e)}")
        raise


def generate_and_store_order_confirmation(order):
    """
    Generate order confirmation PDF and store in Cloudinary
    
    Args:
        order: Order instance
        
    Returns:
        tuple: (pdf_bytes, cloudinary_url)
    """
    try:
        # Generate PDF
        pdf_bytes = generate_order_confirmation_pdf(order)
        
        # Create filename
        filename = f"order_confirmation_{order.serial_number}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Upload to Cloudinary
        cloudinary_url = upload_pdf_to_cloudinary(pdf_bytes, filename)
        
        return (pdf_bytes, cloudinary_url)
        
    except Exception as e:
        logger.error(f"Error in generate_and_store_order_confirmation: {str(e)}")
        # Return PDF even if Cloudinary upload fails
        return (generate_order_confirmation_pdf(order), None)


def generate_and_store_payment_receipt(payment):
    """
    Generate payment receipt PDF and store in Cloudinary
    
    Args:
        payment: PaymentTransaction instance
        
    Returns:
        tuple: (pdf_bytes, cloudinary_url)
    """
    try:
        # Generate PDF
        pdf_bytes = generate_payment_receipt_pdf(payment)
        
        # Create filename
        filename = f"payment_receipt_{payment.reference}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Upload to Cloudinary
        cloudinary_url = upload_pdf_to_cloudinary(pdf_bytes, filename)
        
        return (pdf_bytes, cloudinary_url)
        
    except Exception as e:
        logger.error(f"Error in generate_and_store_payment_receipt: {str(e)}")
        # Return PDF even if Cloudinary upload fails
        return (generate_payment_receipt_pdf(payment), None)