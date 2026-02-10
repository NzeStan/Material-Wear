"""
Program Duration Model

Tracks the duration of academic programs by department.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class ProgramDuration(models.Model):
    """
    Program Duration model for tracking academic program lengths by department.
    
    Different departments have different program durations:
    - 4 years: Most B.Sc programs
    - 5 years: Engineering, Architecture
    - 6 years: Medicine (MBBS)
    - 7 years: Medicine with extended programs
    
    Attributes:
        department: One-to-One relationship with Department
        duration_years: Number of years for the program (4-7)
        program_type: Type of degree (B.Sc, B.Eng, MBBS, etc.)
        notes: Optional notes about the program
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """
    
    PROGRAM_TYPES = [
        ('BSC', 'Bachelor of Science (B.Sc)'),
        ('BENG', 'Bachelor of Engineering (B.Eng)'),
        ('BTECH', 'Bachelor of Technology (B.Tech)'),
        ('BA', 'Bachelor of Arts (B.A)'),
        ('MBBS', 'Bachelor of Medicine, Bachelor of Surgery (MBBS)'),
        ('LLB', 'Bachelor of Laws (LLB)'),
        ('BARCH', 'Bachelor of Architecture (B.Arch)'),
        ('BAGRICULTURE', 'Bachelor of Agriculture (B.Agriculture)'),
        ('BPHARM', 'Bachelor of Pharmacy (B.Pharm)'),
        ('OTHER', 'Other'),
    ]
    
    department = models.OneToOneField(
        'Department',
        on_delete=models.CASCADE,
        related_name='programduration',
        help_text="Department this program duration applies to"
    )
    
    duration_years = models.PositiveIntegerField(
        validators=[
            MinValueValidator(4, message="Program duration must be at least 4 years"),
            MaxValueValidator(7, message="Program duration cannot exceed 7 years")
        ],
        help_text="Number of years for the program (4-7 years)"
    )
    
    program_type = models.CharField(
        max_length=20,
        choices=PROGRAM_TYPES,
        default='BSC',
        help_text="Type of degree program"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Optional notes about the program (e.g., special requirements)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Program Duration"
        verbose_name_plural = "Program Durations"
        ordering = ['department__faculty__university__name', 'department__name']
    
    def __str__(self):
        return f"{self.department.full_name} - {self.duration_years} years ({self.get_program_type_display()})"
    
    def clean(self):
        """Validate model data before saving."""
        from django.core.exceptions import ValidationError
        
        # Validate duration is within acceptable range
        if self.duration_years < 4 or self.duration_years > 7:
            raise ValidationError({
                'duration_years': 'Program duration must be between 4 and 7 years'
            })
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def faculty(self):
        """Return the faculty this program belongs to."""
        return self.department.faculty
    
    @property
    def university(self):
        """Return the university this program belongs to."""
        return self.department.faculty.university
