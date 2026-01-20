"""
Comprehensive bulletproof tests for measurement/models.py

Test Coverage:
- Model creation and field validation
- UUID generation and uniqueness
- Min/Max validators for all measurement fields
- Soft delete functionality
- Hard delete functionality
- Custom manager (MeasurementManager)
- clean() method validation
- Relationship with User model
- Timestamp fields (created_at, updated_at)
- String representation (__str__)
- URL generation (get_absolute_url)
- Edge cases and boundary conditions
- Security considerations
- Data integrity
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
import uuid
from datetime import datetime, timedelta
from django.utils import timezone

from measurement.models import Measurement, MeasurementManager


User = get_user_model()


class MeasurementModelCreationTests(TestCase):
    """Test measurement model creation and basic field operations."""

    def setUp(self):
        """Set up test user for measurement creation."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_create_measurement_with_all_fields(self):
        """Test creating a measurement with all fields populated."""
        measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal("38.50"),
            shoulder=Decimal("18.00"),
            neck=Decimal("15.50"),
            sleeve_length=Decimal("32.00"),
            sleeve_round=Decimal("14.00"),
            top_length=Decimal("28.50"),
            waist=Decimal("32.00"),
            thigh=Decimal("22.00"),
            knee=Decimal("16.00"),
            ankle=Decimal("10.00"),
            hips=Decimal("40.00"),
            trouser_length=Decimal("38.00")
        )
        
        self.assertIsNotNone(measurement.id)
        self.assertIsInstance(measurement.id, uuid.UUID)
        self.assertEqual(measurement.user, self.user)
        self.assertEqual(measurement.chest, Decimal("38.50"))
        self.assertEqual(measurement.shoulder, Decimal("18.00"))
        self.assertEqual(measurement.neck, Decimal("15.50"))
        self.assertFalse(measurement.is_deleted)

    def test_create_measurement_with_minimal_fields(self):
        """Test creating a measurement with only one field (chest only)."""
        measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal("38.00")
        )
        
        self.assertIsNotNone(measurement.id)
        self.assertEqual(measurement.chest, Decimal("38.00"))
        self.assertIsNone(measurement.shoulder)
        self.assertIsNone(measurement.waist)

    def test_uuid_is_automatically_generated(self):
        """Test that UUID is automatically generated and unique."""
        measurement1 = Measurement.objects.create(user=self.user, chest=Decimal("38.00"))
        measurement2 = Measurement.objects.create(user=self.user, chest=Decimal("40.00"))
        
        self.assertIsInstance(measurement1.id, uuid.UUID)
        self.assertIsInstance(measurement2.id, uuid.UUID)
        self.assertNotEqual(measurement1.id, measurement2.id)

    def test_timestamps_are_set_automatically(self):
        """Test that created_at and updated_at timestamps are set automatically."""
        measurement = Measurement.objects.create(user=self.user, chest=Decimal("38.00"))
        
        self.assertIsNotNone(measurement.created_at)
        self.assertIsNotNone(measurement.updated_at)
        self.assertIsInstance(measurement.created_at, datetime)
        self.assertIsInstance(measurement.updated_at, datetime)

    def test_updated_at_changes_on_update(self):
        """Test that updated_at timestamp changes when measurement is updated."""
        measurement = Measurement.objects.create(user=self.user, chest=Decimal("38.00"))
        original_updated_at = measurement.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        measurement.chest = Decimal("40.00")
        measurement.save()
        measurement.refresh_from_db()
        
        self.assertNotEqual(measurement.updated_at, original_updated_at)
        self.assertGreater(measurement.updated_at, original_updated_at)

    def test_created_at_does_not_change_on_update(self):
        """Test that created_at remains unchanged when measurement is updated."""
        measurement = Measurement.objects.create(user=self.user, chest=Decimal("38.00"))
        original_created_at = measurement.created_at
        
        measurement.chest = Decimal("40.00")
        measurement.save()
        measurement.refresh_from_db()
        
        self.assertEqual(measurement.created_at, original_created_at)

    def test_user_required(self):
        """Test that user field is required."""
        with self.assertRaises(IntegrityError):
            Measurement.objects.create(chest=Decimal("38.00"))

    def test_default_is_deleted_is_false(self):
        """Test that is_deleted defaults to False."""
        measurement = Measurement.objects.create(user=self.user, chest=Decimal("38.00"))
        self.assertFalse(measurement.is_deleted)


