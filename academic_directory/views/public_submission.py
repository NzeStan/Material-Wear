"""Public Submission View"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from jmw.throttling import StrictAnonRateThrottle
from ..serializers import BulkSubmissionSerializer, SingleSubmissionSerializer
from ..utils.notifications import send_new_submission_email, create_submission_notification


class PublicSubmissionView(APIView):
    """
    Public API endpoint for submitting representative data.
    
    Accepts single or bulk submissions.
    No authentication required.
    Rate limited to prevent spam.
    """
    
    permission_classes = [AllowAny]
    throttle_classes = [StrictAnonRateThrottle]
    
    def post(self, request):
        """
        Submit representative data.
        
        Request body can be:
        1. Single submission: {...}
        2. Bulk submission: {"submissions": [{...}, {...}]}
        """
        # Check if bulk submission
        if 'submissions' in request.data:
            serializer = BulkSubmissionSerializer(data=request.data)
        else:
            # Wrap single submission
            serializer = BulkSubmissionSerializer(data={'submissions': [request.data]})
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid submission data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process submissions
        results = serializer.save()
        
        # Send email notifications for new submissions (async recommended)
        for created_item in results['created']:
            try:
                rep = created_item['representative']
                # In production, use Celery for async email sending
                # send_new_submission_email.delay(rep.id)
                pass
            except:
                pass
        
        # Prepare response
        response_data = {
            'success': True,
            'message': f"Processed {len(results['created']) + len(results['updated'])} submissions",
            'created': len(results['created']),
            'updated': len(results['updated']),
            'errors': len(results['errors']),
            'results': results
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
