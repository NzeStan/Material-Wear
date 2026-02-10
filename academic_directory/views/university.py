"""University ViewSet"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from ..models import University
from ..serializers import UniversitySerializer, UniversityListSerializer


class UniversityViewSet(viewsets.ModelViewSet):
    """ViewSet for university CRUD operations."""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = University.objects.all().order_by('name')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UniversityListSerializer
        return UniversitySerializer
