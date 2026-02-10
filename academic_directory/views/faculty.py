"""Faculty ViewSet"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from ..models import Faculty
from ..serializers import FacultySerializer, FacultyListSerializer


class FacultyViewSet(viewsets.ModelViewSet):
    """ViewSet for faculty CRUD operations."""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = Faculty.objects.select_related('university').order_by('university__name', 'name')
        
        # Filter by university if provided
        university_id = self.request.query_params.get('university')
        if university_id:
            queryset = queryset.filter(university_id=university_id)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return FacultyListSerializer
        return FacultySerializer
