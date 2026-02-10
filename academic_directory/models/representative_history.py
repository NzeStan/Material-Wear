"""
Representative History Model

Tracks historical positions and role changes for representatives.
"""

from django.db import models
from django.utils import timezone


class RepresentativeHistory(models.Model):
    """
    Representative History model for tracking role changes and historical positions.
    
    This model creates a historical record whenever a representative's details are updated,
    allowing us to track:
    - Former class reps who became presidents
    - Role transitions over time
    - Historical contact information
    
    Attributes:
        representative: Foreign key to Representative
        full_name: Name at time of snapshot
        phone_number: Phone at time of snapshot
        department: Department at time of snapshot
        faculty: Faculty at time of snapshot
        university: University at time of snapshot
        role: Role at time of snapshot
        entry_year: Entry year at time of snapshot
        tenure_start_year: Tenure start at time of snapshot
        verification_status: Verification status at time of snapshot
        is_active: Active status at time of snapshot
        snapshot_date: When this snapshot was created
        notes: Optional notes about this historical record
    """
    
    representative = models.ForeignKey(
        'Representative',
        on_delete=models.CASCADE,
        related_name='history',
        help_text="Representative this history belongs to"
    )
    
    # Snapshot of key fields
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        help_text="Department at time of snapshot"
    )
    
    faculty = models.ForeignKey(
        'Faculty',
        on_delete=models.SET_NULL,
        null=True,
        help_text="Faculty at time of snapshot"
    )
    
    university = models.ForeignKey(
        'University',
        on_delete=models.SET_NULL,
        null=True,
        help_text="University at time of snapshot"
    )
    
    role = models.CharField(
        max_length=20,
        help_text="Role at time of snapshot"
    )
    
    entry_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Entry year at time of snapshot"
    )
    
    tenure_start_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Tenure start at time of snapshot"
    )
    
    verification_status = models.CharField(
        max_length=20,
        help_text="Verification status at time of snapshot"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Active status at time of snapshot"
    )
    
    snapshot_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When this snapshot was created"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Optional notes about this historical record"
    )
    
    class Meta:
        verbose_name = "Representative History"
        verbose_name_plural = "Representative Histories"
        ordering = ['-snapshot_date']
        indexes = [
            models.Index(fields=['representative', '-snapshot_date']),
            models.Index(fields=['phone_number']),
        ]
    
    def __str__(self):
        return f"{self.full_name} - {self.role} ({self.snapshot_date.strftime('%Y-%m-%d')})"
    
    @classmethod
    def create_from_representative(cls, representative):
        """
        Create a history snapshot from a Representative instance.
        
        Args:
            representative: Representative instance to snapshot
        
        Returns:
            RepresentativeHistory instance
        """
        return cls.objects.create(
            representative=representative,
            full_name=representative.full_name,
            phone_number=representative.phone_number,
            department=representative.department,
            faculty=representative.faculty,
            university=representative.university,
            role=representative.role,
            entry_year=representative.entry_year,
            tenure_start_year=representative.tenure_start_year,
            verification_status=representative.verification_status,
            is_active=representative.is_active,
            notes=f"Snapshot created on update"
        )
    
    @property
    def role_display(self):
        """Return human-readable role."""
        role_map = {
            'CLASS_REP': 'Class Representative',
            'DEPT_PRESIDENT': 'Department President',
            'FACULTY_PRESIDENT': 'Faculty President',
        }
        return role_map.get(self.role, self.role)
