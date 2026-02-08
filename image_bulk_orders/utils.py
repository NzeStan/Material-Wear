# image_bulk_orders/utils.py
"""
Utility functions for image bulk orders.

Key Features:
- Coupon code generation
- Document generation (PDF, Word, Excel)
- Image organization by size with custom naming
- ZIP archive creation with directory structure
- Cloudinary integration for uploads

Optimizations:
- Bulk operations where possible
- Efficient file handling
- Progress logging
- Error recovery
"""
import string
import random
import logging
import zipfile
import tempfile
import shutil
from pathlib import Path
from io import BytesIO
from typing import List, Dict, Optional
import requests

from django.utils import timezone
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Count, Q, Prefetch
from django.core.paginator import Paginator
from django.utils.text import slugify

import cloudinary.uploader
import xlsxwriter
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from weasyprint import HTML

from .models import ImageBulkOrderLink, ImageOrderEntry, ImageCouponCode

logger = logging.getLogger(__name__)


# ============================================================================
# COUPON CODE GENERATION
# ============================================================================

def generate_coupon_codes(bulk_order: ImageBulkOrderLink, count: int = 10) -> List[ImageCouponCode]:
    """
    Generate unique coupon codes for a bulk order.
    
    Args:
        bulk_order: ImageBulkOrderLink instance
        count: Number of coupons to generate
    
    Returns:
        List of ImageCouponCode instances
    
    Raises:
        Exception: If coupon generation fails
    """
    chars = string.ascii_uppercase + string.digits
    codes = []
    
    try:
        for _ in range(count):
            while True:
                code = ''.join(random.choices(chars, k=8))
                if not ImageCouponCode.objects.filter(code=code).exists():
                    coupon = ImageCouponCode.objects.create(
                        bulk_order=bulk_order,
                        code=code
                    )
                    codes.append(coupon)
                    break
        
        logger.info(f"Generated {count} coupon codes for image bulk order: {bulk_order.id}")
        return codes
        
    except Exception as e:
        logger.error(f"Error generating coupon codes: {str(e)}")
        raise


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_bulk_order_with_orders(bulk_order):
    """
    Helper to get bulk order with optimized prefetch.
    
    Args:
        bulk_order: Either ImageBulkOrderLink instance or slug string
    
    Returns:
        ImageBulkOrderLink instance with prefetched orders
    """
    if isinstance(bulk_order, str):
        # Fetch by slug
        return ImageBulkOrderLink.objects.prefetch_related(
            Prefetch(
                'orders',
                queryset=ImageOrderEntry.objects.select_related('coupon_used')
                .filter(paid=True)
                .order_by('size', 'full_name')
            )
        ).get(slug=bulk_order)
    else:
        # Refetch with proper prefetch
        return ImageBulkOrderLink.objects.prefetch_related(
            Prefetch(
                'orders',
                queryset=ImageOrderEntry.objects.select_related('coupon_used')
                .filter(paid=True)
                .order_by('size', 'full_name')
            )
        ).get(id=bulk_order.id)


def _download_image_from_cloudinary(image_url: str) -> bytes:
    """
    Download image from Cloudinary URL.
    
    Args:
        image_url: Cloudinary URL
    
    Returns:
        Image bytes
    
    Raises:
        Exception: If download fails
    """
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Failed to download image from {image_url}: {str(e)}")
        raise


def _get_image_extension(image_url: str) -> str:
    """
    Extract file extension from Cloudinary URL.
    
    Args:
        image_url: Cloudinary URL
    
    Returns:
        File extension (e.g., 'jpg', 'png')
    """
    # Extract extension from URL (before query params)
    return image_url.split('.')[-1].split('?')[0].lower()


# ============================================================================
# IMAGE ORGANIZATION
# ============================================================================

