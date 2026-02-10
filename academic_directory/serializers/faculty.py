"""Faculty Serializers"""

from rest_framework import serializers
from ..models import Faculty
from .university import UniversityListSerializer


class FacultyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing faculties."""
    
    university_name = serializers.CharField(source='university.name', read_only=True)
    university_abbreviation = serializers.CharField(source='university.abbreviation', read_only=True)
    departments_count = serializers.ReadOnlyField()
    representatives_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Faculty
        fields = [
            'id', 'name', 'abbreviation', 'university', 'university_name',
            'university_abbreviation', 'departments_count', 'representatives_count',
            'is_active'
        ]


class FacultySerializer(serializers.ModelSerializer):
    """Full faculty serializer with nested university details."""
    
    university_detail = UniversityListSerializer(source='university', read_only=True)
    departments_count = serializers.ReadOnlyField()
    representatives_count = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Faculty
        fields = [
            'id', 'name', 'abbreviation', 'full_name', 'university',
            'university_detail', 'departments_count', 'representatives_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
