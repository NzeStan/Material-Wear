"""Department Serializers"""

from rest_framework import serializers
from ..models import Department
from .faculty import FacultyListSerializer


class DepartmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing departments."""
    
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    university_name = serializers.CharField(source='faculty.university.name', read_only=True)
    representatives_count = serializers.ReadOnlyField()
    program_duration = serializers.ReadOnlyField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'abbreviation', 'faculty', 'faculty_name',
            'university_name', 'program_duration', 'representatives_count',
            'is_active'
        ]


class DepartmentSerializer(serializers.ModelSerializer):
    """Full department serializer with nested faculty and university."""
    
    faculty_detail = FacultyListSerializer(source='faculty', read_only=True)
    university_name = serializers.CharField(source='faculty.university.name', read_only=True)
    university_abbreviation = serializers.CharField(source='faculty.university.abbreviation', read_only=True)
    representatives_count = serializers.ReadOnlyField()
    program_duration = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'abbreviation', 'full_name', 'faculty',
            'faculty_detail', 'university_name', 'university_abbreviation',
            'program_duration', 'representatives_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
