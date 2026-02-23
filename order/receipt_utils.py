# order/receipt_utils.py
from weasyprint import HTML
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.utils.html import escape  # ✅ ADD THIS
import cloudinary
import cloudinary.uploader
import logging
import io
import re

logger = logging.getLogger(__name__)


def sanitize_text_for_pdf(text):
    """
    ✅ Sanitize user input for PDF generation

    Args:
        text: User-provided text

    Returns:
        str: Sanitized text safe for PDF
    """
    if not text:
        return ""

    # Convert to string if not already
    text = str(text)

    # HTML escape to prevent injection
    text = escape(text)

    # Remove any potentially dangerous characters
    # Keep only alphanumeric, spaces, and common punctuation
    text = re.sub(r"[^\w\s\-.,@()/]", "", text)

    # Limit length to prevent DoS
    max_length = 200
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def upload_pdf_to_cloudinary(pdf_content, filename, pdf_type="general"):
    """
    Upload PDF to Cloudinary in organized directories

    Args:
        pdf_content: PDF binary content
        filename: Name of the file
        pdf_type: Type of PDF - 'order_confirmation', 'payment_receipt', or 'general'

    Returns:
        str: Cloudinary secure URL or None on failure
    """
    try:
        # ✅ FIXED: Organize PDFs into subdirectories based on type
        folder_map = {
            "order_confirmation": "material_receipts/orders",
            "payment_receipt": "material_receipts/payments",
            "general": "material_receipts/general",
        }

        folder = folder_map.get(pdf_type, "material_receipts/general")

        result = cloudinary.uploader.upload(
            pdf_content,
            resource_type="raw",
            public_id=filename.replace(
                ".pdf", ""
            ),  # ✅ FIXED: No redundant path prefix
            folder=folder,  # ✅ FIXED: Organized subdirectories
            format="pdf",
            overwrite=True,
            invalidate=True,
        )

        logger.info(f"PDF uploaded to Cloudinary ({pdf_type}): {result['secure_url']}")
        return result["secure_url"]

    except Exception as e:
        logger.error(f"Failed to upload PDF to Cloudinary: {str(e)}")
        return None


def generate_order_confirmation_pdf(order):
    """
    ✅ SECURED: Generate Order Confirmation PDF with sanitized inputs
    """
    try:
        # ✅ Sanitize all user-provided data
        context = {
            "order": order,
            "first_name": sanitize_text_for_pdf(order.first_name),
            "middle_name": sanitize_text_for_pdf(order.middle_name),
            "last_name": sanitize_text_for_pdf(order.last_name),
            "email": sanitize_text_for_pdf(order.email),
            "phone_number": sanitize_text_for_pdf(order.phone_number),
            # Company info (from settings - trusted)
            "company_name": settings.COMPANY_NAME,
            "company_logo": settings.COMPANY_LOGO_URL,
            "company_email": settings.COMPANY_EMAIL,
            "company_phone": settings.COMPANY_PHONE,
            "company_address": settings.COMPANY_ADDRESS,
            # System data
            "generated_date": timezone.now(),
            "primary_color": "#064E3B",
            "background_color": "#FFFBEB",
            "accent_color": "#F59E0B",
            "text_color": "#1F2937",
        }

        # ✅ Sanitize order-specific fields based on type
        if hasattr(order, "call_up_number"):
            context["call_up_number"] = sanitize_text_for_pdf(order.call_up_number)
            context["state"] = sanitize_text_for_pdf(order.state)
            context["local_government"] = sanitize_text_for_pdf(order.local_government)

        if hasattr(order, "delivery_state"):
            context["delivery_state"] = sanitize_text_for_pdf(order.delivery_state)
            context["delivery_lga"] = sanitize_text_for_pdf(order.delivery_lga)

        # Render HTML template
        html_string = render_to_string("receipts/order_confirmation_pdf.html", context)

        # Generate PDF
        pdf_file = HTML(string=html_string).write_pdf()

        logger.info(f"Order confirmation PDF generated for order {order.serial_number}")
        return pdf_file

    except Exception as e:
        logger.error(f"Failed to generate order confirmation PDF: {str(e)}")
        return None


def generate_payment_receipt_pdf(payment):
    """
    ✅ SECURED: Generate Payment Receipt PDF with sanitized inputs
    """
    try:
        # Get first order for customer info
        first_order = payment.orders.first()

        if not first_order:
            logger.error(f"No orders found for payment {payment.reference}")
            return None

        # ✅ Sanitize all user-provided data
        context = {
            "payment": payment,
            "orders": payment.orders.all(),
            "first_name": sanitize_text_for_pdf(first_order.first_name),
            "middle_name": sanitize_text_for_pdf(first_order.middle_name),
            "last_name": sanitize_text_for_pdf(first_order.last_name),
            "email": sanitize_text_for_pdf(first_order.email),
            "phone_number": sanitize_text_for_pdf(first_order.phone_number),
            # Company info (from settings - trusted)
            "company_name": settings.COMPANY_NAME,
            "company_logo": settings.COMPANY_LOGO_URL,
            "company_email": settings.COMPANY_EMAIL,
            "company_phone": settings.COMPANY_PHONE,
            "company_address": settings.COMPANY_ADDRESS,
            # System data
            "generated_date": timezone.now(),
            "primary_color": "#064E3B",
            "background_color": "#FFFBEB",
            "accent_color": "#F59E0B",
            "text_color": "#1F2937",
        }

        # Render HTML template
        html_string = render_to_string("receipts/payment_receipt_pdf.html", context)

        # Generate PDF
        pdf_file = HTML(string=html_string).write_pdf()

        logger.info(f"Payment receipt PDF generated for payment {payment.reference}")
        return pdf_file

    except Exception as e:
        logger.error(f"Failed to generate payment receipt PDF: {str(e)}")
        return None


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

        # ✅ FIXED: Upload to Cloudinary with pdf_type parameter
        cloudinary_url = upload_pdf_to_cloudinary(
            pdf_bytes,
            filename,
            pdf_type="order_confirmation",  # ✅ NEW: Specify PDF type
        )

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

        # ✅ FIXED: Upload to Cloudinary with pdf_type parameter
        cloudinary_url = upload_pdf_to_cloudinary(
            pdf_bytes, filename, pdf_type="payment_receipt"  # ✅ NEW: Specify PDF type
        )

        return (pdf_bytes, cloudinary_url)

    except Exception as e:
        logger.error(f"Error in generate_and_store_payment_receipt: {str(e)}")
        # Return PDF even if Cloudinary upload fails
        return (generate_payment_receipt_pdf(payment), None)
