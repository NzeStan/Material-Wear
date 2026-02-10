"""Department ViewSet"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from ..models import Department
from ..serializers import DepartmentSerializer, DepartmentListSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for department CRUD operations."""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = Department.objects.select_related(
            'faculty__university'
        ).order_by('faculty__university__name', 'faculty__name', 'name')
        
        # Filter by faculty if provided
        faculty_id = self.request.query_params.get('faculty')
        if faculty_id:
            queryset = queryset.filter(faculty_id=faculty_id)
        
        # Filter by university if provided
        university_id = self.request.query_params.get('university')
        if university_id:
            queryset = queryset.filter(faculty__university_id=university_id)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DepartmentListSerializer
        return DepartmentSerializer
