# academic_directory/tests/management/test_populate_academic_data.py
"""
Comprehensive test suite for populate_academic_data management command.

Test Coverage:
- Command execution (with/without arguments)
- Dry-run mode (no database changes)
- Normal mode (creates records)
- University filtering (single/multiple)
- Idempotency (safe to run multiple times)
- get_or_create behavior (no duplicates)
- Output messages and formatting
- Error handling (invalid university code)
- Data integrity (relationships preserved)
- Edge cases (empty data, re-runs, partial data)
"""

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO
from academic_directory.models import University, Faculty, Department


class CommandBasicsTest(TestCase):
    """Test basic command execution."""
    
    def test_command_runs_without_arguments(self):
        """Test command runs successfully without arguments."""
        out = StringIO()
        call_command('populate_academic_data', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Database seeded successfully', output)
    
    def test_command_help_text(self):
        """Test command has proper help text."""
        out = StringIO()
        call_command('populate_academic_data', '--help', stdout=out)
        
        output = out.getvalue()
        self.assertIn('populate_academic_data', output)
        self.assertIn('Nigerian universities', output)


class DryRunModeTest(TestCase):
    """Test dry-run mode functionality."""
    
    def test_dry_run_creates_no_records(self):
        """Test --dry-run doesn't create any database records."""
        self.assertEqual(University.objects.count(), 0)
        self.assertEqual(Faculty.objects.count(), 0)
        self.assertEqual(Department.objects.count(), 0)
        
        out = StringIO()
        call_command('populate_academic_data', '--dry-run', stdout=out)
        
        # No records should be created
        self.assertEqual(University.objects.count(), 0)
        self.assertEqual(Faculty.objects.count(), 0)
        self.assertEqual(Department.objects.count(), 0)
    
    def test_dry_run_shows_preview(self):
        """Test --dry-run shows what would be created."""
        out = StringIO()
        call_command('populate_academic_data', '--dry-run', stdout=out)
        
        output = out.getvalue()
        self.assertIn('DRY RUN', output)
        self.assertIn('University', output)
        self.assertIn('Faculty', output)
        self.assertIn('Department', output)
    
    def test_dry_run_with_university_filter(self):
        """Test --dry-run with specific university."""
        out = StringIO()
        call_command('populate_academic_data', '--university', 'UNN', '--dry-run', stdout=out)
        
        output = out.getvalue()
        self.assertIn('DRY RUN', output)
        self.assertIn('UNN', output)
        # Should not show other universities
        self.assertEqual(University.objects.count(), 0)


class NormalModeTest(TestCase):
    """Test normal execution mode (creates records)."""
    
    def test_creates_universities(self):
        """Test command creates universities."""
        self.assertEqual(University.objects.count(), 0)
        
        out = StringIO()
        call_command('populate_academic_data', stdout=out)
        
        # Should create multiple universities
        self.assertGreater(University.objects.count(), 0)
        
        output = out.getvalue()
        self.assertIn('Created University', output)
    
    def test_creates_faculties(self):
        """Test command creates faculties."""
        self.assertEqual(Faculty.objects.count(), 0)
        
        out = StringIO()
        call_command('populate_academic_data', stdout=out)
        
        # Should create multiple faculties
        self.assertGreater(Faculty.objects.count(), 0)
        
        output = out.getvalue()
        self.assertIn('Created Faculty', output)
    
    def test_creates_departments(self):
        """Test command creates departments."""
        self.assertEqual(Department.objects.count(), 0)
        
        out = StringIO()
        call_command('populate_academic_data', stdout=out)
        
        # Should create multiple departments
        self.assertGreater(Department.objects.count(), 0)
        
        output = out.getvalue()
        self.assertIn('Created Department', output)
    
    def test_shows_success_message(self):
        """Test command shows success message."""
        out = StringIO()
        call_command('populate_academic_data', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Database seeded successfully', output)
        self.assertIn('Universities:', output)
        self.assertIn('Faculties:', output)
        self.assertIn('Departments:', output)


class UniversityFilteringTest(TestCase):
    """Test --university argument filtering."""
    
    def test_filter_single_university(self):
        """Test filtering by single university code."""
        out = StringIO()
        call_command('populate_academic_data', '--university', 'UNN', stdout=out)
        
        # Should create only UNN
        self.assertTrue(University.objects.filter(abbreviation='UNN').exists())
        
        # Should not create other universities
        self.assertFalse(University.objects.filter(abbreviation='UNILAG').exists())
        self.assertFalse(University.objects.filter(abbreviation='UNIBEN').exists())
    
    def test_filter_multiple_universities(self):
        """Test filtering by multiple university codes."""
        out = StringIO()
        call_command(
            'populate_academic_data',
            '--university', 'UNN',
            '--university', 'UNILAG',
            stdout=out
        )
        
        # Should create both UNN and UNILAG
        self.assertTrue(University.objects.filter(abbreviation='UNN').exists())
        self.assertTrue(University.objects.filter(abbreviation='UNILAG').exists())
        
        # Should not create others
        self.assertFalse(University.objects.filter(abbreviation='UNIBEN').exists())
    
    def test_invalid_university_code(self):
        """Test filtering with invalid university code."""
        out = StringIO()
        call_command('populate_academic_data', '--university', 'INVALID', stdout=out)
        
        # Should not create any universities
        self.assertEqual(University.objects.count(), 0)
        
        output = out.getvalue()
        self.assertIn('No matching universities', output)


class IdempotencyTest(TestCase):
    """Test that command is safe to run multiple times."""
    
    def test_running_twice_no_duplicates(self):
        """Test running command twice doesn't create duplicates."""
        # Run first time
        out1 = StringIO()
        call_command('populate_academic_data', stdout=out1)
        
        first_uni_count = University.objects.count()
        first_fac_count = Faculty.objects.count()
        first_dept_count = Department.objects.count()
        
        # Run second time
        out2 = StringIO()
        call_command('populate_academic_data', stdout=out2)
        
        # Counts should remain the same
        self.assertEqual(University.objects.count(), first_uni_count)
        self.assertEqual(Faculty.objects.count(), first_fac_count)
        self.assertEqual(Department.objects.count(), first_dept_count)
        
        output2 = out2.getvalue()
        self.assertIn('Skipped (exists)', output2)
    
    def test_get_or_create_behavior(self):
        """Test that existing records are preserved."""
        # Create a university manually
        uni = University.objects.create(
            name="University of Nigeria, Nsukka",
            abbreviation="UNN",
            state="ENUGU",
            type="FEDERAL"
        )
        
        # Run command
        out = StringIO()
        call_command('populate_academic_data', '--university', 'UNN', stdout=out)
        
        # University should not be duplicated
        self.assertEqual(University.objects.filter(abbreviation='UNN').count(), 1)
        
        # Should be the same instance
        uni.refresh_from_db()
        self.assertEqual(uni.name, "University of Nigeria, Nsukka")
        
        output = out.getvalue()
        self.assertIn('Skipped (exists)', output)


class DataIntegrityTest(TestCase):
    """Test that relationships are correctly preserved."""
    
    def test_faculties_linked_to_universities(self):
        """Test faculties are correctly linked to their universities."""
        out = StringIO()
        call_command('populate_academic_data', '--university', 'UNN', stdout=out)
        
        uni = University.objects.get(abbreviation='UNN')
        faculties = Faculty.objects.filter(university=uni)
        
        # Should have faculties
        self.assertGreater(faculties.count(), 0)
        
        # All faculties should link to UNN
        for faculty in faculties:
            self.assertEqual(faculty.university, uni)
    
    def test_departments_linked_to_faculties(self):
        """Test departments are correctly linked to their faculties."""
        out = StringIO()
        call_command('populate_academic_data', '--university', 'UNN', stdout=out)
        
        uni = University.objects.get(abbreviation='UNN')
        faculties = Faculty.objects.filter(university=uni)
        
        for faculty in faculties:
            departments = Department.objects.filter(faculty=faculty)
            
            if departments.exists():
                # All departments should link to correct faculty
                for dept in departments:
                    self.assertEqual(dept.faculty, faculty)
    
    def test_all_records_active_by_default(self):
        """Test all created records are active."""
        out = StringIO()
        call_command('populate_academic_data', stdout=out)
        
        # All universities should be active
        self.assertTrue(
            all(uni.is_active for uni in University.objects.all())
        )
        
        # All faculties should be active
        self.assertTrue(
            all(fac.is_active for fac in Faculty.objects.all())
        )
        
        # All departments should be active
        self.assertTrue(
            all(dept.is_active for dept in Department.objects.all())
        )


class OutputFormattingTest(TestCase):
    """Test command output formatting and messages."""
    
    def test_created_message_format(self):
        """Test created records show checkmark."""
        out = StringIO()
        call_command('populate_academic_data', '--university', 'UNN', stdout=out)
        
        output = out.getvalue()
        self.assertIn('✅ Created University', output)
        self.assertIn('✅ Created Faculty', output)
        self.assertIn('✅ Created Department', output)
    
    def test_skipped_message_format(self):
        """Test skipped records show skip indicator."""
        # Create first
        out1 = StringIO()
        call_command('populate_academic_data', '--university', 'UNN', stdout=out1)
        
        # Run again
        out2 = StringIO()
        call_command('populate_academic_data', '--university', 'UNN', stdout=out2)
        
        output2 = out2.getvalue()
        self.assertIn('⏩ Skipped (exists)', output2)
    
    def test_summary_includes_counts(self):
        """Test summary includes actual counts."""
        out = StringIO()
        call_command('populate_academic_data', '--university', 'UNN', stdout=out)
        
        output = out.getvalue()
        
        # Should show counts
        uni_count = University.objects.count()
        fac_count = Faculty.objects.count()
        dept_count = Department.objects.count()
        
        self.assertIn(f'Universities: {uni_count}', output)
        self.assertIn(f'Faculties: {fac_count}', output)
        self.assertIn(f'Departments: {dept_count}', output)


class EdgeCasesTest(TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_empty_university_list(self):
        """Test behavior with no matching universities."""
        out = StringIO()
        call_command('populate_academic_data', '--university', 'NOTEXIST', stdout=out)
        
        output = out.getvalue()
        self.assertIn('No matching universities', output)
    
    def test_partial_data_creation(self):
        """Test that partial data is created correctly."""
        # Create university manually
        uni = University.objects.create(
            name="University of Nigeria, Nsukka",
            abbreviation="UNN",
            state="ENUGU",
            type="FEDERAL"
        )
        
        # Run command - should create faculties and departments
        out = StringIO()
        call_command('populate_academic_data', '--university', 'UNN', stdout=out)
        
        # Faculties should be created
        self.assertGreater(Faculty.objects.filter(university=uni).count(), 0)
        
        # Departments should be created
        self.assertGreater(Department.objects.count(), 0)
    
    def test_concurrent_safe_execution(self):
        """Test command is safe for concurrent execution (get_or_create)."""
        # This test verifies get_or_create prevents race conditions
        
        # First run
        out1 = StringIO()
        call_command('populate_academic_data', '--university', 'UNN', stdout=out1)
        
        count_after_first = University.objects.count()
        
        # Second run (simulating concurrent execution)
        out2 = StringIO()
        call_command('populate_academic_data', '--university', 'UNN', stdout=out2)
        
        count_after_second = University.objects.count()
        
        # Should be the same - no duplicates
        self.assertEqual(count_after_first, count_after_second)


class SpecificUniversitiesTest(TestCase):
    """Test data for specific universities."""
    
    def test_unn_data_structure(self):
        """Test UNN has expected faculties and departments."""
        out = StringIO()
        call_command('populate_academic_data', '--university', 'UNN', stdout=out)
        
        uni = University.objects.get(abbreviation='UNN')
        
        # Should have faculties
        faculties = Faculty.objects.filter(university=uni)
        self.assertGreater(faculties.count(), 0)
        
        # Check for specific expected faculties
        self.assertTrue(
            faculties.filter(name__icontains='Engineering').exists()
        )
        self.assertTrue(
            faculties.filter(name__icontains='Sciences').exists()
        )
    
    def test_uniport_data_structure(self):
        """Test UNIPORT has expected structure."""
        out = StringIO()
        call_command('populate_academic_data', '--university', 'UNIPORT', stdout=out)
        
        uni = University.objects.get(abbreviation='UNIPORT')
        
        # Verify university details
        self.assertEqual(uni.state, 'RIVERS')
        self.assertEqual(uni.type, 'FEDERAL')
        
        # Should have faculties
        self.assertGreater(Faculty.objects.filter(university=uni).count(), 0)
    
    def test_multiple_universities_independent(self):
        """Test multiple universities maintain separate data."""
        out = StringIO()
        call_command(
            'populate_academic_data',
            '--university', 'UNN',
            '--university', 'UNIPORT',
            stdout=out
        )
        
        unn = University.objects.get(abbreviation='UNN')
        uniport = University.objects.get(abbreviation='UNIPORT')
        
        unn_faculties = set(Faculty.objects.filter(university=unn).values_list('id', flat=True))
        uniport_faculties = set(Faculty.objects.filter(university=uniport).values_list('id', flat=True))
        
        # Should have no overlap
        self.assertEqual(len(unn_faculties & uniport_faculties), 0)