"""
Representative Model

Core model for storing academic representative contact information.
"""

from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import datetime
from django.conf import settings
import uuid

class Representative(models.Model):
    """
    Representative model for storing academic representative contact information.
    
    This model handles:
    - Class Representatives (by academic level)
    - Department Presidents (fixed-term)
    - Faculty Presidents (fixed-term)
    
    Key Features:
    - Auto-deduplication by phone number
    - Dynamic academic level calculation
    - Automatic graduation/deactivation
    - Historical role tracking
    - Verification workflow
    
    Attributes:
        full_name: Full legal name
        nickname: Optional preferred name
        phone_number: Primary contact (unique identifier)
        whatsapp_number: Optional WhatsApp contact
        email: Optional email address
        department: Foreign key to Department
        faculty: Denormalized FK to Faculty (for faster queries)
        university: Denormalized FK to University (for faster queries)
        role: CLASS_REP, DEPT_PRESIDENT, or FACULTY_PRESIDENT
        entry_year: Year student entered program (for class reps only)
        tenure_start_year: Year representative took office (for presidents)
        submission_source: How the data was submitted
        submission_source_other: Free text for "other" source
        verification_status: UNVERIFIED, VERIFIED, or DISPUTED
        verified_by: User who verified the entry
        verified_at: Timestamp of verification
        notes: Optional internal notes
        is_active: Whether the representative is currently active
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """
    
    ROLES = [
        ('CLASS_REP', 'Class Representative'),
        ('DEPT_PRESIDENT', 'Department President'),
        ('FACULTY_PRESIDENT', 'Faculty President'),
    ]
    
    VERIFICATION_STATUS = [
        ('UNVERIFIED', 'Unverified'),
        ('VERIFIED', 'Verified'),
        ('DISPUTED', 'Disputed'),
    ]
    
    SUBMISSION_SOURCES = [
        ('WEBSITE', 'Website Submission'),
        ('WHATSAPP', 'WhatsApp'),
        ('EMAIL', 'Email'),
        ('PHONE', 'Phone Call'),
        ('SMS', 'SMS'),
        ('MANUAL', 'Manual Entry'),
        ('IMPORT', 'Bulk Import'),
        ('OTHER', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Phone number validator (Nigerian format)
    phone_regex = RegexValidator(
        regex=r'^\+?234?\d{10,11}$',
        message="Phone number must be in format: '+2348012345678' or '08012345678'"
    )
    
    # Personal Information
    full_name = models.CharField(
        max_length=255,
        help_text="Full legal name of the representative"
    )
    
    nickname = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Optional preferred name or nickname"
    )
    
    # Contact Information
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[phone_regex],
        help_text="Primary contact number (unique identifier)"
    )
    
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[phone_regex],
        help_text="Optional WhatsApp contact number"
    )
    
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Optional email address"
    )
    
    # Institutional Relationships
    department = models.ForeignKey(
        'Department',
        on_delete=models.CASCADE,
        related_name='representatives',
        help_text="Department the representative belongs to"
    )
    
    faculty = models.ForeignKey(
        'Faculty',
        on_delete=models.CASCADE,
        related_name='representatives',
        help_text="Faculty (denormalized for faster queries)"
    )
    
    university = models.ForeignKey(
        'University',
        on_delete=models.CASCADE,
        related_name='representatives',
        help_text="University (denormalized for faster queries)"
    )
    
    # Role Information
    role = models.CharField(
        max_length=20,
        choices=ROLES,
        help_text="Type of representative role"
    )
    
    # Academic Information (for Class Reps)
    entry_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Year student entered the program (for class reps only)"
    )
    
    # Tenure Information (for Presidents)
    tenure_start_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Year representative took office (for presidents)"
    )
    
    # Submission Metadata
    submission_source = models.CharField(
        max_length=20,
        choices=SUBMISSION_SOURCES,
        default='WEBSITE',
        help_text="How this data was submitted"
    )
    
    submission_source_other = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Free text description if source is 'Other'"
    )
    
    # Verification
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='UNVERIFIED',
        help_text="Verification status of this entry"
    )
    
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_representatives',
        help_text="Admin user who verified this entry"
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when verification occurred"
    )
    
    # Additional Information
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Optional internal notes about this representative"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this representative is currently active"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Representative"
        verbose_name_plural = "Representatives"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['department', 'role']),
            models.Index(fields=['faculty', 'role']),
            models.Index(fields=['university', 'role']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['entry_year']),
            models.Index(fields=['tenure_start_year']),
        ]
    
    def __str__(self):
        display_name = self.nickname if self.nickname else self.full_name
        return f"{display_name} - {self.get_role_display()} ({self.department.abbreviation})"
    
    def clean(self):
        """Validate model data before saving."""
        from django.core.exceptions import ValidationError
        
        # Validate role-specific requirements
        if self.role == 'CLASS_REP':
            if not self.entry_year:
                raise ValidationError({
                    'entry_year': 'Entry year is required for class representatives'
                })
            if self.tenure_start_year:
                raise ValidationError({
                    'tenure_start_year': 'Class representatives should not have tenure_start_year'
                })
        
        elif self.role in ['DEPT_PRESIDENT', 'FACULTY_PRESIDENT']:
            if not self.tenure_start_year:
                raise ValidationError({
                    'tenure_start_year': 'Tenure start year is required for presidents'
                })
            if self.entry_year:
                raise ValidationError({
                    'entry_year': 'Presidents should not have entry_year (use tenure_start_year instead)'
                })
        
        # Validate phone number format
        if self.phone_number and not self.phone_number.startswith('+'):
            # Auto-format Nigerian numbers
            if self.phone_number.startswith('0'):
                self.phone_number = f'+234{self.phone_number[1:]}'
            elif self.phone_number.startswith('234'):
                self.phone_number = f'+{self.phone_number}'
        
        # Same for WhatsApp number
        if self.whatsapp_number and not self.whatsapp_number.startswith('+'):
            if self.whatsapp_number.startswith('0'):
                self.whatsapp_number = f'+234{self.whatsapp_number[1:]}'
            elif self.whatsapp_number.startswith('234'):
                self.whatsapp_number = f'+{self.whatsapp_number}'
        
        # Validate submission source
        if self.submission_source == 'OTHER' and not self.submission_source_other:
            raise ValidationError({
                'submission_source_other': 'Please specify the submission source when "Other" is selected'
            })
    
    def save(self, *args, **kwargs):
        """Override save to handle denormalization and validation."""
        # Auto-populate denormalized fields
        if self.department:
            self.faculty = self.department.faculty
            self.university = self.department.faculty.university
        
        # Run validation
        self.clean()
        
        # Check if this is a new record (for history tracking)
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Create history entry if not new
        if not is_new:
            from .representative_history import RepresentativeHistory
            RepresentativeHistory.create_from_representative(self)
    
    # ==================== COMPUTED PROPERTIES ====================
    
    @property
    def current_level(self):
        """
        Calculate current academic level for class representatives.
        
        Returns:
            int: Current level (100, 200, 300, etc.) or None if not applicable
        """
        if self.role != 'CLASS_REP' or not self.entry_year:
            return None
        
        from ..utils.level_calculator import calculate_current_level
        
        try:
            program_duration = self.department.programduration.duration_years
        except:
            # Default to 4 years if no program duration set
            program_duration = 4
        
        return calculate_current_level(self.entry_year, program_duration)
    
    @property
    def current_level_display(self):
        """Return formatted level (e.g., '300L')."""
        level = self.current_level
        return f"{level}L" if level else None
    
    @property
    def is_final_year(self):
        """Check if the representative is in their final year."""
        if self.role != 'CLASS_REP' or not self.entry_year:
            return False
        
        try:
            program_duration = self.department.programduration.duration_years
            current_year = datetime.now().year
            years_elapsed = current_year - self.entry_year + 1
            return years_elapsed >= program_duration
        except:
            return False
    
    @property
    def expected_graduation_year(self):
        """Calculate expected graduation year for class reps."""
        if self.role != 'CLASS_REP' or not self.entry_year:
            return None
        
        try:
            program_duration = self.department.programduration.duration_years
        except:
            program_duration = 4
        
        return self.entry_year + program_duration
    
    @property
    def has_graduated(self):
        """Check if the representative has graduated."""
        if self.role != 'CLASS_REP':
            return False
        
        grad_year = self.expected_graduation_year
        if not grad_year:
            return False
        
        return datetime.now().year > grad_year
    
    @property
    def display_name(self):
        """Return preferred display name (nickname if available, else full name)."""
        return self.nickname if self.nickname else self.full_name
    
    @property
    def verification_status_badge(self):
        """Return HTML badge for verification status (for admin)."""
        status_colors = {
            'UNVERIFIED': 'warning',
            'VERIFIED': 'success',
            'DISPUTED': 'danger',
        }
        color = status_colors.get(self.verification_status, 'secondary')
        return f'<span class="badge bg-{color}">{self.get_verification_status_display()}</span>'
    
    # ==================== METHODS ====================
    
    def verify(self, user):
        """
        Mark this representative as verified.
        
        Args:
            user: Django User instance who is verifying
        """
        self.verification_status = 'VERIFIED'
        self.verified_by = user
        self.verified_at = timezone.now()
        self.save()
    
    def dispute(self):
        """Mark this representative as disputed."""
        self.verification_status = 'DISPUTED'
        self.verified_by = None
        self.verified_at = None
        self.save()
    
    def deactivate(self, reason=None):
        """
        Deactivate this representative.
        
        Args:
            reason: Optional reason for deactivation
        """
        self.is_active = False
        if reason:
            self.notes = f"{self.notes}\n\nDeactivated: {reason}" if self.notes else f"Deactivated: {reason}"
        self.save()
    
    def check_and_update_status(self):
        """
        Check if representative should be auto-deactivated based on graduation.
        
        This is called periodically (e.g., via management command or celery task).
        """
        if self.has_graduated and self.is_active:
            self.deactivate(reason=f"Auto-deactivated: Graduated in {self.expected_graduation_year}")
            return True
        return False