def organize_images_by_size(
    bulk_order: ImageBulkOrderLink,
    output_dir: Path
) -> Dict[str, List[Dict]]:
    """
    Download and organize images by size into directories.
    
    Directory structure:
    output_dir/
    ├── S/
    │   ├── john_doe.jpg
    │   └── jane_smith.jpg
    ├── M/
    ├── L/
    └── XL/
    
    Args:
        bulk_order: ImageBulkOrderLink instance with prefetched orders
        output_dir: Path to output directory
    
    Returns:
        Dictionary mapping size to list of file info dicts
        {
            'S': [{'filename': 'john_doe.jpg', 'path': Path(...), 'order_id': ...}],
            ...
        }
    """
    images_dir = output_dir / 'images'
    images_dir.mkdir(parents=True, exist_ok=True)
    
    size_mapping = {}
    paid_orders = bulk_order.orders.filter(paid=True)
    
    logger.info(f"Organizing {paid_orders.count()} images by size")
    
    for order in paid_orders:
        # Create size directory if not exists
        size_dir = images_dir / order.size
        size_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Download image
            image_bytes = _download_image_from_cloudinary(order.uploaded_image)
            
            # Determine filename
            filename = order.get_image_filename()
            
            # Save image
            image_path = size_dir / filename
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
            
            # Track in mapping
            if order.size not in size_mapping:
                size_mapping[order.size] = []
            
            size_mapping[order.size].append({
                'filename': filename,
                'path': image_path,
                'order_id': str(order.id),
                'full_name': order.full_name,
                'custom_name': order.custom_name if order.custom_name else None,
                'serial_number': order.serial_number,
            })
            
            logger.debug(f"Saved image: {image_path}")
            
        except Exception as e:
            logger.error(
                f"Failed to download/save image for order {order.reference}: {str(e)}"
            )
            # Continue with other images
            continue
    
    logger.info(f"Successfully organized images into {len(size_mapping)} size directories")
    
    return size_mapping


# ============================================================================
# PDF GENERATION
# ============================================================================

def generate_bulk_order_pdf(bulk_order, request=None):
    """
    Generate PDF summary for bulk order.
    
    Args:
        bulk_order: ImageBulkOrderLink instance or slug
        request: Optional HTTP request for absolute URLs
    
    Returns:
        bytes: PDF content
    """
    # Get bulk order with optimized query
    bulk_order = _get_bulk_order_with_orders(bulk_order)
    
    # Get paid orders grouped by size
    paid_orders = bulk_order.orders.filter(paid=True).order_by('size', 'full_name')
    
    # Size summary
    size_summary = list(
        paid_orders.values('size')
        .annotate(count=Count('size'))
        .order_by('size')
    )
    
    # Prepare context
    context = {
        'bulk_order': bulk_order,
        'paid_orders': paid_orders,
        'size_summary': size_summary,
        'total_paid': paid_orders.count(),
        'total_revenue': float(bulk_order.get_total_revenue()),
        'company_name': settings.COMPANY_NAME,
        'company_address': getattr(settings, 'COMPANY_ADDRESS', ''),
        'company_phone': getattr(settings, 'COMPANY_PHONE', ''),
        'company_email': getattr(settings, 'COMPANY_EMAIL', ''),
        'now': timezone.now(),
    }
    
    # Render HTML
    html_string = render_to_string('image_bulk_orders/pdf_template.html', context)
    
    # Generate PDF
    try:
        html = HTML(string=html_string, base_url=request.build_absolute_uri() if request else None)
        pdf_bytes = html.write_pdf()
        
        logger.info(f"Generated PDF for image bulk order: {bulk_order.slug}")
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise


# ============================================================================
# WORD DOCUMENT GENERATION
# ============================================================================

