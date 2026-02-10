"""Representative Serializers"""

from rest_framework import serializers
from ..models import Representative
from ..utils.validators import validate_representative_data, normalize_phone_number
from .department import DepartmentListSerializer


class RepresentativeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing representatives."""
    
    display_name = serializers.ReadOnlyField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    university_name = serializers.CharField(source='university.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    current_level_display = serializers.ReadOnlyField()
    
    class Meta:
        model = Representative
        fields = [
            'id', 'display_name', 'full_name', 'phone_number',
            'role', 'role_display', 'department_name', 'faculty_name',
            'university_name', 'current_level_display', 'verification_status',
            'verification_status_display', 'is_active', 'created_at'
        ]


class RepresentativeDetailSerializer(serializers.ModelSerializer):
    """Full serializer with all representative details and computed fields."""
    
    display_name = serializers.ReadOnlyField()
    department_detail = DepartmentListSerializer(source='department', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    university_name = serializers.CharField(source='university.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    submission_source_display = serializers.CharField(source='get_submission_source_display', read_only=True)
    
    # Computed fields
    current_level = serializers.ReadOnlyField()
    current_level_display = serializers.ReadOnlyField()
    is_final_year = serializers.ReadOnlyField()
    expected_graduation_year = serializers.ReadOnlyField()
    has_graduated = serializers.ReadOnlyField()
    
    verified_by_username = serializers.CharField(source='verified_by.username', read_only=True)
    
    class Meta:
        model = Representative
        fields = [
            'id', 'full_name', 'nickname', 'display_name',
            'phone_number', 'whatsapp_number', 'email',
            'department', 'department_detail', 'faculty_name', 'university_name',
            'role', 'role_display', 'entry_year', 'tenure_start_year',
            'current_level', 'current_level_display', 'is_final_year',
            'expected_graduation_year', 'has_graduated',
            'submission_source', 'submission_source_display', 'submission_source_other',
            'verification_status', 'verification_status_display',
            'verified_by', 'verified_by_username', 'verified_at',
            'notes', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'verified_by', 'verified_at', 'created_at', 'updated_at',
            'current_level', 'is_final_year', 'expected_graduation_year', 'has_graduated'
        ]


class RepresentativeSerializer(serializers.ModelSerializer):
    """Main serializer for creating and updating representatives."""
    
    class Meta:
        model = Representative
        fields = [
            'id', 'full_name', 'nickname', 'phone_number', 'whatsapp_number', 'email',
            'department', 'role', 'entry_year', 'tenure_start_year',
            'submission_source', 'submission_source_other', 'notes'
        ]
    
    def validate(self, attrs):
        """Comprehensive validation using utility functions."""
        # Normalize phone number
        if 'phone_number' in attrs:
            try:
                attrs['phone_number'] = normalize_phone_number(attrs['phone_number'])
            except Exception as e:
                raise serializers.ValidationError({'phone_number': str(e)})
        
        # Validate all data
        is_valid, errors = validate_representative_data(attrs)
        if not is_valid:
            raise serializers.ValidationError(errors)
        
        return attrs
    
    def to_representation(self, instance):
        """Use detailed serializer for representation."""
        return RepresentativeDetailSerializer(instance, context=self.context).data


class RepresentativeVerificationSerializer(serializers.Serializer):
    """Serializer for bulk verification actions."""
    
    representative_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="List of representative IDs to verify"
    )
    action = serializers.ChoiceField(
        choices=['verify', 'dispute'],
        help_text="Action to perform: verify or dispute"
    )
