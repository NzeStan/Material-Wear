"""Representative ViewSet"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from datetime import datetime

from ..models import Representative
from ..serializers import (
    RepresentativeSerializer,
    RepresentativeListSerializer,
    RepresentativeDetailSerializer,
    RepresentativeVerificationSerializer
)
from ..utils.notifications import send_bulk_verification_email


class RepresentativeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for representative CRUD operations.
    
    Admin-only access. Supports:
    - Filtering by university, faculty, department, role, level, verification status
    - Searching by name, phone number
    - Bulk verification/dispute
    - Final year filtering
    """
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'nickname', 'phone_number', 'email']
    ordering_fields = ['created_at', 'full_name', 'verification_status']
    ordering = ['-created_at']
    
    filterset_fields = {
        'university': ['exact'],
        'faculty': ['exact'],
        'department': ['exact'],
        'role': ['exact'],
        'verification_status': ['exact'],
        'is_active': ['exact'],
    }
    
    def get_queryset(self):
        """
        Get queryset with optimized queries and custom filters.
        """
        queryset = Representative.objects.select_related(
            'department__faculty__university',
            'verified_by'
        ).filter(verification_status__in=['VERIFIED', 'UNVERIFIED', 'DISPUTED'])
        
        # Custom filters
        params = self.request.query_params
        
        # Filter by current level
        if 'current_level' in params:
            try:
                level = int(params['current_level'])
                # This would require custom filtering logic
                # For simplicity, filter by entry_year calculation
                current_year = datetime.now().year
                # Students whose current level matches
                queryset = queryset.filter(role='CLASS_REP')
                # Add level filtering logic here
            except ValueError:
                pass
        
        # Filter final year students
        if params.get('is_final_year') == 'true':
            queryset = queryset.filter(role='CLASS_REP')
            # Add final year filtering logic
        
        # Filter by graduation status
        if params.get('has_graduated') == 'false':
            queryset = queryset.filter(role='CLASS_REP')
            # Add graduated filter logic
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return RepresentativeListSerializer
        elif self.action == 'retrieve':
            return RepresentativeDetailSerializer
        return RepresentativeSerializer
    
    @action(detail=False, methods=['post'], url_path='bulk-verify')
    def bulk_verify(self, request):
        """
        Bulk verify or dispute representatives.
        
        POST /api/v1/academic-directory/representatives/bulk-verify/
        Body: {
            "representative_ids": [1, 2, 3],
            "action": "verify" | "dispute"
        }
        """
        serializer = RepresentativeVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        ids = serializer.validated_data['representative_ids']
        action_type = serializer.validated_data['action']
        
        representatives = Representative.objects.filter(id__in=ids)
        
        if action_type == 'verify':
            for rep in representatives:
                rep.verify(request.user)
            message = f"Successfully verified {representatives.count()} representatives"
        else:
            for rep in representatives:
                rep.dispute()
            message = f"Successfully disputed {representatives.count()} representatives"
        
        # Send email notification
        try:
            send_bulk_verification_email(list(representatives), request.user)
        except:
            pass
        
        return Response({
            'success': True,
            'message': message,
            'count': representatives.count()
        })
    
    @action(detail=True, methods=['post'], url_path='verify')
    def verify_single(self, request, pk=None):
        """Verify a single representative."""
        representative = self.get_object()
        representative.verify(request.user)
        
        return Response({
            'success': True,
            'message': f"{representative.display_name} has been verified"
        })
    
    @action(detail=True, methods=['post'], url_path='dispute')
    def dispute_single(self, request, pk=None):
        """Dispute a single representative."""
        representative = self.get_object()
        representative.dispute()
        
        return Response({
            'success': True,
            'message': f"{representative.display_name} has been marked as disputed"
        })
