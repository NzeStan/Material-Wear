# academic_directory/tests/utils/test_deduplication.py
"""
Comprehensive test suite for deduplication utility.

Test Coverage:
- Finding existing representatives by phone
- Merging representative records
- Handling duplicate data
- Change tracking during merge
- Verification status handling during merge
- Creating vs updating representatives
"""

from django.test import TestCase
from academic_directory.models import University, Faculty, Department, Representative, ProgramDuration
from academic_directory.utils.deduplication import (
    find_existing_representative,
    merge_representative_records,
    deduplicate_or_create_representative
)


class FindExistingRepresentativeTest(TestCase):
    """Test finding existing representatives by phone number."""
    
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
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="+2348012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_finds_by_normalized_phone(self):
        """Test finds representative with normalized phone."""
        found = find_existing_representative('+2348012345678')
        self.assertEqual(found.id, self.rep.id)
    
    def test_finds_with_different_format(self):
        """Test finds representative with different phone format."""
        found = find_existing_representative('08012345678')
        self.assertEqual(found.id, self.rep.id)
    
    def test_finds_with_234_prefix(self):
        """Test finds representative with 234 prefix."""
        found = find_existing_representative('2348012345678')
        self.assertEqual(found.id, self.rep.id)
    
    def test_returns_none_for_nonexistent(self):
        """Test returns None for non-existent phone."""
        found = find_existing_representative('08087654321')
        self.assertIsNone(found)
    
    def test_returns_none_for_invalid_phone(self):
        """Test returns None for invalid phone."""
        found = find_existing_representative('invalid')
        self.assertIsNone(found)


class MergeRepresentativeRecordsTest(TestCase):
    """Test merging representative records."""
    
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
        self.existing = Representative.objects.create(
            full_name="John Doe",
            phone_number="+2348012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_updates_changed_fields(self):
        """Test that changed fields are updated."""
        new_data = {
            'full_name': 'John Updated',
            'email': 'john@example.com'
        }
        
        updated, changes = merge_representative_records(self.existing, new_data)
        
        self.assertEqual(updated.full_name, 'John Updated')
        self.assertEqual(updated.email, 'john@example.com')
        self.assertIn('full_name', changes)
        self.assertIn('email', changes)
    
    def test_no_changes_returns_empty_dict(self):
        """Test no changes returns empty changes dict."""
        new_data = {
            'full_name': 'John Doe',  # Same as existing
        }
        
        updated, changes = merge_representative_records(self.existing, new_data)
        
        self.assertEqual(changes, {})
    
    def test_none_values_skipped(self):
        """Test that None values don't override existing data."""
        new_data = {
            'email': None,  # Don't override existing
            'full_name': 'John Updated'
        }
        
        self.existing.email = 'existing@example.com'
        self.existing.save()
        
        updated, changes = merge_representative_records(self.existing, new_data)
        
        self.assertEqual(updated.email, 'existing@example.com')
        self.assertNotIn('email', changes)
    
    def test_verified_reset_on_data_change(self):
        """Test verified status is reset when data changes."""
        # Set as verified
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin = User.objects.create_user(
            email="admin@example.com",
            password="test",
            is_staff=True
        )
        self.existing.verify(admin)
        
        new_data = {
            'full_name': 'John Updated'
        }
        
        updated, changes = merge_representative_records(self.existing, new_data)
        
        self.assertEqual(updated.verification_status, 'UNVERIFIED')
        self.assertIn('verification_status', changes)
    
    def test_unverified_stays_unverified(self):
        """Test unverified record stays unverified on update."""
        self.assertEqual(self.existing.verification_status, 'UNVERIFIED')
        
        new_data = {'email': 'john@example.com'}
        updated, changes = merge_representative_records(self.existing, new_data)
        
        self.assertEqual(updated.verification_status, 'UNVERIFIED')


class DeduplicateOrCreateRepresentativeTest(TestCase):
    """Test creating or updating representatives."""
    
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
    
    def test_creates_new_representative(self):
        """Test creating new representative when none exists."""
        data = {
            'full_name': 'John Doe',
            'phone_number': '08012345678',
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        
        rep, is_new, changes = deduplicate_or_create_representative(data)
        
        self.assertTrue(is_new)
        self.assertEqual(changes, {})
        self.assertEqual(Representative.objects.count(), 1)
        self.assertEqual(rep.phone_number, '+2348012345678')  # Normalized
    
    def test_updates_existing_representative(self):
        """Test updating existing representative."""
        # Create existing
        Representative.objects.create(
            full_name="John Doe",
            phone_number="+2348012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        # Submit with updated data
        data = {
            'full_name': 'John Updated',
            'phone_number': '08012345678',  # Same phone, different format
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2021
        }
        
        rep, is_new, changes = deduplicate_or_create_representative(data)
        
        self.assertFalse(is_new)
        self.assertIn('full_name', changes)
        self.assertEqual(Representative.objects.count(), 1)  # Still only 1
        self.assertEqual(rep.full_name, 'John Updated')
    
    def test_normalizes_phone_number(self):
        """Test phone number is normalized before processing."""
        data = {
            'full_name': 'John Doe',
            'phone_number': '0801 234 5678',  # Spaces
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        
        rep, is_new, changes = deduplicate_or_create_representative(data)
        
        self.assertEqual(rep.phone_number, '+2348012345678')
    
    def test_sets_denormalized_fields(self):
        """Test denormalized fields (faculty, university) are set."""
        data = {
            'full_name': 'John Doe',
            'phone_number': '08012345678',
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        
        rep, is_new, changes = deduplicate_or_create_representative(data)
        
        self.assertEqual(rep.department, self.department)
        self.assertEqual(rep.faculty, self.faculty)
        self.assertEqual(rep.university, self.university)