# image_bulk_orders/utils.py
"""
Utility functions for Image Bulk Orders.
IDENTICAL to bulk_orders/utils.py with image downloading added.
"""
import string
import random
import logging
from django.utils import timezone
from django.template.loader import render_to_string
from django.conf import settings
from django.http import HttpResponse
from django.db.models import Count, Q, Prefetch
from io import BytesIO
import zipfile
import os
import tempfile
import requests
from pathlib import Path

from .models import ImageCouponCode, ImageBulkOrderLink, ImageOrderEntry

logger = logging.getLogger(__name__)


def generate_coupon_codes_image(bulk_order, count=10):
    """
    Generate unique coupon codes.
    IDENTICAL to bulk_orders version.
    """
    chars = string.ascii_uppercase + string.digits
    codes = []
    try:
        for _ in range(count):
            while True:
                code = "".join(random.choices(chars, k=8))
                if not ImageCouponCode.objects.filter(code=code).exists():
                    coupon = ImageCouponCode.objects.create(bulk_order=bulk_order, code=code)
                    codes.append(coupon)
                    break
        logger.info(f"Generated {count} coupon codes")
        return codes
    except Exception as e:
        logger.error(f"Error generating coupons: {str(e)}")
        raise


def _get_image_bulk_order_with_orders(bulk_order):
    """Helper to get bulk order with optimized prefetch"""
    if isinstance(bulk_order, str):
        return ImageBulkOrderLink.objects.prefetch_related(
            Prefetch(
                "orders",
                queryset=ImageOrderEntry.objects.select_related("coupon_used")
                .filter(Q(paid=True) | Q(coupon_used__isnull=False))
                .order_by("size", "full_name"),
            )
        ).get(slug=bulk_order)
    else:
        return ImageBulkOrderLink.objects.prefetch_related(
            Prefetch(
                "orders",
                queryset=ImageOrderEntry.objects.select_related("coupon_used")
                .filter(Q(paid=True) | Q(coupon_used__isnull=False))
                .order_by("size", "full_name"),
            )
        ).get(id=bulk_order.id)


def generate_image_bulk_order_pdf(bulk_order, request=None):
    """Generate PDF summary (IDENTICAL to bulk_orders)"""
    try:
        from weasyprint import HTML
        
        bulk_order = _get_image_bulk_order_with_orders(bulk_order)
        orders = bulk_order.orders.all()
        size_summary = orders.values("size").annotate(count=Count("size")).order_by("size")
        paid_orders = orders.filter(Q(paid=True) | Q(coupon_used__isnull=False))
        
        context = {
            'bulk_order': bulk_order,
            'size_summary': size_summary,
            'orders': orders,
            'paid_orders': paid_orders,
            'total_orders': orders.count(),
            'total_paid': paid_orders.count(),
            'company_name': settings.COMPANY_NAME,
            'company_address': settings.COMPANY_ADDRESS,
            'company_phone': settings.COMPANY_PHONE,
            'company_email': settings.COMPANY_EMAIL,
            'now': timezone.now(),
        }
        
        html_string = render_to_string('image_bulk_orders/pdf_template.html', context)
        
        if request:
            html = HTML(string=html_string, base_url=request.build_absolute_uri())
        else:
            html = HTML(string=html_string)
        
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f'image_bulk_order_{bulk_order.slug}_{timezone.now().strftime("%Y%m%d")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise


def generate_image_bulk_order_word(bulk_order):
    """Generate Word document (IDENTICAL to bulk_orders)"""
    try:
        from docx import Document
        
        bulk_order = _get_image_bulk_order_with_orders(bulk_order)
        doc = Document()
        
        doc.add_heading(settings.COMPANY_NAME, 0)
        doc.add_heading(f'Image Bulk Order: {bulk_order.organization_name}', level=1)
        doc.add_paragraph(f"Generated: {timezone.now().strftime('%B %d, %Y - %I:%M %p')}")
        doc.add_paragraph(f'Payment Deadline: {bulk_order.payment_deadline.strftime("%B %d, %Y")}')
        doc.add_paragraph('')
        
        orders = bulk_order.orders.all()
        size_summary = orders.values("size").annotate(total=Count("id")).order_by("size")
        
        doc.add_heading('Summary by Size', level=2)
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Light Grid Accent 1'
        header_cells = table.rows[0].cells
        header_cells[0].text = 'Size'
        header_cells[1].text = 'Total'
        
        for size_info in size_summary:
            row_cells = table.add_row().cells
            row_cells[0].text = size_info['size']
            row_cells[1].text = str(size_info['total'])
        
        doc.add_paragraph('')
        doc.add_heading('All Orders', level=2)
        
        table = doc.add_table(rows=1, cols=5 if bulk_order.custom_branding_enabled else 4)
        table.style = 'Light Grid Accent 1'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = '#'
        hdr_cells[1].text = 'Name'
        hdr_cells[2].text = 'Size'
        if bulk_order.custom_branding_enabled:
            hdr_cells[3].text = 'Custom Name'
            hdr_cells[4].text = 'Status'
        else:
            hdr_cells[3].text = 'Status'
        
        for order in orders:
            row_cells = table.add_row().cells
            row_cells[0].text = str(order.serial_number)
            row_cells[1].text = order.full_name
            row_cells[2].text = order.size
            
            if bulk_order.custom_branding_enabled:
                row_cells[3].text = order.custom_name or ''
                status = 'Paid' if order.paid else ('Coupon' if order.coupon_used else 'Pending')
                row_cells[4].text = status
            else:
                status = 'Paid' if order.paid else ('Coupon' if order.coupon_used else 'Pending')
                row_cells[3].text = status
        
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        filename = f'image_bulk_order_{bulk_order.slug}_{timezone.now().strftime("%Y%m%d")}.docx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating Word: {str(e)}")
        raise


