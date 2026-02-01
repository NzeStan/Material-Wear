# excel_bulk_orders/utils.py
"""
Utility functions for Excel Bulk Orders.

Handles:
- Excel template generation with data validation
- Excel file parsing and validation
- Document generation (PDF, Word, Excel) for participants
"""
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from io import BytesIO
import pandas as pd
import logging
from django.conf import settings
from bulk_orders.models import CouponCode
from .models import ExcelBulkOrder, ExcelParticipant

logger = logging.getLogger(__name__)


# ============================================================================
# EXCEL TEMPLATE GENERATION
# ============================================================================

def generate_excel_template(bulk_order: ExcelBulkOrder) -> BytesIO:
    """
    Generate Excel template with data validation and formatting.
    
    Args:
        bulk_order: ExcelBulkOrder instance
    
    Returns:
        BytesIO: Excel file buffer
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Participants"
    
    # Style definitions
    header_fill = PatternFill(start_color="064E3B", end_color="064E3B", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_alignment = Alignment(horizontal="center", vertical="center")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Define headers
    headers = ['S/N', 'Full Name', 'Size']
    if bulk_order.requires_custom_name:
        headers.append('Custom Name')
    headers.append('Coupon Code')
    
    # Write headers
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border
    
    # Add data validation for Size column
    size_col_letter = chr(67)  # 'C' (third column)
    size_validation = DataValidation(
        type="list",
        formula1='"Small,Medium,Large,Extra Large,2X Large,3X Large,4X Large"',
        allow_blank=False
    )
    size_validation.error = 'Please select a valid size from the dropdown'
    size_validation.errorTitle = 'Invalid Size'
    ws.add_data_validation(size_validation)
    size_validation.add(f'{size_col_letter}2:{size_col_letter}1000')
    
    # Add example row (row 2)
    example_data = [
        1,
        'John Doe',
        'Medium',
    ]
    if bulk_order.requires_custom_name:
        example_data.append('JD')
    example_data.append('')  # Empty coupon code
    
    for col_num, value in enumerate(example_data, 1):
        cell = ws.cell(row=2, column=col_num)
        cell.value = value
        cell.border = border
        if col_num == 1:  # S/N column
            cell.fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
    
    # Add instructions sheet
    instructions_ws = wb.create_sheet("Instructions")
    instructions = [
        "HOW TO FILL THIS TEMPLATE",
        "",
        f"Campaign: {bulk_order.title}",
        f"Price per participant: ₦{bulk_order.price_per_participant:,.2f}",
        "",
        "COLUMN INSTRUCTIONS:",
        "",
        "1. S/N: Auto-numbered (1, 2, 3, ...)",
        "   - Use sequential numbers starting from 1",
        "",
        "2. Full Name: Participant's complete name",
        "   - Required field",
        "   - Example: 'John Doe', 'Mary Jane Smith'",
        "",
        "3. Size: Uniform/shirt size",
        "   - Select from dropdown only",
        "   - Options: Small, Medium, Large, Extra Large, 2X Large, 3X Large, 4X Large",
        "",
    ]
    
    if bulk_order.requires_custom_name:
        instructions.extend([
            "4. Custom Name: Name for badge/tag",
            "   - Required field",
            "   - Keep it short (max 20 characters recommended)",
            "   - Example: 'JD', 'Mary', 'Coach John'",
            "",
            "5. Coupon Code: Optional discount code",
        ])
    else:
        instructions.extend([
            "4. Coupon Code: Optional discount code",
        ])
    
    instructions.extend([
        "   - Optional field",
        "   - If valid, participant is FREE",
        "   - Leave blank if no coupon",
        "",
        "IMPORTANT NOTES:",
        "- Do NOT delete or rename column headers",
        "- Do NOT skip rows",
        "- Do NOT add extra columns",
        "- Delete the example row before filling your data",
        "- Save as .xlsx format",
        "",
        f"After filling, upload the file to complete your order.",
        "",
        f"Questions? Contact: {settings.COMPANY_EMAIL}",
    ])
    
    for row_num, instruction in enumerate(instructions, 1):
        cell = instructions_ws.cell(row=row_num, column=1)
        cell.value = instruction
        if row_num == 1:
            cell.font = Font(bold=True, size=14)
        elif instruction.startswith(("1.", "2.", "3.", "4.", "5.")):
            cell.font = Font(bold=True)
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 8  # S/N
    ws.column_dimensions['B'].width = 30  # Full Name
    ws.column_dimensions['C'].width = 15  # Size
    if bulk_order.requires_custom_name:
        ws.column_dimensions['D'].width = 20  # Custom Name
        ws.column_dimensions['E'].width = 15  # Coupon Code
    else:
        ws.column_dimensions['D'].width = 15  # Coupon Code
    
    instructions_ws.column_dimensions['A'].width = 70
    
    # Save to BytesIO
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    logger.info(f"Generated Excel template for bulk order: {bulk_order.reference}")
    return buffer


# ============================================================================
# EXCEL VALIDATION
# ============================================================================

def validate_excel_file(bulk_order: ExcelBulkOrder, excel_file) -> dict:
    """
    Validate uploaded Excel file.
    
    Args:
        bulk_order: ExcelBulkOrder instance
        excel_file: Uploaded file object
    
    Returns:
        dict: {
            'valid': bool,
            'errors': list of error dicts,
            'summary': {total_rows, valid_rows, error_rows}
        }
    """
    errors = []
    valid_rows = []
    
    try:
        # Read Excel file
        df = pd.read_excel(excel_file, sheet_name='Participants')
        
        # Expected columns
        expected_columns = ['S/N', 'Full Name', 'Size']
        if bulk_order.requires_custom_name:
            expected_columns.append('Custom Name')
        expected_columns.append('Coupon Code')
        
        # Check column structure
        if list(df.columns) != expected_columns:
            return {
                'valid': False,
                'errors': [{
                    'row': 0,
                    'field': 'Structure',
                    'error': f'Invalid column structure. Expected: {", ".join(expected_columns)}',
                    'current_value': str(list(df.columns))
                }],
                'summary': {'total_rows': 0, 'valid_rows': 0, 'error_rows': 1}
            }
        
        # Valid sizes
        valid_sizes = ['Small', 'Medium', 'Large', 'Extra Large', '2X Large', '3X Large', '4X Large']
        
        # Validate each row
        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel row (accounting for header)
            row_errors = []
            
            # Validate S/N
            if pd.isna(row['S/N']):
                row_errors.append({
                    'row': row_num,
                    'field': 'S/N',
                    'error': 'S/N cannot be empty',
                    'current_value': ''
                })
            
            # Validate Full Name
            full_name = str(row['Full Name']).strip() if not pd.isna(row['Full Name']) else ''
            if not full_name:
                row_errors.append({
                    'row': row_num,
                    'field': 'Full Name',
                    'error': 'Full name is required',
                    'current_value': full_name
                })
            elif len(full_name) < 3:
                row_errors.append({
                    'row': row_num,
                    'field': 'Full Name',
                    'error': 'Full name must be at least 3 characters',
                    'current_value': full_name
                })
            
            # Validate Size
            size = str(row['Size']).strip() if not pd.isna(row['Size']) else ''
            if not size:
                row_errors.append({
                    'row': row_num,
                    'field': 'Size',
                    'error': 'Size is required',
                    'current_value': ''
                })
            elif size not in valid_sizes:
                row_errors.append({
                    'row': row_num,
                    'field': 'Size',
                    'error': f'Invalid size. Must be one of: {", ".join(valid_sizes)}',
                    'current_value': size
                })
            
            # Validate Custom Name (if required)
            if bulk_order.requires_custom_name:
                custom_name = str(row['Custom Name']).strip() if not pd.isna(row['Custom Name']) else ''
                if not custom_name:
                    row_errors.append({
                        'row': row_num,
                        'field': 'Custom Name',
                        'error': 'Custom name is required for this campaign',
                        'current_value': ''
                    })
            
            # Validate Coupon Code (optional)
            coupon_code = str(row['Coupon Code']).strip() if not pd.isna(row['Coupon Code']) else ''
            if coupon_code:
                try:
                    coupon = CouponCode.objects.get(code=coupon_code)
                    if coupon.is_used:
                        row_errors.append({
                            'row': row_num,
                            'field': 'Coupon Code',
                            'error': f'Coupon code "{coupon_code}" has already been used',
                            'current_value': coupon_code
                        })
                except CouponCode.DoesNotExist:
                    row_errors.append({
                        'row': row_num,
                        'field': 'Coupon Code',
                        'error': f'Coupon code "{coupon_code}" does not exist or has expired',
                        'current_value': coupon_code
                    })
            
            # Collect results
            if row_errors:
                errors.extend(row_errors)
            else:
                valid_rows.append(row_num)
        
        # Build response
        total_rows = len(df)
        is_valid = len(errors) == 0
        
        result = {
            'valid': is_valid,
            'errors': errors,
            'summary': {
                'total_rows': total_rows,
                'valid_rows': len(valid_rows),
                'error_rows': len(errors)
            }
        }
        
        logger.info(
            f"Validated Excel for {bulk_order.reference}: "
            f"Valid={is_valid}, Total={total_rows}, Errors={len(errors)}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error validating Excel file: {str(e)}")
        return {
            'valid': False,
            'errors': [{
                'row': 0,
                'field': 'File',
                'error': f'Error reading Excel file: {str(e)}',
                'current_value': ''
            }],
            'summary': {'total_rows': 0, 'valid_rows': 0, 'error_rows': 1}
        }


# ============================================================================
# PARTICIPANT CREATION FROM EXCEL
# ============================================================================

def create_participants_from_excel(bulk_order: ExcelBulkOrder, excel_file) -> int:
    """
    Create ExcelParticipant records from validated Excel file.
    Should only be called after successful payment.
    
    Args:
        bulk_order: ExcelBulkOrder instance
        excel_file: Uploaded/validated Excel file
    
    Returns:
        int: Number of participants created
    """
    try:
        df = pd.read_excel(excel_file, sheet_name='Participants')
        
        # Size mapping
        size_map = {
            'Small': 'S',
            'Medium': 'M',
            'Large': 'L',
            'Extra Large': 'XL',
            '2X Large': 'XXL',
            '3X Large': 'XXXL',
            '4X Large': 'XXXXL'
        }
        
        participants_created = 0
        
        for idx, row in df.iterrows():
            row_num = idx + 2
            
            # Extract data
            full_name = str(row['Full Name']).strip()
            size_display = str(row['Size']).strip()
            size_code = size_map.get(size_display, 'M')  # Default to Medium if unknown
            
            custom_name = None
            if bulk_order.requires_custom_name:
                custom_name = str(row['Custom Name']).strip() if not pd.isna(row['Custom Name']) else ''
            
            coupon_code = str(row['Coupon Code']).strip() if not pd.isna(row['Coupon Code']) else ''
            
            # Handle coupon
            coupon = None
            is_coupon_applied = False
            if coupon_code:
                try:
                    coupon = CouponCode.objects.get(code=coupon_code, is_used=False)
                    is_coupon_applied = True
                    # Mark coupon as used
                    coupon.is_used = True
                    coupon.save()
                except CouponCode.DoesNotExist:
                    pass  # Coupon not found or already used
            
            # Create participant
            ExcelParticipant.objects.create(
                bulk_order=bulk_order,
                full_name=full_name,
                size=size_code,
                custom_name=custom_name,
                coupon_code=coupon_code if coupon_code else None,
                coupon=coupon,
                is_coupon_applied=is_coupon_applied,
                row_number=row_num
            )
            
            participants_created += 1
        
        logger.info(
            f"Created {participants_created} participants for bulk order: {bulk_order.reference}"
        )
        
        return participants_created
        
    except Exception as e:
        logger.error(f"Error creating participants from Excel: {str(e)}")
        raise


# ============================================================================
# DOCUMENT GENERATION (PDF, WORD, EXCEL)
# ============================================================================

def generate_participants_pdf(bulk_order: ExcelBulkOrder) -> BytesIO:
    """
    Generate PDF list of all participants.
    Similar to bulk_orders.utils.generate_bulk_order_pdf
    """
    # TODO: Implement PDF generation
    # Use bulk_orders PDF generation as reference
    pass


def generate_participants_word(bulk_order: ExcelBulkOrder) -> BytesIO:
    """
    Generate Word document list of all participants.
    Similar to bulk_orders.utils.generate_bulk_order_word
    """
    # TODO: Implement Word generation
    # Use bulk_orders Word generation as reference
    pass


def generate_participants_excel(bulk_order: ExcelBulkOrder) -> BytesIO:
    """
    Generate Excel summary of all participants.
    Similar to bulk_orders.utils.generate_bulk_order_excel
    """
    # TODO: Implement Excel generation
    # Use bulk_orders Excel generation as reference
    pass