# academic_directory/views/faculty.py
"""Faculty ViewSet"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response

from ..models import Faculty
from ..serializers import FacultySerializer, FacultyListSerializer


class FacultyViewSet(viewsets.ModelViewSet):
    """ViewSet for faculty CRUD operations."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        queryset = Faculty.objects.select_related('university').filter(
            is_active=True
        ).order_by('university__name', 'name')

        university_id = self.request.query_params.get('university')
        if university_id:
            queryset = queryset.filter(university_id=university_id)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return FacultyListSerializer
        return FacultySerializer

    # ------------------------------------------------------------------
    # GET /api/v1/academic-directory/faculties/choices/?university=<id>
    # Public — used by frontend dropdowns; optionally filtered by university
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'], permission_classes=[AllowAny],
            url_path='choices')
    def choices(self, request):
        """
        Return a lightweight list of active faculties for use in dropdowns.
        Optionally filter by university: ?university=<id>

        Response format:
            [
                { "id": 1, "name": "Faculty of Engineering", "abbreviation": "ENG",
                  "university_id": 1, "university_abbreviation": "UNN" },
                ...
            ]
        """
        qs = Faculty.objects.filter(is_active=True).select_related('university').order_by(
            'university__name', 'name'
        )

        university_id = request.query_params.get('university')
        if university_id:
            qs = qs.filter(university_id=university_id)

        data = [
            {
                'id': f.id,
                'name': f.name,
                'abbreviation': f.abbreviation,
                'university_id': f.university_id,
                'university_abbreviation': f.university.abbreviation,
            }
            for f in qs
        ]
        return Response(data)