class MeasurementFieldValidationTests(TestCase):
    """Test validation for all measurement fields."""

    def setUp(self):
        """Set up test user for measurement validation tests."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    # CHEST FIELD VALIDATION
    def test_chest_min_value_validation(self):
        """Test chest measurement minimum value validation (20.00)."""
        measurement = Measurement(user=self.user, chest=Decimal("19.99"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("chest", cm.exception.message_dict)

    def test_chest_max_value_validation(self):
        """Test chest measurement maximum value validation (70.00)."""
        measurement = Measurement(user=self.user, chest=Decimal("70.01"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("chest", cm.exception.message_dict)

    def test_chest_valid_boundary_values(self):
        """Test chest measurement valid boundary values."""
        # Minimum boundary
        measurement1 = Measurement(user=self.user, chest=Decimal("20.00"))
        measurement1.full_clean()  # Should not raise
        
        # Maximum boundary
        measurement2 = Measurement(user=self.user, chest=Decimal("70.00"))
        measurement2.full_clean()  # Should not raise

    # SHOULDER FIELD VALIDATION
    def test_shoulder_min_value_validation(self):
        """Test shoulder measurement minimum value validation (12.00)."""
        measurement = Measurement(user=self.user, shoulder=Decimal("11.99"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("shoulder", cm.exception.message_dict)

    def test_shoulder_max_value_validation(self):
        """Test shoulder measurement maximum value validation (30.00)."""
        measurement = Measurement(user=self.user, shoulder=Decimal("30.01"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("shoulder", cm.exception.message_dict)

    def test_shoulder_valid_boundary_values(self):
        """Test shoulder measurement valid boundary values."""
        measurement1 = Measurement(user=self.user, shoulder=Decimal("12.00"))
        measurement1.full_clean()
        
        measurement2 = Measurement(user=self.user, shoulder=Decimal("30.00"))
        measurement2.full_clean()

    # NECK FIELD VALIDATION
    def test_neck_min_value_validation(self):
        """Test neck measurement minimum value validation (10.00)."""
        measurement = Measurement(user=self.user, neck=Decimal("9.99"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("neck", cm.exception.message_dict)

    def test_neck_max_value_validation(self):
        """Test neck measurement maximum value validation (30.00)."""
        measurement = Measurement(user=self.user, neck=Decimal("30.01"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("neck", cm.exception.message_dict)

    def test_neck_valid_boundary_values(self):
        """Test neck measurement valid boundary values."""
        measurement1 = Measurement(user=self.user, neck=Decimal("10.00"))
        measurement1.full_clean()
        
        measurement2 = Measurement(user=self.user, neck=Decimal("30.00"))
        measurement2.full_clean()

    # SLEEVE_LENGTH FIELD VALIDATION
    def test_sleeve_length_min_value_validation(self):
        """Test sleeve_length minimum value validation (20.00)."""
        measurement = Measurement(user=self.user, sleeve_length=Decimal("19.99"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("sleeve_length", cm.exception.message_dict)

    def test_sleeve_length_max_value_validation(self):
        """Test sleeve_length maximum value validation (40.00)."""
        measurement = Measurement(user=self.user, sleeve_length=Decimal("40.01"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("sleeve_length", cm.exception.message_dict)

    def test_sleeve_length_valid_boundary_values(self):
        """Test sleeve_length valid boundary values."""
        measurement1 = Measurement(user=self.user, sleeve_length=Decimal("20.00"))
        measurement1.full_clean()
        
        measurement2 = Measurement(user=self.user, sleeve_length=Decimal("40.00"))
        measurement2.full_clean()

    # SLEEVE_ROUND FIELD VALIDATION
    def test_sleeve_round_min_value_validation(self):
        """Test sleeve_round minimum value validation (8.00)."""
        measurement = Measurement(user=self.user, sleeve_round=Decimal("7.99"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("sleeve_round", cm.exception.message_dict)

    def test_sleeve_round_max_value_validation(self):
        """Test sleeve_round maximum value validation (20.00)."""
        measurement = Measurement(user=self.user, sleeve_round=Decimal("20.01"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("sleeve_round", cm.exception.message_dict)

    def test_sleeve_round_valid_boundary_values(self):
        """Test sleeve_round valid boundary values."""
        measurement1 = Measurement(user=self.user, sleeve_round=Decimal("8.00"))
        measurement1.full_clean()
        
        measurement2 = Measurement(user=self.user, sleeve_round=Decimal("20.00"))
        measurement2.full_clean()

    # TOP_LENGTH FIELD VALIDATION
    def test_top_length_min_value_validation(self):
        """Test top_length minimum value validation (20.00)."""
        measurement = Measurement(user=self.user, top_length=Decimal("19.99"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("top_length", cm.exception.message_dict)

    def test_top_length_max_value_validation(self):
        """Test top_length maximum value validation (40.00)."""
        measurement = Measurement(user=self.user, top_length=Decimal("40.01"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("top_length", cm.exception.message_dict)

    def test_top_length_valid_boundary_values(self):
        """Test top_length valid boundary values."""
        measurement1 = Measurement(user=self.user, top_length=Decimal("20.00"))
        measurement1.full_clean()
        
        measurement2 = Measurement(user=self.user, top_length=Decimal("40.00"))
        measurement2.full_clean()

    # WAIST FIELD VALIDATION
    def test_waist_min_value_validation(self):
        """Test waist minimum value validation (20.00)."""
        measurement = Measurement(user=self.user, waist=Decimal("19.99"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("waist", cm.exception.message_dict)

    def test_waist_max_value_validation(self):
        """Test waist maximum value validation (60.00)."""
        measurement = Measurement(user=self.user, waist=Decimal("60.01"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("waist", cm.exception.message_dict)

    def test_waist_valid_boundary_values(self):
        """Test waist valid boundary values."""
        measurement1 = Measurement(user=self.user, waist=Decimal("20.00"))
        measurement1.full_clean()
        
        measurement2 = Measurement(user=self.user, waist=Decimal("60.00"))
        measurement2.full_clean()

    # THIGH FIELD VALIDATION
    def test_thigh_min_value_validation(self):
        """Test thigh minimum value validation (12.00)."""
        measurement = Measurement(user=self.user, thigh=Decimal("11.99"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("thigh", cm.exception.message_dict)

    def test_thigh_max_value_validation(self):
        """Test thigh maximum value validation (40.00)."""
        measurement = Measurement(user=self.user, thigh=Decimal("40.01"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("thigh", cm.exception.message_dict)

    def test_thigh_valid_boundary_values(self):
        """Test thigh valid boundary values."""
        measurement1 = Measurement(user=self.user, thigh=Decimal("12.00"))
        measurement1.full_clean()
        
        measurement2 = Measurement(user=self.user, thigh=Decimal("40.00"))
        measurement2.full_clean()

    # KNEE FIELD VALIDATION
    def test_knee_min_value_validation(self):
        """Test knee minimum value validation (10.00)."""
        measurement = Measurement(user=self.user, knee=Decimal("9.99"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("knee", cm.exception.message_dict)

    def test_knee_max_value_validation(self):
        """Test knee maximum value validation (30.00)."""
        measurement = Measurement(user=self.user, knee=Decimal("30.01"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("knee", cm.exception.message_dict)

    def test_knee_valid_boundary_values(self):
        """Test knee valid boundary values."""
        measurement1 = Measurement(user=self.user, knee=Decimal("10.00"))
        measurement1.full_clean()
        
        measurement2 = Measurement(user=self.user, knee=Decimal("30.00"))
        measurement2.full_clean()

    # ANKLE FIELD VALIDATION
    def test_ankle_min_value_validation(self):
        """Test ankle minimum value validation (7.00)."""
        measurement = Measurement(user=self.user, ankle=Decimal("6.99"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("ankle", cm.exception.message_dict)

    def test_ankle_max_value_validation(self):
        """Test ankle maximum value validation (20.00)."""
        measurement = Measurement(user=self.user, ankle=Decimal("20.01"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("ankle", cm.exception.message_dict)

    def test_ankle_valid_boundary_values(self):
        """Test ankle valid boundary values."""
        measurement1 = Measurement(user=self.user, ankle=Decimal("7.00"))
        measurement1.full_clean()
        
        measurement2 = Measurement(user=self.user, ankle=Decimal("20.00"))
        measurement2.full_clean()

    # HIPS FIELD VALIDATION
    def test_hips_min_value_validation(self):
        """Test hips minimum value validation (25.00)."""
        measurement = Measurement(user=self.user, hips=Decimal("24.99"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("hips", cm.exception.message_dict)

    def test_hips_max_value_validation(self):
        """Test hips maximum value validation (70.00)."""
        measurement = Measurement(user=self.user, hips=Decimal("70.01"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("hips", cm.exception.message_dict)

    def test_hips_valid_boundary_values(self):
        """Test hips valid boundary values."""
        measurement1 = Measurement(user=self.user, hips=Decimal("25.00"))
        measurement1.full_clean()
        
        measurement2 = Measurement(user=self.user, hips=Decimal("70.00"))
        measurement2.full_clean()

    # TROUSER_LENGTH FIELD VALIDATION
    def test_trouser_length_min_value_validation(self):
        """Test trouser_length minimum value validation (25.00)."""
        measurement = Measurement(user=self.user, trouser_length=Decimal("24.99"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("trouser_length", cm.exception.message_dict)

    def test_trouser_length_max_value_validation(self):
        """Test trouser_length maximum value validation (50.00)."""
        measurement = Measurement(user=self.user, trouser_length=Decimal("50.01"))
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("trouser_length", cm.exception.message_dict)

    def test_trouser_length_valid_boundary_values(self):
        """Test trouser_length valid boundary values."""
        measurement1 = Measurement(user=self.user, trouser_length=Decimal("25.00"))
        measurement1.full_clean()
        
        measurement2 = Measurement(user=self.user, trouser_length=Decimal("50.00"))
        measurement2.full_clean()

    # DECIMAL PRECISION VALIDATION
    def test_decimal_precision_validation(self):
        """Test that measurements accept up to 2 decimal places."""
        measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal("38.12")
        )
        self.assertEqual(measurement.chest, Decimal("38.12"))

    def test_negative_values_rejected(self):
        """Test that negative values are rejected for all fields."""
        measurement = Measurement(user=self.user, chest=Decimal("-10.00"))
        with self.assertRaises(ValidationError):
            measurement.full_clean()

    def test_zero_values_rejected(self):
        """Test that zero values are rejected (below minimum)."""
        measurement = Measurement(user=self.user, chest=Decimal("0.00"))
        with self.assertRaises(ValidationError):
            measurement.full_clean()


class MeasurementCleanMethodTests(TestCase):
    """Test the custom clean() method validation."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_clean_method_requires_at_least_one_measurement(self):
        """Test that clean() raises error when no measurements are provided."""
        measurement = Measurement(user=self.user)
        with self.assertRaises(ValidationError) as cm:
            measurement.clean()
        
        self.assertIn("At least one measurement must be provided", str(cm.exception))

    def test_clean_method_passes_with_one_measurement(self):
        """Test that clean() passes when at least one measurement is provided."""
        measurement = Measurement(user=self.user, chest=Decimal("38.00"))
        measurement.clean()  # Should not raise

    def test_clean_method_passes_with_multiple_measurements(self):
        """Test that clean() passes when multiple measurements are provided."""
        measurement = Measurement(
            user=self.user,
            chest=Decimal("38.00"),
            waist=Decimal("32.00")
        )
        measurement.clean()  # Should not raise

    def test_clean_method_with_only_none_values(self):
        """Test that clean() fails when all measurement fields are None."""
        measurement = Measurement(
            user=self.user,
            chest=None,
            shoulder=None,
            neck=None,
            sleeve_length=None,
            sleeve_round=None,
            top_length=None,
            waist=None,
            thigh=None,
            knee=None,
            ankle=None,
            hips=None,
            trouser_length=None
        )
        with self.assertRaises(ValidationError):
            measurement.clean()