def generate_bulk_order_word(bulk_order):
    """
    Generate Word document summary for bulk order.
    
    Args:
        bulk_order: ImageBulkOrderLink instance or slug
    
    Returns:
        BytesIO: Word document buffer
    """
    # Get bulk order with optimized query
    bulk_order = _get_bulk_order_with_orders(bulk_order)
    
    # Create document
    doc = Document()
    
    # Company branding colors
    DARK_GREEN = RGBColor(6, 78, 59)
    GOLD = RGBColor(245, 158, 11)
    
    # Title
    title = doc.add_heading(level=0)
    title_run = title.add_run('IMAGE BULK ORDER SUMMARY')
    title_run.font.color.rgb = DARK_GREEN
    title_run.font.size = Pt(24)
    title_run.bold = True
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Organization name
    org_para = doc.add_paragraph()
    org_run = org_para.add_run(bulk_order.organization_name)
    org_run.font.size = Pt(18)
    org_run.font.color.rgb = GOLD
    org_run.bold = True
    org_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()  # Spacing
    
    # Order details
    doc.add_heading('Order Details', level=1)
    details_table = doc.add_table(rows=5, cols=2)
    details_table.style = 'Light Grid Accent 1'
    
    details_data = [
        ('Organization', bulk_order.organization_name),
        ('Price Per Item', f'₦{bulk_order.price_per_item:,.2f}'),
        ('Total Paid Orders', str(bulk_order.orders.filter(paid=True).count())),
        ('Total Revenue', f'₦{bulk_order.get_total_revenue():,.2f}'),
        ('Generated On', timezone.now().strftime('%B %d, %Y at %I:%M %p')),
    ]
    
    for i, (label, value) in enumerate(details_data):
        row = details_table.rows[i]
        row.cells[0].text = label
        row.cells[1].text = value
        # Bold labels
        row.cells[0].paragraphs[0].runs[0].bold = True
    
    doc.add_paragraph()  # Spacing
    
    # Size summary
    doc.add_heading('Orders by Size', level=1)
    paid_orders = bulk_order.orders.filter(paid=True)
    size_summary = paid_orders.values('size').annotate(count=Count('size')).order_by('size')
    
    size_table = doc.add_table(rows=len(size_summary) + 1, cols=2)
    size_table.style = 'Light Grid Accent 1'
    
    # Header
    size_table.rows[0].cells[0].text = 'Size'
    size_table.rows[0].cells[1].text = 'Count'
    for cell in size_table.rows[0].cells:
        cell.paragraphs[0].runs[0].bold = True
    
    # Data
    for i, item in enumerate(size_summary, start=1):
        size_table.rows[i].cells[0].text = item['size']
        size_table.rows[i].cells[1].text = str(item['count'])
    
    doc.add_page_break()
    
    # Detailed orders list
    doc.add_heading('Detailed Orders List', level=1)
    
    orders_table = doc.add_table(rows=1, cols=5)
    orders_table.style = 'Light Grid Accent 1'
    
    # Header
    header_cells = orders_table.rows[0].cells
    header_cells[0].text = 'Serial #'
    header_cells[1].text = 'Full Name'
    header_cells[2].text = 'Size'
    header_cells[3].text = 'Custom Name'
    header_cells[4].text = 'Payment'
    
    for cell in header_cells:
        cell.paragraphs[0].runs[0].bold = True
    
    # Data rows
    for order in paid_orders.order_by('size', 'serial_number'):
        row_cells = orders_table.add_row().cells
        row_cells[0].text = str(order.serial_number)
        row_cells[1].text = order.full_name
        row_cells[2].text = order.size
        row_cells[3].text = order.custom_name if order.custom_name else '-'
        row_cells[4].text = 'PAID' if order.paid else 'PENDING'
    
    # Save to buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    logger.info(f"Generated Word document for image bulk order: {bulk_order.slug}")
    
    return buffer


# ============================================================================
# EXCEL GENERATION
# ============================================================================

