"""PDF Generation View"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from django.http import HttpResponse
from ..models import Representative
from ..utils.pdf_generator import generate_pdf_response, create_zip_from_pdfs


class PDFGenerationView(APIView):
    """
    Generate PDFs of representative contact lists.
    
    Supports:
    - Single PDF with filters
    - Bulk PDFs by department
    - Bulk PDFs by faculty
    - Master PDF with sections
    """
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """
        Generate PDF based on query parameters.
        
        Query params:
        - university, faculty, department, role, level: Filters
        - mode: 'single', 'bulk_department', 'bulk_faculty', 'master'
        - group_by: 'department', 'faculty', 'role' (for master mode)
        """
        # Get filters from query params
        filters = {}
        queryset = Representative.objects.filter(is_active=True, verification_status='VERIFIED')
        
        if 'university' in request.query_params:
            university_id = request.query_params['university']
            queryset = queryset.filter(university_id=university_id)
            filters['university'] = queryset.first().university.abbreviation if queryset.exists() else ''
        
        if 'faculty' in request.query_params:
            faculty_id = request.query_params['faculty']
            queryset = queryset.filter(faculty_id=faculty_id)
            filters['faculty'] = queryset.first().faculty.name if queryset.exists() else ''
        
        if 'department' in request.query_params:
            department_id = request.query_params['department']
            queryset = queryset.filter(department_id=department_id)
            filters['department'] = queryset.first().department.name if queryset.exists() else ''
        
        if 'role' in request.query_params:
            role = request.query_params['role']
            queryset = queryset.filter(role=role)
            filters['role'] = role
        
        # Optimize query
        queryset = queryset.select_related('department__faculty__university')
        
        # Get generation mode
        mode = request.query_params.get('mode', 'single')
        
        try:
            if mode in ['bulk_department', 'bulk_faculty']:
                # Generate multiple PDFs and return as ZIP
                pdf_result, filename = generate_pdf_response(queryset, filters, mode=mode)
                zip_buffer = create_zip_from_pdfs(pdf_result)
                
                response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            
            else:
                # Generate single PDF
                group_by = request.query_params.get('group_by', 'department')
                pdf_buffer, filename = generate_pdf_response(
                    queryset, filters, mode=mode, group_by=group_by
                )
                
                response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        
        except Exception as e:
            return Response(
                {'error': f'PDF generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