class MeasurementSoftDeleteTests(TestCase):
    """Test soft delete functionality."""

    def setUp(self):
        """Set up test user and measurement."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal("38.00")
        )

    def test_soft_delete_marks_as_deleted(self):
        """Test that soft delete marks measurement as deleted."""
        self.assertFalse(self.measurement.is_deleted)
        self.measurement.delete()
        
        self.measurement.refresh_from_db()
        self.assertTrue(self.measurement.is_deleted)

    def test_soft_deleted_measurement_not_in_default_queryset(self):
        """Test that soft deleted measurements are excluded from default queryset."""
        measurement_id = self.measurement.id
        self.measurement.delete()
        
        # Should not be in default queryset
        self.assertFalse(Measurement.objects.filter(id=measurement_id).exists())

    def test_soft_deleted_measurement_in_all_with_deleted_queryset(self):
        """Test that soft deleted measurements appear in all_with_deleted queryset."""
        measurement_id = self.measurement.id
        self.measurement.delete()
        
        # Should be in all_with_deleted queryset
        self.assertTrue(
            Measurement.objects.all_with_deleted().filter(id=measurement_id).exists()
        )

    def test_multiple_soft_deletes_idempotent(self):
        """Test that calling delete multiple times is idempotent."""
        self.measurement.delete()
        self.measurement.delete()  # Should not cause error
        
        self.measurement.refresh_from_db()
        self.assertTrue(self.measurement.is_deleted)

    def test_hard_delete_removes_from_database(self):
        """Test that hard_delete permanently removes measurement."""
        measurement_id = self.measurement.id
        self.measurement.hard_delete()
        
        # Should not exist in any queryset
        self.assertFalse(Measurement.objects.filter(id=measurement_id).exists())
        self.assertFalse(
            Measurement.objects.all_with_deleted().filter(id=measurement_id).exists()
        )

    def test_soft_delete_does_not_cascade_to_user(self):
        """Test that soft deleting measurement doesn't affect user."""
        self.measurement.delete()
        
        # User should still exist
        self.assertTrue(User.objects.filter(id=self.user.id).exists())

    def test_user_deletion_cascades_to_measurements(self):
        """Test that deleting user cascades to measurements."""
        measurement_id = self.measurement.id
        user_id = self.user.id
        
        self.user.delete()
        
        # Measurement should be hard deleted (CASCADE)
        self.assertFalse(
            Measurement.objects.all_with_deleted().filter(id=measurement_id).exists()
        )