def generate_bulk_order_excel(bulk_order):
    """
    Generate Excel spreadsheet for bulk order.
    
    Args:
        bulk_order: ImageBulkOrderLink instance or slug
    
    Returns:
        BytesIO: Excel workbook buffer
    """
    # Get bulk order with optimized query
    bulk_order = _get_bulk_order_with_orders(bulk_order)
    
    # Create workbook
    buffer = BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
    
    # Company branding colors
    dark_green = '#064E3B'
    gold = '#F59E0B'
    cream = '#FFFBEB'
    
    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'font_color': cream,
        'bg_color': dark_green,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
    })
    
    subheader_format = workbook.add_format({
        'bold': True,
        'font_color': dark_green,
        'bg_color': gold,
        'border': 1,
    })
    
    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'vcenter',
    })
    
    paid_format = workbook.add_format({
        'border': 1,
        'bg_color': '#D1FAE5',
        'font_color': dark_green,
        'bold': True,
    })
    
    # Summary sheet
    summary_sheet = workbook.add_worksheet('Summary')
    summary_sheet.set_column('A:A', 25)
    summary_sheet.set_column('B:B', 30)
    
    # Title
    summary_sheet.merge_range('A1:B1', 'IMAGE BULK ORDER SUMMARY', header_format)
    summary_sheet.set_row(0, 25)
    
    # Organization
    summary_sheet.write('A2', 'Organization', subheader_format)
    summary_sheet.write('B2', bulk_order.organization_name, cell_format)
    
    # Details
    details = [
        ('Price Per Item', f'₦{bulk_order.price_per_item:,.2f}'),
        ('Total Paid Orders', bulk_order.orders.filter(paid=True).count()),
        ('Total Revenue', f'₦{bulk_order.get_total_revenue():,.2f}'),
        ('Payment Deadline', bulk_order.payment_deadline.strftime('%B %d, %Y')),
        ('Generated On', timezone.now().strftime('%B %d, %Y at %I:%M %p')),
    ]
    
    row = 2
    for label, value in details:
        summary_sheet.write(row, 0, label, subheader_format)
        summary_sheet.write(row, 1, value, cell_format)
        row += 1
    
    # Size summary
    row += 1
    summary_sheet.merge_range(row, 0, row, 1, 'ORDERS BY SIZE', header_format)
    row += 1
    
    size_summary = (
        bulk_order.orders.filter(paid=True)
        .values('size')
        .annotate(count=Count('size'))
        .order_by('size')
    )
    
    summary_sheet.write(row, 0, 'Size', subheader_format)
    summary_sheet.write(row, 1, 'Count', subheader_format)
    row += 1
    
    for item in size_summary:
        summary_sheet.write(row, 0, item['size'], cell_format)
        summary_sheet.write(row, 1, item['count'], cell_format)
        row += 1
    
    # Orders sheet
    orders_sheet = workbook.add_worksheet('Orders')
    orders_sheet.set_column('A:A', 10)  # Serial
    orders_sheet.set_column('B:B', 25)  # Full Name
    orders_sheet.set_column('C:C', 30)  # Email
    orders_sheet.set_column('D:D', 10)  # Size
    orders_sheet.set_column('E:E', 20)  # Custom Name
    orders_sheet.set_column('F:F', 15)  # Coupon
    orders_sheet.set_column('G:G', 12)  # Payment
    orders_sheet.set_column('H:H', 20)  # Created
    
    # Header
    headers = ['Serial #', 'Full Name', 'Email', 'Size', 'Custom Name', 'Coupon', 'Payment', 'Created']
    for col, header in enumerate(headers):
        orders_sheet.write(0, col, header, header_format)
    
    # Data rows
    paid_orders = bulk_order.orders.filter(paid=True).order_by('size', 'serial_number')
    
    for row, order in enumerate(paid_orders, start=1):
        orders_sheet.write(row, 0, order.serial_number, cell_format)
        orders_sheet.write(row, 1, order.full_name, cell_format)
        orders_sheet.write(row, 2, order.email, cell_format)
        orders_sheet.write(row, 3, order.size, cell_format)
        orders_sheet.write(row, 4, order.custom_name if order.custom_name else '-', cell_format)
        orders_sheet.write(row, 5, order.coupon_used.code if order.coupon_used else '-', cell_format)
        orders_sheet.write(row, 6, 'PAID', paid_format)
        orders_sheet.write(row, 7, order.created_at.strftime('%Y-%m-%d %H:%M'), cell_format)
    
    workbook.close()
    buffer.seek(0)
    
    logger.info(f"Generated Excel for image bulk order: {bulk_order.slug}")
    
    return buffer


# ============================================================================
# COMPLETE DOCUMENT GENERATION WITH IMAGES
# ============================================================================

