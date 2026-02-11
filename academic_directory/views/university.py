# academic_directory/views/university.py
"""University ViewSet"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response

from ..models import University
from ..serializers import UniversitySerializer, UniversityListSerializer


class UniversityViewSet(viewsets.ModelViewSet):
    """ViewSet for university CRUD operations."""

    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = University.objects.filter(is_active=True).order_by('name')

    def get_serializer_class(self):
        if self.action == 'list':
            return UniversityListSerializer
        return UniversitySerializer

    # ------------------------------------------------------------------
    # GET /api/v1/academic-directory/universities/choices/
    # Public — used by frontend dropdowns; returns minimal id+name payload
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'], permission_classes=[AllowAny],
            url_path='choices')
    def choices(self, request):
        """
        Return a lightweight list of active universities for use in dropdowns.

        Response format:
            [
                { "id": 1, "name": "University of Nigeria, Nsukka", "abbreviation": "UNN" },
                ...
            ]
        """
        qs = University.objects.filter(is_active=True).order_by('name').values(
            'id', 'name', 'abbreviation', 'state', 'type'
        )
        return Response(list(qs))