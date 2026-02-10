"""
University Model

Represents Nigerian universities in the directory system.
"""

from django.db import models
from django.core.validators import RegexValidator


class University(models.Model):
    """
    University model representing Nigerian higher education institutions.
    
    Attributes:
        name: Full official name of the university
        abbreviation: Short form (e.g., UNIBEN, UI, UNILAG)
        state: Nigerian state where university is located
        type: Federal, State, or Private
        is_active: Whether university is currently operational
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """
    
    UNIVERSITY_TYPES = [
        ('FEDERAL', 'Federal University'),
        ('STATE', 'State University'),
        ('PRIVATE', 'Private University'),
    ]
    
    # Nigerian states for validation
    NIGERIAN_STATES = [
        ('ABIA', 'Abia'),
        ('ADAMAWA', 'Adamawa'),
        ('AKWA_IBOM', 'Akwa Ibom'),
        ('ANAMBRA', 'Anambra'),
        ('BAUCHI', 'Bauchi'),
        ('BAYELSA', 'Bayelsa'),
        ('BENUE', 'Benue'),
        ('BORNO', 'Borno'),
        ('CROSS_RIVER', 'Cross River'),
        ('DELTA', 'Delta'),
        ('EBONYI', 'Ebonyi'),
        ('EDO', 'Edo'),
        ('EKITI', 'Ekiti'),
        ('ENUGU', 'Enugu'),
        ('FCT', 'Federal Capital Territory'),
        ('GOMBE', 'Gombe'),
        ('IMO', 'Imo'),
        ('JIGAWA', 'Jigawa'),
        ('KADUNA', 'Kaduna'),
        ('KANO', 'Kano'),
        ('KATSINA', 'Katsina'),
        ('KEBBI', 'Kebbi'),
        ('KOGI', 'Kogi'),
        ('KWARA', 'Kwara'),
        ('LAGOS', 'Lagos'),
        ('NASARAWA', 'Nasarawa'),
        ('NIGER', 'Niger'),
        ('OGUN', 'Ogun'),
        ('ONDO', 'Ondo'),
        ('OSUN', 'Osun'),
        ('OYO', 'Oyo'),
        ('PLATEAU', 'Plateau'),
        ('RIVERS', 'Rivers'),
        ('SOKOTO', 'Sokoto'),
        ('TARABA', 'Taraba'),
        ('YOBE', 'Yobe'),
        ('ZAMFARA', 'Zamfara'),
    ]
    
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Full official name of the university"
    )
    
    abbreviation = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]+$',
                message="Abbreviation must contain only uppercase letters"
            )
        ],
        help_text="Short form (e.g., UNIBEN, UI, UNILAG)"
    )
    
    state = models.CharField(
        max_length=50,
        choices=NIGERIAN_STATES,
        help_text="Nigerian state where the university is located"
    )
    
    type = models.CharField(
        max_length=20,
        choices=UNIVERSITY_TYPES,
        default='FEDERAL',
        help_text="Federal, State, or Private university"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the university is currently operational"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "University"
        verbose_name_plural = "Universities"
        ordering = ['name']
        indexes = [
            models.Index(fields=['abbreviation']),
            models.Index(fields=['state']),
            models.Index(fields=['type']),
        ]
    
    def __str__(self):
        return f"{self.abbreviation} - {self.name}"
    
    def clean(self):
        """Validate model data before saving."""
        from django.core.exceptions import ValidationError
        
        # Ensure abbreviation is uppercase
        if self.abbreviation:
            self.abbreviation = self.abbreviation.upper()
        
        # Validate name is not empty
        if not self.name or not self.name.strip():
            raise ValidationError({'name': 'University name cannot be empty'})
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def faculties_count(self):
        """Return the number of faculties in this university."""
        return self.faculties.filter(is_active=True).count()
    
    @property
    def departments_count(self):
        """Return the number of departments across all faculties."""
        from .department import Department
        return Department.objects.filter(
            faculty__university=self,
            is_active=True
        ).count()
    
    @property
    def representatives_count(self):
        """Return the number of representatives in this university."""
        return self.representatives.filter(is_active=True).count()