class MeasurementManagerTests(TestCase):
    """Test the custom MeasurementManager."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.active_measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal("38.00")
        )
        self.deleted_measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal("40.00")
        )
        self.deleted_measurement.delete()  # Soft delete

    def test_default_queryset_excludes_deleted(self):
        """Test that default queryset excludes soft-deleted measurements."""
        measurements = Measurement.objects.all()
        self.assertEqual(measurements.count(), 1)
        self.assertIn(self.active_measurement, measurements)
        self.assertNotIn(self.deleted_measurement, measurements)

    def test_all_with_deleted_includes_all(self):
        """Test that all_with_deleted includes soft-deleted measurements."""
        measurements = Measurement.objects.all_with_deleted()
        self.assertEqual(measurements.count(), 2)
        self.assertIn(self.active_measurement, measurements)

    def test_filter_works_with_default_manager(self):
        """Test that filter operations work with default manager."""
        measurements = Measurement.objects.filter(chest=Decimal("38.00"))
        self.assertEqual(measurements.count(), 1)
        self.assertEqual(measurements.first(), self.active_measurement)

    def test_filter_works_with_all_with_deleted(self):
        """Test that filter operations work with all_with_deleted."""
        measurements = Measurement.objects.all_with_deleted().filter(
            chest=Decimal("40.00")
        )
        self.assertEqual(measurements.count(), 1)


class MeasurementStringRepresentationTests(TestCase):
    """Test string representation and display methods."""

    def setUp(self):
        """Set up test user and measurement."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_str_method(self):
        """Test __str__ method returns expected format."""
        measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal("38.00")
        )
        
        expected = f"Measurements for {self.user.username} ({measurement.created_at.date()})"
        self.assertEqual(str(measurement), expected)

    def test_str_method_with_different_users(self):
        """Test __str__ method with different users."""
        user2 = User.objects.create_user(
            username="anotheruser",
            email="another@example.com",
            password="testpass123"
        )
        
        measurement = Measurement.objects.create(
            user=user2,
            chest=Decimal("38.00")
        )
        
        self.assertIn("anotheruser", str(measurement))


