"""
PDF Generator Utility

Handles PDF generation for representative contact lists using WeasyPrint.
"""

from io import BytesIO
from typing import Optional, Dict, Any, List
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML, CSS
from weasyprint.document import FontConfiguration

def generate_single_pdf(queryset, filters: Dict[str, Any], title: Optional[str] = None) -> BytesIO:
    """
    Generate a single PDF containing filtered representatives.
    
    Args:
        queryset: QuerySet of Representative instances
        filters: Dictionary of applied filters for display
        title: Optional custom title for the PDF
    
    Returns:
        BytesIO: PDF file buffer
    
    Example:
        >>> reps = Representative.objects.filter(university__abbreviation='UNIBEN')
        >>> filters = {'university': 'UNIBEN', 'faculty': 'Engineering'}
        >>> pdf_buffer = generate_single_pdf(reps, filters, "UNIBEN Engineering Reps")
    """
    # Prepare context
    context = {
        'representatives': queryset,
        'filters': filters,
        'title': title or "Academic Representatives Directory",
        'generated_at': timezone.now(),
        'total_count': queryset.count(),
    }
    
    # Group representatives by role for better organization
    context['class_reps'] = queryset.filter(role='CLASS_REP')
    context['dept_presidents'] = queryset.filter(role='DEPT_PRESIDENT')
    context['faculty_presidents'] = queryset.filter(role='FACULTY_PRESIDENT')
    
    # Render HTML template
    html_string = render_to_string(
        'academic_directory/pdf/single_representatives.html',
        context
    )
    
    # Generate PDF
    pdf_buffer = BytesIO()
    font_config = FontConfiguration()
    
    HTML(string=html_string).write_pdf(
        pdf_buffer,
        font_config=font_config
    )
    
    pdf_buffer.seek(0)
    return pdf_buffer


def generate_bulk_pdfs_by_department(queryset, filters: Dict[str, Any]) -> Dict[str, BytesIO]:
    """
    Generate multiple PDFs, one per department.
    
    Args:
        queryset: QuerySet of Representative instances
        filters: Dictionary of applied filters
    
    Returns:
        Dict[str, BytesIO]: Dictionary mapping department names to PDF buffers
    
    Example:
        >>> reps = Representative.objects.filter(faculty__abbreviation='ENG')
        >>> pdfs = generate_bulk_pdfs_by_department(reps, {'faculty': 'Engineering'})
        >>> for dept_name, pdf_buffer in pdfs.items():
        ...     # Save or send each PDF
        ...     pass
    """
    from ..models import Department
    
    pdf_dict = {}
    
    # Get unique departments from queryset
    department_ids = queryset.values_list('department', flat=True).distinct()
    departments = Department.objects.filter(id__in=department_ids).select_related(
        'faculty__university'
    )
    
    for department in departments:
        # Filter representatives for this department
        dept_reps = queryset.filter(department=department)
        
        # Generate PDF for this department
        dept_filters = filters.copy()
        dept_filters['department'] = department.name
        
        title = f"{department.full_name} - Representatives"
        pdf_buffer = generate_single_pdf(dept_reps, dept_filters, title)
        
        # Use department full name as key
        pdf_dict[department.full_name] = pdf_buffer
    
    return pdf_dict


def generate_bulk_pdfs_by_faculty(queryset, filters: Dict[str, Any]) -> Dict[str, BytesIO]:
    """
    Generate multiple PDFs, one per faculty.
    
    Args:
        queryset: QuerySet of Representative instances
        filters: Dictionary of applied filters
    
    Returns:
        Dict[str, BytesIO]: Dictionary mapping faculty names to PDF buffers
    """
    from ..models import Faculty
    
    pdf_dict = {}
    
    # Get unique faculties from queryset
    faculty_ids = queryset.values_list('faculty', flat=True).distinct()
    faculties = Faculty.objects.filter(id__in=faculty_ids).select_related('university')
    
    for faculty in faculties:
        # Filter representatives for this faculty
        faculty_reps = queryset.filter(faculty=faculty)
        
        # Generate PDF for this faculty
        faculty_filters = filters.copy()
        faculty_filters['faculty'] = faculty.name
        
        title = f"{faculty.full_name} - Representatives"
        pdf_buffer = generate_single_pdf(faculty_reps, faculty_filters, title)
        
        # Use faculty full name as key
        pdf_dict[faculty.full_name] = pdf_buffer
    
    return pdf_dict


