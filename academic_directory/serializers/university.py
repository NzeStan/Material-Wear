"""University Serializers"""

from rest_framework import serializers
from ..models import University


class UniversityListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing universities."""
    
    faculties_count = serializers.ReadOnlyField()
    departments_count = serializers.ReadOnlyField()
    representatives_count = serializers.ReadOnlyField()
    
    class Meta:
        model = University
        fields = [
            'id', 'name', 'abbreviation', 'state', 'type',
            'is_active', 'faculties_count', 'departments_count',
            'representatives_count'
        ]


class UniversitySerializer(serializers.ModelSerializer):
    """Full university serializer with all details."""
    
    faculties_count = serializers.ReadOnlyField()
    departments_count = serializers.ReadOnlyField()
    representatives_count = serializers.ReadOnlyField()
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = University
        fields = [
            'id', 'name', 'abbreviation', 'state', 'state_display',
            'type', 'type_display', 'is_active', 'faculties_count',
            'departments_count', 'representatives_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