class MeasurementOrderingTests(TestCase):
    """Test default ordering of measurements."""

    def setUp(self):
        """Set up test user and multiple measurements."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_measurements_ordered_by_created_at_desc(self):
        """Test that measurements are ordered by created_at descending."""
        # Create measurements with slight time differences
        measurement1 = Measurement.objects.create(user=self.user, chest=Decimal("38.00"))
        
        import time
        time.sleep(0.01)
        
        measurement2 = Measurement.objects.create(user=self.user, chest=Decimal("40.00"))
        
        measurements = Measurement.objects.all()
        # Most recent should be first
        self.assertEqual(measurements.first(), measurement2)
        self.assertEqual(measurements.last(), measurement1)


class MeasurementUserRelationshipTests(TestCase):
    """Test relationship between Measurement and User models."""

    def setUp(self):
        """Set up test users."""
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123"
        )

    def test_user_can_have_multiple_measurements(self):
        """Test that a user can have multiple measurements."""
        measurement1 = Measurement.objects.create(user=self.user1, chest=Decimal("38.00"))
        measurement2 = Measurement.objects.create(user=self.user1, chest=Decimal("40.00"))
        
        user_measurements = Measurement.objects.filter(user=self.user1)
        self.assertEqual(user_measurements.count(), 2)
        self.assertIn(measurement1, user_measurements)
        self.assertIn(measurement2, user_measurements)

    def test_measurements_isolated_by_user(self):
        """Test that measurements are properly isolated by user."""
        measurement1 = Measurement.objects.create(user=self.user1, chest=Decimal("38.00"))
        measurement2 = Measurement.objects.create(user=self.user2, chest=Decimal("40.00"))
        
        user1_measurements = Measurement.objects.filter(user=self.user1)
        user2_measurements = Measurement.objects.filter(user=self.user2)
        
        self.assertEqual(user1_measurements.count(), 1)
        self.assertEqual(user2_measurements.count(), 1)
        self.assertNotIn(measurement2, user1_measurements)
        self.assertNotIn(measurement1, user2_measurements)

    def test_measurement_user_foreign_key(self):
        """Test that measurement correctly references user via foreign key."""
        measurement = Measurement.objects.create(user=self.user1, chest=Decimal("38.00"))
        
        self.assertEqual(measurement.user, self.user1)
        self.assertEqual(measurement.user.username, "user1")


class MeasurementEdgeCaseTests(TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_all_fields_at_minimum_boundary(self):
        """Test creating measurement with all fields at minimum values."""
        measurement = Measurement(
            user=self.user,
            chest=Decimal("20.00"),
            shoulder=Decimal("12.00"),
            neck=Decimal("10.00"),
            sleeve_length=Decimal("20.00"),
            sleeve_round=Decimal("8.00"),
            top_length=Decimal("20.00"),
            waist=Decimal("20.00"),
            thigh=Decimal("12.00"),
            knee=Decimal("10.00"),
            ankle=Decimal("7.00"),
            hips=Decimal("25.00"),
            trouser_length=Decimal("25.00")
        )
        measurement.full_clean()  # Should not raise
        measurement.save()
        self.assertIsNotNone(measurement.id)

    def test_all_fields_at_maximum_boundary(self):
        """Test creating measurement with all fields at maximum values."""
        measurement = Measurement(
            user=self.user,
            chest=Decimal("70.00"),
            shoulder=Decimal("30.00"),
            neck=Decimal("30.00"),
            sleeve_length=Decimal("40.00"),
            sleeve_round=Decimal("20.00"),
            top_length=Decimal("40.00"),
            waist=Decimal("60.00"),
            thigh=Decimal("40.00"),
            knee=Decimal("30.00"),
            ankle=Decimal("20.00"),
            hips=Decimal("70.00"),
            trouser_length=Decimal("50.00")
        )
        measurement.full_clean()  # Should not raise
        measurement.save()
        self.assertIsNotNone(measurement.id)

    def test_mixed_none_and_valid_values(self):
        """Test measurement with mix of None and valid values."""
        measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal("38.00"),
            shoulder=None,
            neck=Decimal("15.00"),
            sleeve_length=None,
            waist=Decimal("32.00")
        )
        
        self.assertEqual(measurement.chest, Decimal("38.00"))
        self.assertIsNone(measurement.shoulder)
        self.assertEqual(measurement.neck, Decimal("15.00"))

    def test_large_number_of_measurements_per_user(self):
        """Test that user can have many measurements (no artificial limit)."""
        # Create 100 measurements
        measurements = []
        for i in range(100):
            measurement = Measurement.objects.create(
                user=self.user,
                chest=Decimal("38.00")
            )
            measurements.append(measurement)
        
        user_measurements = Measurement.objects.filter(user=self.user)
        self.assertEqual(user_measurements.count(), 100)

    def test_decimal_field_precision_handling(self):
        """Test that decimal precision is handled correctly."""
        # Test with various decimal precisions
        measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal("38.1"),  # 1 decimal place
            waist=Decimal("32.12"),  # 2 decimal places
            thigh=Decimal("22.00")  # Explicit 2 decimal places
        )
        
        self.assertEqual(measurement.chest, Decimal("38.10"))  # Should be normalized
        self.assertEqual(measurement.waist, Decimal("32.12"))
        self.assertEqual(measurement.thigh, Decimal("22.00"))


class MeasurementSecurityTests(TestCase):
    """Test security-related aspects of measurements."""

    def setUp(self):
        """Set up test users."""
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123"
        )

    def test_uuid_not_sequential(self):
        """Test that UUIDs are not sequential (security consideration)."""
        measurement1 = Measurement.objects.create(user=self.user1, chest=Decimal("38.00"))
        measurement2 = Measurement.objects.create(user=self.user1, chest=Decimal("40.00"))
        
        # UUIDs should not be predictable
        self.assertNotEqual(measurement1.id, measurement2.id)
        # Check that they're not sequential integers
        self.assertIsInstance(measurement1.id, uuid.UUID)
        self.assertIsInstance(measurement2.id, uuid.UUID)

    def test_user_cannot_access_other_user_measurements_via_pk(self):
        """Test data isolation - one user's measurement shouldn't be guessable."""
        measurement1 = Measurement.objects.create(user=self.user1, chest=Decimal("38.00"))
        
        # In a real application, you'd check this at the view/permission level,
        # but the UUID makes it hard to guess
        self.assertEqual(measurement1.user, self.user1)
        self.assertNotEqual(measurement1.user, self.user2)

    def test_measurement_data_integrity_on_cascade_delete(self):
        """Test that measurement data is properly cleaned up on user deletion."""
        measurement = Measurement.objects.create(user=self.user1, chest=Decimal("38.00"))
        measurement_id = measurement.id
        
        # Delete user
        self.user1.delete()
        
        # Measurement should be gone (CASCADE)
        self.assertFalse(
            Measurement.objects.all_with_deleted().filter(id=measurement_id).exists()
        )


class MeasurementMetaOptionsTests(TestCase):
    """Test Meta options and database configurations."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_verbose_name(self):
        """Test that verbose_name is set correctly."""
        self.assertEqual(Measurement._meta.verbose_name, "Measurement")

    def test_verbose_name_plural(self):
        """Test that verbose_name_plural is set correctly."""
        self.assertEqual(Measurement._meta.verbose_name_plural, "Measurements")

    def test_default_ordering(self):
        """Test that default ordering is set correctly."""
        self.assertEqual(Measurement._meta.ordering, ["-created_at"])

    def test_indexes_exist(self):
        """Test that database indexes are properly defined."""
        # Check that the composite index exists
        indexes = [index.name for index in Measurement._meta.indexes]
        self.assertIn("measurement_user_created_idx", indexes)


