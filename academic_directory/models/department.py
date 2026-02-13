"""
Department Model

Represents departments within faculties.
"""

from django.db import models
from django.core.validators import RegexValidator
import uuid

class Department(models.Model):
    """
    Department model representing academic departments within faculties.
    
    A department is a specific academic division within a faculty 
    (e.g., Computer Science, Mechanical Engineering).
    
    Attributes:
        faculty: Foreign key to Faculty
        name: Full name of the department
        abbreviation: Short form (e.g., CSC, MEE, CHE)
        is_active: Whether department is currently operational
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    faculty = models.ForeignKey(
        'Faculty',
        on_delete=models.CASCADE,
        related_name='departments',
        help_text="Faculty this department belongs to"
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Full name of the department (e.g., Computer Science)"
    )
    
    abbreviation = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]+$',
                message="Abbreviation must contain only uppercase letters"
            )
        ],
        help_text="Short form (e.g., CSC, MEE, CHE)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the department is currently operational"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ['faculty__university__name', 'faculty__name', 'name']
        unique_together = [['faculty', 'name']]
        indexes = [
            models.Index(fields=['faculty', 'name']),
            models.Index(fields=['abbreviation']),
        ]
    
    def __str__(self):
        return f"{self.faculty.university.abbreviation} - {self.faculty.abbreviation} - {self.name}"
    
    def clean(self):
        """Validate model data before saving."""
        from django.core.exceptions import ValidationError
        
        # Ensure abbreviation is uppercase
        if self.abbreviation:
            self.abbreviation = self.abbreviation.upper()
        
        # Validate name is not empty
        if not self.name or not self.name.strip():
            raise ValidationError({'name': 'Department name cannot be empty'})
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def university(self):
        """Return the university this department belongs to."""
        return self.faculty.university
    
    @property
    def representatives_count(self):
        """Return the number of representatives in this department."""
        return self.representatives.filter(is_active=True).count()
    
    @property
    def program_duration(self):
        """Return the program duration for this department (if exists)."""
        try:
            return self.programduration.duration_years
        except:
            return None
    
    @property
    def full_name(self):
        """Return full qualified name including university and faculty."""
        return f"{self.faculty.university.abbreviation} - {self.faculty.abbreviation} - {self.name}"