def generate_master_pdf_with_sections(queryset, filters: Dict[str, Any], 
                                      group_by: str = 'department') -> BytesIO:
    """
    Generate a single master PDF with sections for each group.
    
    Args:
        queryset: QuerySet of Representative instances
        filters: Dictionary of applied filters
        group_by: How to group sections ('department', 'faculty', or 'role')
    
    Returns:
        BytesIO: PDF file buffer
    
    Example:
        >>> reps = Representative.objects.filter(university__abbreviation='UI')
        >>> pdf = generate_master_pdf_with_sections(reps, {'university': 'UI'}, 'faculty')
    """
    # Prepare context
    context = {
        'representatives': queryset,
        'filters': filters,
        'title': "Academic Representatives Directory - Complete",
        'generated_at': timezone.now(),
        'total_count': queryset.count(),
        'group_by': group_by,
    }
    
    # Group representatives based on group_by parameter
    if group_by == 'department':
        from ..models import Department
        department_ids = queryset.values_list('department', flat=True).distinct()
        departments = Department.objects.filter(id__in=department_ids).select_related(
            'faculty__university'
        ).order_by('faculty__university__name', 'faculty__name', 'name')
        
        sections = []
        for dept in departments:
            dept_reps = queryset.filter(department=dept)
            sections.append({
                'title': dept.full_name,
                'representatives': dept_reps,
                'count': dept_reps.count(),
            })
        context['sections'] = sections
    
    elif group_by == 'faculty':
        from ..models import Faculty
        faculty_ids = queryset.values_list('faculty', flat=True).distinct()
        faculties = Faculty.objects.filter(id__in=faculty_ids).select_related(
            'university'
        ).order_by('university__name', 'name')
        
        sections = []
        for faculty in faculties:
            faculty_reps = queryset.filter(faculty=faculty)
            sections.append({
                'title': faculty.full_name,
                'representatives': faculty_reps,
                'count': faculty_reps.count(),
            })
        context['sections'] = sections
    
    elif group_by == 'role':
        sections = [
            {
                'title': 'Class Representatives',
                'representatives': queryset.filter(role='CLASS_REP'),
                'count': queryset.filter(role='CLASS_REP').count(),
            },
            {
                'title': 'Department Presidents',
                'representatives': queryset.filter(role='DEPT_PRESIDENT'),
                'count': queryset.filter(role='DEPT_PRESIDENT').count(),
            },
            {
                'title': 'Faculty Presidents',
                'representatives': queryset.filter(role='FACULTY_PRESIDENT'),
                'count': queryset.filter(role='FACULTY_PRESIDENT').count(),
            },
        ]
        # Remove empty sections
        context['sections'] = [s for s in sections if s['count'] > 0]
    
    else:
        raise ValueError(f"Invalid group_by parameter: {group_by}")
    
    # Render HTML template
    html_string = render_to_string(
        'academic_directory/pdf/bulk_representatives.html',
        context
    )
    
    # Generate PDF
    pdf_buffer = BytesIO()
    font_config = FontConfiguration()
    
    HTML(string=html_string).write_pdf(
        pdf_buffer,
        font_config=font_config
    )
    
    pdf_buffer.seek(0)
    return pdf_buffer


def get_pdf_filename(filters: Dict[str, Any], extension: str = '.pdf') -> str:
    """
    Generate appropriate filename based on filters.
    
    Args:
        filters: Dictionary of applied filters
        extension: File extension (default: '.pdf')
    
    Returns:
        str: Generated filename
    
    Example:
        >>> filters = {'university': 'UNIBEN', 'faculty': 'Engineering', 'role': 'CLASS_REP'}
        >>> filename = get_pdf_filename(filters)
        'UNIBEN_Engineering_CLASS_REP_2025-02-10.pdf'
    """
    from django.utils.text import slugify
    
    parts = []
    
    # Add filter values to filename
    for key in ['university', 'faculty', 'department', 'role', 'level']:
        if key in filters and filters[key]:
            value = str(filters[key])
            # Convert to slug-friendly format
            parts.append(slugify(value).replace('-', '_'))
    
    # Add date
    date_str = timezone.now().strftime('%Y-%m-%d')
    
    # Combine parts
    if parts:
        filename = f"{'_'.join(parts)}_{date_str}{extension}"
    else:
        filename = f"representatives_{date_str}{extension}"
    
    return filename


def generate_pdf_response(queryset, filters: Dict[str, Any], 
                          mode: str = 'single', **kwargs):
    """
    Generate PDF and prepare HTTP response.
    
    Args:
        queryset: QuerySet of Representative instances
        filters: Dictionary of applied filters
        mode: 'single', 'bulk_department', 'bulk_faculty', or 'master'
        **kwargs: Additional arguments passed to specific generators
    
    Returns:
        Tuple[BytesIO or Dict, str]: (pdf_buffer(s), filename)
    
    Example:
        >>> from django.http import HttpResponse
        >>> reps = Representative.objects.filter(is_active=True)
        >>> pdf_buffer, filename = generate_pdf_response(reps, {}, mode='single')
        >>> response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        >>> response['Content-Disposition'] = f'attachment; filename="{filename}"'
        >>> return response
    """
    if mode == 'single':
        pdf_buffer = generate_single_pdf(queryset, filters, kwargs.get('title'))
        filename = get_pdf_filename(filters)
        return pdf_buffer, filename
    
    elif mode == 'bulk_department':
        pdf_dict = generate_bulk_pdfs_by_department(queryset, filters)
        return pdf_dict, 'representatives_by_department.zip'
    
    elif mode == 'bulk_faculty':
        pdf_dict = generate_bulk_pdfs_by_faculty(queryset, filters)
        return pdf_dict, 'representatives_by_faculty.zip'
    
    elif mode == 'master':
        group_by = kwargs.get('group_by', 'department')
        pdf_buffer = generate_master_pdf_with_sections(queryset, filters, group_by)
        filename = f"representatives_master_{group_by}_{timezone.now().strftime('%Y-%m-%d')}.pdf"
        return pdf_buffer, filename
    
    else:
        raise ValueError(f"Invalid mode: {mode}")


def create_zip_from_pdfs(pdf_dict: Dict[str, BytesIO]) -> BytesIO:
    """
    Create a ZIP file containing multiple PDFs.
    
    Args:
        pdf_dict: Dictionary mapping filenames to PDF buffers
    
    Returns:
        BytesIO: ZIP file buffer
    """
    import zipfile
    from django.utils.text import slugify
    
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for name, pdf_buffer in pdf_dict.items():
            # Create safe filename
            safe_name = slugify(name).replace('-', '_') + '.pdf'
            
            # Add PDF to ZIP
            zip_file.writestr(safe_name, pdf_buffer.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer
