"""Bulk Submission Serializers"""

from rest_framework import serializers
from ..models import Representative
from .representative import RepresentativeDetailSerializer


class SingleSubmissionSerializer(serializers.Serializer):
    """Serializer for a single representative submission."""
    
    full_name = serializers.CharField(max_length=255)
    nickname = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    phone_number = serializers.CharField(max_length=20)
    whatsapp_number = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    department_id = serializers.UUIDField()  # Changed from IntegerField to UUIDField
    role = serializers.ChoiceField(choices=Representative.ROLES)
    entry_year = serializers.IntegerField(required=False, allow_null=True)
    tenure_start_year = serializers.IntegerField(required=False, allow_null=True)
    submission_source = serializers.ChoiceField(
        choices=Representative.SUBMISSION_SOURCES,
        default='WEBSITE'
    )
    submission_source_other = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True
    )
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class BulkSubmissionSerializer(serializers.Serializer):
    """Serializer for bulk representative submissions."""
    
    submissions = serializers.ListField(
        child=SingleSubmissionSerializer(),
        min_length=1,
        max_length=100,
        help_text="List of representative submissions (max 100)"
    )
    
    def create(self, validated_data):
        """Process bulk submissions with deduplication."""
        from ..utils.deduplication import handle_submission_with_deduplication
        from ..utils.notifications import create_submission_notification
        
        results = {
            'created': [],
            'updated': [],
            'errors': []
        }
        
        for submission_data in validated_data['submissions']:
            try:
                representative, is_new, changes = handle_submission_with_deduplication(submission_data)
                
                if is_new:
                    results['created'].append({
                        'representative': RepresentativeDetailSerializer(representative).data,
                        'phone_number': representative.phone_number
                    })
                    # Create notification for new submission
                    create_submission_notification(representative)
                else:
                    results['updated'].append({
                        'representative': RepresentativeDetailSerializer(representative).data,
                        'phone_number': representative.phone_number,
                        'changes': changes
                    })
            
            except Exception as e:
                results['errors'].append({
                    'phone_number': submission_data.get('phone_number'),
                    'error': str(e)
                })
        
        return results