def generate_bulk_documents_with_images(bulk_order, request=None):
    """
    Generate complete package: PDF + Word + Excel + Organized Images.
    
    Creates directory structure:
    bulk_order_{slug}_{timestamp}/
    ├── summary.pdf
    ├── summary.docx
    ├── summary.xlsx
    └── images/
        ├── S/
        │   ├── john_doe.jpg
        │   └── jane_smith.jpg
        ├── M/
        ├── L/
        └── XL/
    
    Then creates ZIP and uploads to Cloudinary.
    
    Args:
        bulk_order: ImageBulkOrderLink instance or slug
        request: Optional HTTP request for absolute URLs
    
    Returns:
        str: Cloudinary URL of ZIP file
    
    Raises:
        Exception: If generation fails
    """
    # Get bulk order with optimized query
    bulk_order = _get_bulk_order_with_orders(bulk_order)
    
    # Update status
    bulk_order.generation_status = 'processing'
    bulk_order.save(update_fields=['generation_status', 'updated_at'])
    
    try:
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp())
        output_dir = temp_dir / f"bulk_order_{bulk_order.slug}_{int(timezone.now().timestamp())}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Starting document generation for {bulk_order.slug}")
        
        # 1. Generate PDF
        logger.info("Generating PDF...")
        pdf_bytes = generate_bulk_order_pdf(bulk_order, request)
        pdf_path = output_dir / 'summary.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        logger.info(f"PDF saved: {pdf_path}")
        
        # 2. Generate Word document
        logger.info("Generating Word document...")
        word_buffer = generate_bulk_order_word(bulk_order)
        word_path = output_dir / 'summary.docx'
        with open(word_path, 'wb') as f:
            f.write(word_buffer.read())
        logger.info(f"Word document saved: {word_path}")
        
        # 3. Generate Excel
        logger.info("Generating Excel...")
        excel_buffer = generate_bulk_order_excel(bulk_order)
        excel_path = output_dir / 'summary.xlsx'
        with open(excel_path, 'wb') as f:
            f.write(excel_buffer.read())
        logger.info(f"Excel saved: {excel_path}")
        
        # 4. Organize images by size
        logger.info("Organizing images by size...")
        image_mapping = organize_images_by_size(bulk_order, output_dir)
        
        # Log image organization results
        for size, images in image_mapping.items():
            logger.info(f"Size {size}: {len(images)} images")
        
        # 5. Create image manifest (text file with mapping)
        logger.info("Creating image manifest...")
        manifest_path = output_dir / 'images' / 'IMAGE_MANIFEST.txt'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(f"Image Manifest for {bulk_order.organization_name}\n")
            f.write(f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            for size in sorted(image_mapping.keys()):
                f.write(f"\n{'=' * 80}\n")
                f.write(f"SIZE: {size} ({len(image_mapping[size])} images)\n")
                f.write(f"{'=' * 80}\n\n")
                
                for img_info in sorted(image_mapping[size], key=lambda x: x['serial_number']):
                    f.write(f"Serial #{img_info['serial_number']:04d}\n")
                    f.write(f"  Name: {img_info['full_name']}\n")
                    if img_info['custom_name']:
                        f.write(f"  Custom Name: {img_info['custom_name']}\n")
                    f.write(f"  Filename: {img_info['filename']}\n")
                    f.write(f"  Path: images/{size}/{img_info['filename']}\n")
                    f.write("\n")
        
        logger.info(f"Manifest saved: {manifest_path}")
        
        # 6. Create ZIP archive
        logger.info("Creating ZIP archive...")
        zip_path = temp_dir / f"{output_dir.name}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in output_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_dir.parent)
                    zipf.write(file_path, arcname)
                    logger.debug(f"Added to ZIP: {arcname}")
        
        logger.info(f"ZIP created: {zip_path} ({zip_path.stat().st_size / (1024*1024):.2f} MB)")
        
        # 7. Upload ZIP to Cloudinary
        logger.info("Uploading ZIP to Cloudinary...")
        with open(zip_path, 'rb') as f:
            upload_result = cloudinary.uploader.upload(
                f,
                folder=f'image_bulk_orders/archives',
                resource_type='raw',
                public_id=f"{bulk_order.slug}_{int(timezone.now().timestamp())}",
                overwrite=True
            )
        
        zip_url = upload_result['secure_url']
        logger.info(f"ZIP uploaded to Cloudinary: {zip_url}")
        
        # 8. Update bulk order
        bulk_order.generated_zip_url = zip_url
        bulk_order.last_generated_at = timezone.now()
        bulk_order.generation_status = 'completed'
        bulk_order.save(update_fields=[
            'generated_zip_url',
            'last_generated_at',
            'generation_status',
            'updated_at'
        ])
        
        # 9. Cleanup temporary files
        logger.info("Cleaning up temporary files...")
        shutil.rmtree(temp_dir)
        logger.info("Cleanup complete")
        
        logger.info(
            f"Document generation completed successfully for {bulk_order.slug}. "
            f"ZIP URL: {zip_url}"
        )
        
        return zip_url
        
    except Exception as e:
        logger.error(f"Error generating documents with images: {str(e)}")
        
        # Update status to failed
        bulk_order.generation_status = 'failed'
        bulk_order.save(update_fields=['generation_status', 'updated_at'])
        
        # Cleanup on failure
        try:
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir)
        except Exception as cleanup_error:
            logger.error(f"Cleanup failed: {str(cleanup_error)}")
        
        raise


# ============================================================================
# QUICK IMAGE DOWNLOAD (FOR TESTING/PREVIEW)
# ============================================================================

def download_all_images_zip(bulk_order):
    """
    Quick function to download all images in a ZIP (without documents).
    
    Useful for quick previews or testing.
    
    Args:
        bulk_order: ImageBulkOrderLink instance or slug
    
    Returns:
        BytesIO: ZIP file buffer
    """
    # Get bulk order with optimized query
    bulk_order = _get_bulk_order_with_orders(bulk_order)
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    output_dir = temp_dir / f"images_{bulk_order.slug}"
    
    try:
        # Organize images
        image_mapping = organize_images_by_size(bulk_order, output_dir)
        
        # Create ZIP in memory
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in output_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_dir)
                    zipf.write(file_path, arcname)
        
        buffer.seek(0)
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
        logger.info(f"Created images-only ZIP for {bulk_order.slug}")
        
        return buffer
        
    except Exception as e:
        logger.error(f"Error creating images ZIP: {str(e)}")
        
        # Cleanup on failure
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
        
        raise