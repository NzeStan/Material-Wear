# academic_directory/views/public_submission.py
"""Public Submission View"""
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from jmw.throttling import StrictAnonRateThrottle
from ..serializers import BulkSubmissionSerializer
from ..utils.notifications import send_new_submission_email, create_submission_notification

logger = logging.getLogger(__name__)


class PublicSubmissionView(APIView):
    """
    Public API endpoint for submitting representative data.

    Accepts single or bulk submissions.
    No authentication required — rate-limited via StrictAnonRateThrottle (50/hr).
    Email notifications are sent asynchronously via background_utils threading.
    """

    permission_classes = [AllowAny]
    throttle_classes = [StrictAnonRateThrottle]

    def post(self, request):
        """
        Submit representative data.

        Request body formats:
          Single:  { "full_name": "...", "phone_number": "...", ... }
          Bulk:    { "submissions": [ {...}, {...} ] }
        """
        # Normalise to bulk format
        if 'submissions' in request.data:
            serializer = BulkSubmissionSerializer(data=request.data)
        else:
            serializer = BulkSubmissionSerializer(data={'submissions': [request.data]})

        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid submission data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = serializer.save()

        # Queue async email notification for each newly created representative
        for created_item in results.get('created', []):
            try:
                rep = created_item['representative']
                send_new_submission_email(rep)
            except Exception as exc:
                # Never let email failure break the response
                logger.error(
                    f"public_submission: failed to queue notification email "
                    f"for representative {created_item.get('representative')}: {exc}"
                )

        return Response(
            {
                'success': True,
                'message': (
                    f"Processed "
                    f"{len(results.get('created', [])) + len(results.get('updated', []))} "
                    f"submission(s)"
                ),
                'created': len(results.get('created', [])),
                'updated': len(results.get('updated', [])),
                'errors': len(results.get('errors', [])),
                'results': results,
            },
            status=status.HTTP_201_CREATED,
        )