"""
Faculty Model

Represents faculties within universities.
"""

from django.db import models
from django.core.validators import RegexValidator
import uuid

class Faculty(models.Model):
    """
    Faculty model representing academic faculties within universities.
    
    A faculty is a major academic division within a university (e.g., Engineering, Sciences).
    
    Attributes:
        university: Foreign key to University
        name: Full name of the faculty
        abbreviation: Short form (e.g., ENG, SCI, ARTS)
        is_active: Whether faculty is currently operational
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    university = models.ForeignKey(
        'University',
        on_delete=models.CASCADE,
        related_name='faculties',
        help_text="University this faculty belongs to"
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Full name of the faculty (e.g., Faculty of Engineering)"
    )
    
    abbreviation = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]+$',
                message="Abbreviation must contain only uppercase letters"
            )
        ],
        help_text="Short form (e.g., ENG, SCI, ARTS)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the faculty is currently operational"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Faculty"
        verbose_name_plural = "Faculties"
        ordering = ['university__name', 'name']
        unique_together = [['university', 'name']]
        indexes = [
            models.Index(fields=['university', 'name']),
            models.Index(fields=['abbreviation']),
        ]
    
    def __str__(self):
        return f"{self.university.abbreviation} - {self.name}"
    
    def clean(self):
        """Validate model data before saving."""
        from django.core.exceptions import ValidationError
        
        # Ensure abbreviation is uppercase
        if self.abbreviation:
            self.abbreviation = self.abbreviation.upper()
        
        # Validate name is not empty
        if not self.name or not self.name.strip():
            raise ValidationError({'name': 'Faculty name cannot be empty'})
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def departments_count(self):
        """Return the number of departments in this faculty."""
        return self.departments.filter(is_active=True).count()
    
    @property
    def representatives_count(self):
        """Return the number of representatives in this faculty."""
        return self.representatives.filter(is_active=True).count()
    
    @property
    def full_name(self):
        """Return full qualified name including university."""
        return f"{self.university.abbreviation} - {self.name}"
