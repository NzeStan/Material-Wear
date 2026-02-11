# academic_directory/views/department.py
"""Department ViewSet"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response

from ..models import Department
from ..serializers import DepartmentSerializer, DepartmentListSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for department CRUD operations."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        queryset = Department.objects.select_related(
            'faculty__university'
        ).filter(is_active=True).order_by(
            'faculty__university__name', 'faculty__name', 'name'
        )

        faculty_id = self.request.query_params.get('faculty')
        if faculty_id:
            queryset = queryset.filter(faculty_id=faculty_id)

        university_id = self.request.query_params.get('university')
        if university_id:
            queryset = queryset.filter(faculty__university_id=university_id)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return DepartmentListSerializer
        return DepartmentSerializer

    # ------------------------------------------------------------------
    # GET /api/v1/academic-directory/departments/choices/
    #       ?university=<id>  — filter by university
    #       ?faculty=<id>     — filter by faculty (more specific)
    # Public — used by frontend dropdowns; cascades with university/faculty
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'], permission_classes=[AllowAny],
            url_path='choices')
    def choices(self, request):
        """
        Return a lightweight list of active departments for use in dropdowns.

        Query params:
          ?faculty=<id>     → filter by faculty  (recommended — most specific)
          ?university=<id>  → filter by university

        Response format:
            [
                { "id": 1, "name": "Computer Science", "abbreviation": "CSC",
                  "faculty_id": 2, "faculty_abbreviation": "ENG",
                  "university_id": 1, "university_abbreviation": "UNN" },
                ...
            ]
        """
        qs = Department.objects.filter(is_active=True).select_related(
            'faculty__university'
        ).order_by('faculty__university__name', 'faculty__name', 'name')

        faculty_id = request.query_params.get('faculty')
        if faculty_id:
            qs = qs.filter(faculty_id=faculty_id)

        university_id = request.query_params.get('university')
        if university_id:
            qs = qs.filter(faculty__university_id=university_id)

        data = [
            {
                'id': d.id,
                'name': d.name,
                'abbreviation': d.abbreviation,
                'faculty_id': d.faculty_id,
                'faculty_abbreviation': d.faculty.abbreviation,
                'university_id': d.faculty.university_id,
                'university_abbreviation': d.faculty.university.abbreviation,
            }
            for d in qs
        ]
        return Response(data)