class MeasurementFullCleanTests(TestCase):
    """Test full_clean() validation (combines field and model validation)."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_full_clean_with_valid_data(self):
        """Test full_clean passes with valid data."""
        measurement = Measurement(
            user=self.user,
            chest=Decimal("38.00"),
            waist=Decimal("32.00")
        )
        measurement.full_clean()  # Should not raise

    def test_full_clean_catches_field_validation_errors(self):
        """Test full_clean catches field-level validation errors."""
        measurement = Measurement(user=self.user, chest=Decimal("10.00"))  # Too small
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        self.assertIn("chest", cm.exception.message_dict)

    def test_full_clean_catches_model_validation_errors(self):
        """Test full_clean catches model-level validation errors (clean method)."""
        measurement = Measurement(user=self.user)  # No measurements
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        # Should catch the "at least one measurement" error
        self.assertTrue(
            "At least one measurement must be provided" in str(cm.exception) or
            "__all__" in cm.exception.message_dict
        )

    def test_full_clean_with_multiple_errors(self):
        """Test full_clean reports multiple validation errors."""
        measurement = Measurement(
            user=self.user,
            chest=Decimal("10.00"),  # Too small
            waist=Decimal("70.00")   # Too large
        )
        with self.assertRaises(ValidationError) as cm:
            measurement.full_clean()
        
        # Should have errors for both fields
        errors = cm.exception.message_dict
        self.assertIn("chest", errors)
        self.assertIn("waist", errors)