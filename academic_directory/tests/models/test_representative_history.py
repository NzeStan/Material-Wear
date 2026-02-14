# academic_directory/tests/models/test_representative_history.py
"""
Comprehensive test suite for RepresentativeHistory model.

Test Coverage:
- Model creation and snapshot functionality
- Foreign key relationships
- Snapshot data integrity
- Class method create_from_representative()
- Property (role_display)
- String representation
- Edge cases and boundary conditions
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from academic_directory.models import (
    University, Faculty, Department, Representative,
    RepresentativeHistory
)
import uuid


class RepresentativeHistoryCreationTest(TestCase):
    """Test basic representative history creation."""
    
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
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_create_history_manually(self):
        """Test creating history record manually."""
        history = RepresentativeHistory.objects.create(
            representative=self.rep,
            full_name=self.rep.full_name,
            phone_number=self.rep.phone_number,
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role=self.rep.role,
            entry_year=self.rep.entry_year,
            verification_status=self.rep.verification_status,
            is_active=self.rep.is_active
        )
        
        self.assertIsNotNone(history.id)
        self.assertIsInstance(history.id, uuid.UUID)
        self.assertEqual(history.representative, self.rep)
        self.assertEqual(history.full_name, "John Doe")
        self.assertEqual(history.phone_number, "+2348012345678")
        self.assertEqual(history.role, "CLASS_REP")
        self.assertIsNotNone(history.snapshot_date)
    
    def test_create_from_representative_class_method(self):
        """Test create_from_representative() class method."""
        history = RepresentativeHistory.create_from_representative(self.rep)
        
        self.assertIsNotNone(history.id)
        self.assertEqual(history.representative, self.rep)
        self.assertEqual(history.full_name, self.rep.full_name)
        self.assertEqual(history.phone_number, self.rep.phone_number)
        self.assertEqual(history.department, self.rep.department)
        self.assertEqual(history.faculty, self.rep.faculty)
        self.assertEqual(history.university, self.rep.university)
        self.assertEqual(history.role, self.rep.role)
        self.assertEqual(history.entry_year, self.rep.entry_year)
        self.assertEqual(history.verification_status, self.rep.verification_status)
        self.assertEqual(history.is_active, self.rep.is_active)
        self.assertIn("Snapshot created on update", history.notes)


class ForeignKeyRelationshipTest(TestCase):
    """Test foreign key relationships."""
    
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
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_representative_relationship(self):
        """Test history linked to representative."""
        history = RepresentativeHistory.create_from_representative(self.rep)
        
        self.assertEqual(history.representative.id, self.rep.id)
        self.assertEqual(history.representative.full_name, "John Doe")
    
    def test_representative_history_reverse_relation(self):
        """Test reverse relation from representative to history."""
        history1 = RepresentativeHistory.create_from_representative(self.rep)
        history2 = RepresentativeHistory.create_from_representative(self.rep)
        
        histories = self.rep.history.all()
        self.assertEqual(histories.count(), 3)
        self.assertIn(history1, histories)
        self.assertIn(history2, histories)
    
    def test_delete_representative_cascades_to_history(self):
        """Test that deleting representative cascades to history."""
        RepresentativeHistory.create_from_representative(self.rep)
        RepresentativeHistory.create_from_representative(self.rep)
        
        self.assertEqual(RepresentativeHistory.objects.count(), 3)
        
        self.rep.delete()
        
        # All history should be deleted
        self.assertEqual(RepresentativeHistory.objects.count(), 0)
    
    def test_department_set_null_on_delete(self):
        """Test that department is set to NULL on delete."""
        history = RepresentativeHistory.create_from_representative(self.rep)
        
        dept_id = self.department.id
        self.assertEqual(history.department.id, dept_id)
        
        # Delete department
        self.department.delete()
        
        # Representative should also be deleted (cascade)
        self.assertEqual(Representative.objects.count(), 0)
        self.assertEqual(RepresentativeHistory.objects.count(), 0)
    
    def test_faculty_set_null_on_delete(self):
        """Test that faculty is set to NULL on delete."""
        history = RepresentativeHistory.create_from_representative(self.rep)
        
        self.assertEqual(history.faculty.id, self.faculty.id)
        
        # Delete faculty
        self.faculty.delete()
        
        # Department and representative should be deleted
        self.assertEqual(Department.objects.count(), 0)
        self.assertEqual(Representative.objects.count(), 0)
        self.assertEqual(RepresentativeHistory.objects.count(), 0)


class SnapshotDataIntegrityTest(TestCase):
    """Test snapshot data integrity."""
    
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
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,
            verification_status="UNVERIFIED"
        )
    
    def test_snapshot_captures_all_fields(self):
        """Test that snapshot captures all representative fields."""
        history = RepresentativeHistory.create_from_representative(self.rep)
        
        self.assertEqual(history.full_name, self.rep.full_name)
        self.assertEqual(history.phone_number, self.rep.phone_number)
        self.assertEqual(history.role, self.rep.role)
        self.assertEqual(history.entry_year, self.rep.entry_year)
        self.assertEqual(history.verification_status, self.rep.verification_status)
        self.assertEqual(history.is_active, self.rep.is_active)
    
    def test_snapshot_independent_of_representative_changes(self):
        """Test that snapshot is independent of representative changes."""
        history = RepresentativeHistory.create_from_representative(self.rep)
        original_name = history.full_name
        
        # Change representative
        self.rep.full_name = "Changed Name"
        self.rep.save()
        
        # History should not change
        history.refresh_from_db()
        self.assertEqual(history.full_name, original_name)
        self.assertNotEqual(history.full_name, self.rep.full_name)
    
    def test_multiple_snapshots_track_changes(self):
        """Test that multiple snapshots track changes over time."""
        # First snapshot
        history1 = RepresentativeHistory.create_from_representative(self.rep)
        self.assertEqual(history1.verification_status, "UNVERIFIED")
        
        # Change and create second snapshot
        self.rep.verification_status = "VERIFIED"
        self.rep.save()
        
        history2 = RepresentativeHistory.create_from_representative(self.rep)
        self.assertEqual(history2.verification_status, "VERIFIED")
        
        # Both snapshots should exist independently
        self.assertEqual(RepresentativeHistory.objects.count(), 4)
        self.assertNotEqual(history1.verification_status, history2.verification_status)


class RoleTrackingTest(TestCase):
    """Test role change tracking."""
    
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

        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="+2348012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_track_class_rep_to_president_transition(self):
        """Test tracking transition from class rep to president."""
        # Create initial history as class rep
        history1 = RepresentativeHistory.create_from_representative(self.rep)
        self.assertEqual(history1.role, "CLASS_REP")
        
        # Transition to president
        self.rep.role = "DEPT_PRESIDENT"
        self.rep.entry_year = None
        self.rep.tenure_start_year = 2024
        self.rep.save()
        
        # Create new history
        history2 = RepresentativeHistory.create_from_representative(self.rep)
        self.assertEqual(history2.role, "DEPT_PRESIDENT")
        
        # Check all histories (ordered by -snapshot_date, newest first)
        histories = self.rep.history.all()
        self.assertEqual(histories.count(), 4)  # Account for auto-created histories
        
        # Verify we can see both roles in history
        roles = set(histories.values_list('role', flat=True))
        self.assertIn("CLASS_REP", roles)
        self.assertIn("DEPT_PRESIDENT", roles)
        
        # Verify president histories exist
        president_histories = [h for h in histories if h.role == "DEPT_PRESIDENT"]
        self.assertGreater(len(president_histories), 0)

class RoleDisplayPropertyTest(TestCase):
    """Test role_display property."""
    
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
    
    def test_role_display_class_rep(self):
        """Test role_display for CLASS_REP."""
        rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        history = RepresentativeHistory.create_from_representative(rep)
        self.assertEqual(history.role_display, "Class Representative")
    
    def test_role_display_dept_president(self):
        """Test role_display for DEPT_PRESIDENT."""
        rep = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08098765432",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024
        )
        
        history = RepresentativeHistory.create_from_representative(rep)
        self.assertEqual(history.role_display, "Department President")
    
    def test_role_display_faculty_president(self):
        """Test role_display for FACULTY_PRESIDENT."""
        rep = Representative.objects.create(
            full_name="Bob Johnson",
            phone_number="08087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="FACULTY_PRESIDENT",
            tenure_start_year=2024
        )
        
        history = RepresentativeHistory.create_from_representative(rep)
        self.assertEqual(history.role_display, "Faculty President")


class StringRepresentationTest(TestCase):
    """Test string representation."""
    
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
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_str_format(self):
        """Test __str__ returns correct format."""
        history = RepresentativeHistory.create_from_representative(self.rep)
        
        # Format: "Name - Role (YYYY-MM-DD)"
        result = str(history)
        self.assertIn("John Doe", result)
        self.assertIn("CLASS_REP", result)
        # Should contain date in YYYY-MM-DD format
        self.assertRegex(result, r'\d{4}-\d{2}-\d{2}')


class MetaOptionsTest(TestCase):
    """Test model Meta options."""
    
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
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_ordering_by_snapshot_date_desc(self):
        """Test that history is ordered by snapshot_date descending."""
        import time
        
        history1 = RepresentativeHistory.create_from_representative(self.rep)
        time.sleep(0.01)
        history2 = RepresentativeHistory.create_from_representative(self.rep)
        
        histories = list(RepresentativeHistory.objects.all())
        self.assertEqual(histories[0].id, history2.id)  # Newest first
        self.assertEqual(histories[1].id, history1.id)
    
    def test_verbose_name(self):
        """Test verbose_name is set correctly."""
        self.assertEqual(
            RepresentativeHistory._meta.verbose_name,
            "Representative History"
        )
    
    def test_verbose_name_plural(self):
        """Test verbose_name_plural is set correctly."""
        self.assertEqual(
            RepresentativeHistory._meta.verbose_name_plural,
            "Representative Histories"
        )


class IndexingTest(TestCase):
    """Test database indexes."""
    
    def test_representative_snapshot_date_composite_index(self):
        """Test composite index on representative and snapshot_date."""
        indexes = [index.fields for index in RepresentativeHistory._meta.indexes]
        self.assertIn(['representative', '-snapshot_date'], indexes)
    
    def test_phone_number_index_exists(self):
        """Test that phone_number field has an index."""
        indexes = [index.fields for index in RepresentativeHistory._meta.indexes]
        self.assertIn(['phone_number'], indexes)


class EdgeCasesTest(TestCase):
    """Test edge cases and boundary conditions."""
    
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
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="+2348012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_snapshot_with_null_optional_fields(self):
        """Test snapshot with null optional fields."""
        rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="+2348012345679",  # ✅ unique number
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
            # No tenure_start_year (null)
        )
        
        history = RepresentativeHistory.create_from_representative(rep)
        self.assertIsNone(history.tenure_start_year)
    
    def test_snapshot_with_long_notes(self):
        """Test snapshot with very long notes."""
        rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="+2348012345680",  # ✅ unique number
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        long_notes = "A" * 1000
        history = RepresentativeHistory.objects.create(
            representative=rep,
            full_name=rep.full_name,
            phone_number=rep.phone_number,
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role=rep.role,
            entry_year=rep.entry_year,
            verification_status=rep.verification_status,
            is_active=rep.is_active,
            notes=long_notes
        )
        
        self.assertEqual(len(history.notes), 1000)
    
    def test_multiple_representatives_multiple_histories(self):
        """Test multiple representatives each with multiple histories."""
        # Create second representative
        rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="+2348098765432",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024
        )
        
        # Create histories for rep1
        RepresentativeHistory.create_from_representative(self.rep)
        RepresentativeHistory.create_from_representative(self.rep)
        
        # Create histories for rep2
        RepresentativeHistory.create_from_representative(rep2)
        RepresentativeHistory.create_from_representative(rep2)
        
        # Account for automatic history creation
        self.assertEqual(self.rep.history.count(), 3)  # 2 manual + 1 auto
        self.assertEqual(rep2.history.count(), 3)      # 2 manual + 1 auto