def generate_image_bulk_order_excel(bulk_order):
    """Generate Excel spreadsheet (IDENTICAL to bulk_orders)"""
    try:
        import xlsxwriter
        
        bulk_order = _get_image_bulk_order_with_orders(bulk_order)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'constant_memory': True})
        
        # Formats
        title_format = workbook.add_format({'bold': True, 'font_size': 16})
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 'align': 'center'
        })
        cell_format = workbook.add_format({'border': 1, 'align': 'center'})
        
        worksheet = workbook.add_worksheet(bulk_order.organization_name[:31])
        
        row = 0
        worksheet.write(row, 0, settings.COMPANY_NAME, title_format)
        row += 2
        
        orders = bulk_order.orders.all()
        
        # Headers
        headers = ['#', 'Name', 'Email', 'Size', 'Custom Name' if bulk_order.custom_branding_enabled else None, 'Status']
        headers = [h for h in headers if h]
        
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, header_format)
        
        row += 1
        
        for order in orders:
            col = 0
            worksheet.write(row, col, order.serial_number, cell_format)
            col += 1
            worksheet.write(row, col, order.full_name, cell_format)
            col += 1
            worksheet.write(row, col, order.email, cell_format)
            col += 1
            worksheet.write(row, col, order.size, cell_format)
            col += 1
            
            if bulk_order.custom_branding_enabled:
                worksheet.write(row, col, order.custom_name or '', cell_format)
                col += 1
            
            status = 'Paid' if order.paid else ('Coupon' if order.coupon_used else 'Pending')
            worksheet.write(row, col, status, cell_format)
            row += 1
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        filename = f'image_bulk_order_{bulk_order.slug}_{timezone.now().strftime("%Y%m%d")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating Excel: {str(e)}")
        raise


def download_image_from_cloudinary(url):
    """Download image from Cloudinary URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Error downloading image from {url}: {str(e)}")
        return None


def generate_admin_package_with_images(bulk_order_id):
    """
    Generate complete admin package: PDF + Word + Excel + Images by size.
    
    Creates ZIP structure:
    /package_slug_20240212/
        bulk_order_slug.pdf
        bulk_order_slug.docx
        bulk_order_slug.xlsx
        /images/
            /S/
                001_John_Doe.jpg
                002_Jane_Smith.png
            /M/
                003_Bob_Wilson.jpg
            ...
    """
    try:
        bulk_order = ImageBulkOrderLink.objects.prefetch_related(
            'orders'
        ).get(id=bulk_order_id)
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_name = f"{bulk_order.slug}_{timezone.now().strftime('%Y%m%d')}"
            package_dir = temp_path / package_name
            package_dir.mkdir()
            
            # Generate documents
            pdf_response = generate_image_bulk_order_pdf(bulk_order)
            word_response = generate_image_bulk_order_word(bulk_order)
            excel_response = generate_image_bulk_order_excel(bulk_order)
            
            # Save documents
            (package_dir / f"{bulk_order.slug}.pdf").write_bytes(pdf_response.content)
            (package_dir / f"{bulk_order.slug}.docx").write_bytes(word_response.content)
            (package_dir / f"{bulk_order.slug}.xlsx").write_bytes(excel_response.content)
            
            # Create images directory structure
            images_dir = package_dir / "images"
            images_dir.mkdir()
            
            # Download and organize images by size
            orders_with_images = bulk_order.orders.filter(image__isnull=False)
            
            for order in orders_with_images:
                # Create size subdirectory
                size_dir = images_dir / order.size
                size_dir.mkdir(exist_ok=True)
                
                # Determine filename
                if order.custom_name:
                    filename_base = order.custom_name.replace(' ', '_')
                else:
                    filename_base = f"{order.serial_number}_{order.full_name.replace(' ', '_')}"
                
                # Get file extension from Cloudinary URL
                image_url = order.image.url
                ext = Path(image_url).suffix or '.jpg'
                filename = f"{filename_base}{ext}"
                
                # Download image
                image_data = download_image_from_cloudinary(image_url)
                if image_data:
                    (size_dir / filename).write_bytes(image_data)
                    logger.info(f"Downloaded image: {filename}")
            
            # Create ZIP
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in package_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(package_dir.parent)
                        zip_file.write(file_path, arcname)
            
            zip_buffer.seek(0)
            
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{package_name}.zip"'
            
            logger.info(f"Generated admin package with images for: {bulk_order.slug}")
            return response
            
    except Exception as e:
        logger.error(f"Error generating admin package: {str(e)}")
        raise
