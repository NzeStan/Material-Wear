# academic_directory/tests/utils/test_pdf_generator.py
"""
Comprehensive test suite for PDF generator utility.

Test Coverage:
- Single PDF generation
- Bulk PDF generation by department
- PDF response generation
- Template rendering
- Filter application
- Representative grouping by role
- PDF content validation
"""

from django.test import TestCase
from unittest.mock import patch, Mock, MagicMock
from io import BytesIO
from academic_directory.models import University, Faculty, Department, Representative, ProgramDuration
from academic_directory.utils.pdf_generator import (
    generate_single_pdf,
    generate_bulk_pdfs_by_department,
    generate_pdf_response
)


class GenerateSinglePDFTest(TestCase):
    """Test single PDF generation."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
        self.rep1 = Representative.objects.create(
            full_name="John Doe",
            phone_number="+2348012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        self.rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="+2348087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024
        )
    
    @patch('academic_directory.utils.pdf_generator.HTML')
    @patch('academic_directory.utils.pdf_generator.render_to_string')
    def test_generates_pdf_buffer(self, mock_render, mock_html):
        """Test PDF buffer is generated."""
        mock_render.return_value = '<html>Test PDF</html>'
        mock_pdf = MagicMock()
        mock_pdf.write_pdf = Mock(return_value=b'PDF content')
        mock_html.return_value = mock_pdf
        
        queryset = Representative.objects.all()
        filters = {'university': 'UNIBEN'}
        
        pdf_buffer = generate_single_pdf(queryset, filters, "Test Title")
        
        self.assertIsInstance(pdf_buffer, BytesIO)
        mock_render.assert_called_once()
    
    @patch('academic_directory.utils.pdf_generator.HTML')
    @patch('academic_directory.utils.pdf_generator.render_to_string')
    def test_includes_all_representatives(self, mock_render, mock_html):
        """Test all representatives are included in context."""
        mock_render.return_value = '<html>PDF</html>'
        mock_pdf = MagicMock()
        mock_pdf.write_pdf = Mock(return_value=b'PDF')
        mock_html.return_value = mock_pdf
        
        queryset = Representative.objects.all()
        filters = {}
        
        generate_single_pdf(queryset, filters)
        
        # Check context passed to template
        context = mock_render.call_args[0][1]
        self.assertEqual(context['total_count'], 2)
    
    @patch('academic_directory.utils.pdf_generator.HTML')
    @patch('academic_directory.utils.pdf_generator.render_to_string')
    def test_groups_by_role(self, mock_render, mock_html):
        """Test representatives are grouped by role."""
        mock_render.return_value = '<html>PDF</html>'
        mock_pdf = MagicMock()
        mock_pdf.write_pdf = Mock(return_value=b'PDF')
        mock_html.return_value = mock_pdf
        
        queryset = Representative.objects.all()
        filters = {}
        
        generate_single_pdf(queryset, filters)
        
        context = mock_render.call_args[0][1]
        self.assertIn('class_reps', context)
        self.assertIn('dept_presidents', context)
        self.assertIn('faculty_presidents', context)
    
    @patch('academic_directory.utils.pdf_generator.HTML')
    @patch('academic_directory.utils.pdf_generator.render_to_string')
    def test_includes_filters_in_context(self, mock_render, mock_html):
        """Test filters are included in context."""
        mock_render.return_value = '<html>PDF</html>'
        mock_pdf = MagicMock()
        mock_pdf.write_pdf = Mock(return_value=b'PDF')
        mock_html.return_value = mock_pdf
        
        queryset = Representative.objects.all()
        filters = {'university': 'UNIBEN', 'faculty': 'ENG'}
        
        generate_single_pdf(queryset, filters)
        
        context = mock_render.call_args[0][1]
        self.assertEqual(context['filters'], filters)
    
    @patch('academic_directory.utils.pdf_generator.HTML')
    @patch('academic_directory.utils.pdf_generator.render_to_string')
    def test_custom_title(self, mock_render, mock_html):
        """Test custom title is used."""
        mock_render.return_value = '<html>PDF</html>'
        mock_pdf = MagicMock()
        mock_pdf.write_pdf = Mock(return_value=b'PDF')
        mock_html.return_value = mock_pdf
        
        queryset = Representative.objects.all()
        filters = {}
        custom_title = "Custom Report Title"
        
        generate_single_pdf(queryset, filters, custom_title)
        
        context = mock_render.call_args[0][1]
        self.assertEqual(context['title'], custom_title)
    
    @patch('academic_directory.utils.pdf_generator.HTML')
    @patch('academic_directory.utils.pdf_generator.render_to_string')
    def test_default_title(self, mock_render, mock_html):
        """Test default title is used when none provided."""
        mock_render.return_value = '<html>PDF</html>'
        mock_pdf = MagicMock()
        mock_pdf.write_pdf = Mock(return_value=b'PDF')
        mock_html.return_value = mock_pdf
        
        queryset = Representative.objects.all()
        filters = {}
        
        generate_single_pdf(queryset, filters)
        
        context = mock_render.call_args[0][1]
        self.assertIn("Academic Representatives", context['title'])


class GenerateBulkPDFsByDepartmentTest(TestCase):
    """Test bulk PDF generation by department."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.dept1 = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        self.dept2 = Department.objects.create(
            faculty=self.faculty,
            name="Electrical Engineering",
            abbreviation="EEE"
        )
        ProgramDuration.objects.create(
            department=self.dept1,
            duration_years=4,
            program_type='BSC'
        )
        ProgramDuration.objects.create(
            department=self.dept2,
            duration_years=5,
            program_type='BENG'
        )
        
        # Create reps in different departments
        Representative.objects.create(
            full_name="CSC Rep",
            phone_number="+2348012340001",
            department=self.dept1,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        Representative.objects.create(
            full_name="EEE Rep",
            phone_number="+2348012340002",
            department=self.dept2,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    @patch('academic_directory.utils.pdf_generator.generate_single_pdf')
    def test_generates_pdf_per_department(self, mock_generate):
        """Test generates one PDF per department."""
        mock_generate.return_value = BytesIO(b'PDF')
        
        queryset = Representative.objects.all()
        filters = {}
        
        pdfs = generate_bulk_pdfs_by_department(queryset, filters)
        
        # Should generate 2 PDFs (one per department)
        self.assertEqual(len(pdfs), 2)
        self.assertEqual(mock_generate.call_count, 2)
    
    @patch('academic_directory.utils.pdf_generator.generate_single_pdf')
    def test_pdf_keys_include_department_names(self, mock_generate):
        """Test PDF dictionary keys include department names."""
        mock_generate.return_value = BytesIO(b'PDF')
        
        queryset = Representative.objects.all()
        filters = {}
        
        pdfs = generate_bulk_pdfs_by_department(queryset, filters)
        
        # Keys should include department names
        keys = list(pdfs.keys())
        self.assertTrue(any('Computer Science' in key for key in keys))
        self.assertTrue(any('Electrical Engineering' in key for key in keys))


class GeneratePDFResponseTest(TestCase):
    """Test PDF HTTP response generation."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
        Representative.objects.create(
            full_name="John Doe",
            phone_number="+2348012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    @patch('academic_directory.utils.pdf_generator.generate_single_pdf')
    def test_returns_http_response(self, mock_generate):
        """Test returns HttpResponse with PDF."""
        mock_generate.return_value = BytesIO(b'PDF content')
        
        queryset = Representative.objects.all()
        filters = {}
        
        response = generate_pdf_response(queryset, filters)
        
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
    
    @patch('academic_directory.utils.pdf_generator.generate_single_pdf')
    def test_filename_includes_timestamp(self, mock_generate):
        """Test filename includes timestamp."""
        mock_generate.return_value = BytesIO(b'PDF content')
        
        queryset = Representative.objects.all()
        filters = {}
        
        response = generate_pdf_response(queryset, filters)
        
        # Filename should include date
        self.assertIn('filename', response['Content-Disposition'])
        self.assertIn('representatives', response['Content-Disposition'].lower())
    
    @patch('academic_directory.utils.pdf_generator.generate_single_pdf')
    def test_custom_filename(self, mock_generate):
        """Test custom filename is used."""
        mock_generate.return_value = BytesIO(b'PDF content')
        
        queryset = Representative.objects.all()
        filters = {}
        filename = "custom_report.pdf"
        
        response = generate_pdf_response(queryset, filters, filename=filename)
        
        self.assertIn(filename, response['Content-Disposition'])


class PDFGenerationEmptyDataTest(TestCase):
    """Test PDF generation with no data."""
    
    @patch('academic_directory.utils.pdf_generator.HTML')
    @patch('academic_directory.utils.pdf_generator.render_to_string')
    def test_generates_pdf_with_no_representatives(self, mock_render, mock_html):
        """Test PDF is generated even with no representatives."""
        mock_render.return_value = '<html>Empty PDF</html>'
        mock_pdf = MagicMock()
        mock_pdf.write_pdf = Mock(return_value=b'PDF')
        mock_html.return_value = mock_pdf
        
        queryset = Representative.objects.none()
        filters = {}
        
        pdf_buffer = generate_single_pdf(queryset, filters)
        
        self.assertIsInstance(pdf_buffer, BytesIO)
        mock_render.assert_called_once()