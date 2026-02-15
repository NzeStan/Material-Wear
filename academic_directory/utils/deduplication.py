"""
Deduplication Utility

Handles automatic merging of duplicate representative entries based on phone number.
"""

from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone
import uuid


def merge_representative_records(existing_record, new_data: Dict[str, Any]) -> tuple:
    """
    Merge a new submission with an existing representative record.
    
    This function handles auto-deduplication when the same phone number
    is submitted multiple times. It:
    - Updates existing record with new data
    - Preserves verification status unless explicitly overridden
    - Creates a history snapshot before merging
    - Returns information about what was updated
    
    Args:
        existing_record: Existing Representative instance
        new_data: Dictionary containing new submission data
    
    Returns:
        Tuple[Representative, dict]: (updated_record, changes_made)
    
    Example:
        >>> existing = Representative.objects.get(phone_number='+2348012345678')
        >>> new_data = {'full_name': 'Updated Name', 'email': 'new@example.com'}
        >>> updated, changes = merge_representative_records(existing, new_data)
        >>> print(changes)
        {'full_name': {'old': 'Old Name', 'new': 'Updated Name'}, 'email': {...}}
    """
    from ..models import Representative, RepresentativeHistory
    
    changes_made = {}
    
    with transaction.atomic():
        # Create history snapshot before making changes
        RepresentativeHistory.create_from_representative(existing_record)
        
        # Fields that can be updated
        updateable_fields = [
            'full_name', 'nickname', 'whatsapp_number', 'email',
            'department', 'faculty', 'university', 'role',
            'entry_year', 'tenure_start_year', 'submission_source',
            'submission_source_other', 'notes'
        ]
        
        # Track changes
        for field in updateable_fields:
            if field in new_data:
                old_value = getattr(existing_record, field)
                new_value = new_data[field]
                
                # Only update if different and new value is not None/empty
                if new_value and new_value != old_value:
                    changes_made[field] = {
                        'old': str(old_value) if old_value else None,
                        'new': str(new_value)
                    }
                    setattr(existing_record, field, new_value)
        
        # Special handling for verification status
        # If existing record is UNVERIFIED and new submission comes in,
        # keep it UNVERIFIED but update the data
        if existing_record.verification_status == 'UNVERIFIED':
            # Data updated but still needs verification
            pass
        elif existing_record.verification_status == 'VERIFIED':
            # If verified record gets updated, mark as needing re-verification
            if changes_made:
                existing_record.verification_status = 'UNVERIFIED'
                existing_record.verified_by = None
                existing_record.verified_at = None
                changes_made['verification_status'] = {
                    'old': 'VERIFIED',
                    'new': 'UNVERIFIED',
                    'reason': 'Auto-reset due to data update'
                }
        
        # Add merge metadata to notes
        if changes_made:
            merge_note = (
                f"\n\n[Auto-merge on {timezone.now().strftime('%Y-%m-%d %H:%M')}] "
                f"Updated from new submission. "
                f"Fields changed: {', '.join(changes_made.keys())}"
            )
            existing_record.notes = (
                f"{existing_record.notes or ''}{merge_note}"
            ).strip()
        
        # Save the updated record
        existing_record.save()
    
    return existing_record, changes_made


def find_existing_representative(phone_number: str):
    """
    Find existing representative by phone number.
    
    Handles different phone number formats by normalizing before search.
    
    Args:
        phone_number: Phone number to search for
    
    Returns:
        Representative instance or None if not found
    """
    from ..models import Representative
    from .validators import normalize_phone_number, validate_nigerian_phone
    
    # Validate and normalize phone number
    if not validate_nigerian_phone(phone_number):
        return None
    
    normalized_phone = normalize_phone_number(phone_number)
    
    try:
        return Representative.objects.get(phone_number=normalized_phone)
    except Representative.DoesNotExist:
        return None
    except Representative.MultipleObjectsReturned:
        # This shouldn't happen due to unique constraint, but handle it
        return Representative.objects.filter(phone_number=normalized_phone).first()


def check_for_potential_duplicates(data: Dict[str, Any]) -> list:
    """
    Check for potential duplicate entries beyond just phone number.
    
    This function looks for:
    - Similar names in same department
    - Same email addresses
    - Same WhatsApp numbers
    
    Useful for admin review of possible duplicates.
    
    Args:
        data: Dictionary containing representative data
    
    Returns:
        List of potential duplicate Representative instances
    """
    from ..models import Representative
    from django.db.models import Q
    
    potential_duplicates = []
    
    # Check for same email (if provided)
    if data.get('email'):
        email_matches = Representative.objects.filter(
            email__iexact=data['email']
        ).exclude(phone_number=data.get('phone_number'))
        potential_duplicates.extend(list(email_matches))
    
    # Check for same WhatsApp number (if provided)
    if data.get('whatsapp_number'):
        whatsapp_matches = Representative.objects.filter(
            whatsapp_number=data['whatsapp_number']
        ).exclude(phone_number=data.get('phone_number'))
        potential_duplicates.extend(list(whatsapp_matches))
    
    # Check for similar names in same department
    if data.get('full_name') and data.get('department'):
        name_parts = data['full_name'].lower().split()
        if len(name_parts) >= 2:
            # Look for records with same first and last name
            name_query = Q(full_name__icontains=name_parts[0]) & Q(full_name__icontains=name_parts[-1])
            name_matches = Representative.objects.filter(
                name_query,
                department=data['department']
            ).exclude(phone_number=data.get('phone_number'))
            potential_duplicates.extend(list(name_matches))
    
    # Remove duplicates from the list
    return list(set(potential_duplicates))


def preview_merge_changes(existing_record, new_data: Dict[str, Any]) -> Dict:
    """
    Preview what would change if we merged new data with existing record.
    
    Useful for admin review before automatic merging.
    
    Args:
        existing_record: Existing Representative instance
        new_data: Dictionary containing new submission data
    
    Returns:
        Dictionary showing field-by-field comparison
    """
    preview = {
        'phone_number': existing_record.phone_number,
        'existing_id': existing_record.id,
        'changes': {},
        'unchanged': {},
    }
    
    updateable_fields = [
        'full_name', 'nickname', 'whatsapp_number', 'email',
        'department', 'faculty', 'university', 'role',
        'entry_year', 'tenure_start_year', 'submission_source',
        'submission_source_other', 'notes'
    ]
    
    for field in updateable_fields:
        old_value = getattr(existing_record, field)
        new_value = new_data.get(field)
        
        if new_value and new_value != old_value:
            preview['changes'][field] = {
                'current': str(old_value) if old_value else None,
                'incoming': str(new_value)
            }
        else:
            preview['unchanged'][field] = str(old_value) if old_value else None
    
    return preview


def handle_submission_with_deduplication(data: Dict[str, Any]):
    """
    Handle a new submission with automatic deduplication.
    
    This is the main entry point for processing submissions.
    It will either create a new record or merge with existing.
    
    Args:
        data: Dictionary containing representative data
    
    Returns:
        Tuple[Representative, bool, dict]: (record, is_new, changes_or_errors)
    
    Example:
        >>> data = {
        ...     'phone_number': '+2348012345678',
        ...     'full_name': 'John Doe',
        ...     'department_id': '10950e0b-c8e2-4628-aacb-dcd0d6c7cc68',
        ...     'role': 'CLASS_REP',
        ...     'entry_year': 2022
        ... }
        >>> record, is_new, result = handle_submission_with_deduplication(data)
        >>> if is_new:
        ...     print(f"Created new record: {record}")
        ... else:
        ...     print(f"Updated existing record. Changes: {result}")
    """
    from ..models import Representative, Department
    from .validators import normalize_phone_number
    
    # Normalize phone number
    phone_number = normalize_phone_number(data['phone_number'])
    data['phone_number'] = phone_number
    
    # Check for existing record
    existing = find_existing_representative(phone_number)
    
    if existing:
        # Merge with existing record
        updated_record, changes = merge_representative_records(existing, data)
        return updated_record, False, changes
    else:
        # Create new record
        # Handle denormalized fields and UUID support
        if 'department' in data or 'department_id' in data:
            dept_id = data.get('department_id') or data.get('department')
            
            # Check if dept_id needs to be fetched from database
            # Support both int (legacy) and UUID
            if isinstance(dept_id, (int, uuid.UUID, str)):
                department = Department.objects.select_related('faculty__university').get(id=dept_id)
            else:
                # Already a Department instance
                department = dept_id
            
            data['department'] = department
            data['faculty'] = department.faculty
            data['university'] = department.faculty.university
            
            # Remove department_id if present (we use department object)
            data.pop('department_id', None)
        
        new_record = Representative.objects.create(**data)
        return new_record, True, {}