"""Program Duration Serializers"""

from rest_framework import serializers
from ..models import ProgramDuration
from .department import DepartmentListSerializer


class ProgramDurationSerializer(serializers.ModelSerializer):
    """Serializer for program duration."""
    
    department_detail = DepartmentListSerializer(source='department', read_only=True)
    program_type_display = serializers.CharField(source='get_program_type_display', read_only=True)
    
    class Meta:
        model = ProgramDuration
        fields = [
            'id', 'department', 'department_detail', 'duration_years',
            'program_type', 'program_type_display', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
