# clothing_image_orders/validators.py
"""
Validators for clothing image orders.

Includes image validation using python-magic for MIME type checking.
"""
import magic
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
import logging

logger = logging.getLogger(__name__)


def validate_image_file(file):
    """
    Validate uploaded image file.
    
    Checks:
    - File size (max 5MB)
    - MIME type (must be image/jpeg, image/png, or image/jpg)
    - File extension
    
    Args:
        file: UploadedFile instance
    
    Raises:
        ValidationError: If validation fails
    """
    # Check file size (5MB max)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    
    if hasattr(file, 'size') and file.size > max_size:
        raise ValidationError(
            f"File size exceeds maximum allowed size of 5MB. Your file is {file.size / (1024*1024):.2f}MB"
        )
    
    # Check MIME type using python-magic
    try:
        # Read file content for MIME detection
        file_content = file.read()
        file.seek(0)  # Reset file pointer
        
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file_content)
        
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        
        if mime_type not in allowed_types:
            raise ValidationError(
                f"Invalid file type: {mime_type}. Only JPEG, JPG, and PNG images are allowed."
            )
        
        logger.debug(f"Image validated: MIME type {mime_type}, size {file.size} bytes")
        
    except Exception as e:
        logger.error(f"Error validating image: {str(e)}")
        raise ValidationError(f"Error validating image file: {str(e)}")
    
    # Check file extension
    if hasattr(file, 'name'):
        filename = file.name.lower()
        allowed_extensions = ['.jpg', '.jpeg', '.png']
        
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            raise ValidationError(
                f"Invalid file extension. Only .jpg, .jpeg, and .png files are allowed."
            )


def validate_cloudinary_image_url(url):
    """
    Validate Cloudinary image URL format.
    
    Args:
        url: Cloudinary URL string
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not url:
        return False
    
    # Check if it's a Cloudinary URL
    if 'cloudinary.com' not in url:
        return False
    
    # Check if it contains /image/upload/
    if '/image/upload/' not in url:
        return False
    
    return True


def validate_size_choice(size):
    """
    Validate clothing size choice.
    
    Args:
        size: Size string
    
    Raises:
        ValidationError: If size is invalid
    """
    from .models import ClothingOrderParticipant
    
    valid_sizes = [choice[0] for choice in ClothingOrderParticipant.SIZE_CHOICES]
    
    if size not in valid_sizes:
        raise ValidationError(
            f"Invalid size: {size}. Valid sizes are: {', '.join(valid_sizes)}"
        )


def validate_custom_name_length(custom_name):
    """
    Validate custom name length for printing.
    
    Args:
        custom_name: Custom name string
    
    Raises:
        ValidationError: If name is too long
    """
    max_length = 50  # Maximum characters for printing
    
    if len(custom_name) > max_length:
        raise ValidationError(
            f"Custom name is too long. Maximum {max_length} characters allowed. "
            f"Your name is {len(custom_name)} characters."
        )


def validate_nigerian_phone(phone):
    """
    Validate Nigerian phone number format.
    
    Accepts formats:
    - 08012345678 (11 digits)
    - +2348012345678 (14 digits with country code)
    - 2348012345678 (13 digits with country code)
    
    Args:
        phone: Phone number string
    
    Raises:
        ValidationError: If phone format is invalid
    """
    import re
    
    # Remove spaces and hyphens
    cleaned = re.sub(r'[\s\-]', '', phone)
    
    # Check formats
    patterns = [
        r'^0[7-9][0-1]\d{8}$',  # 08012345678
        r'^\+234[7-9][0-1]\d{8}$',  # +2348012345678
        r'^234[7-9][0-1]\d{8}$',  # 2348012345678
    ]
    
    if not any(re.match(pattern, cleaned) for pattern in patterns):
        raise ValidationError(
            "Invalid Nigerian phone number format. "
            "Valid formats: 08012345678, +2348012345678, or 2348012345678"
        )