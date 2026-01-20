"""
Comprehensive bulletproof tests for measurement/serializers.py

Test Coverage:
- Serialization (model instance to JSON/dict)
- Deserialization (JSON/dict to model)
- Field validation for all 12 measurement fields
- Custom error messages
- Min/Max validators
- Read-only fields (user, created_at, updated_at, is_deleted)
- validate() method (at least one measurement required)
- create() method (auto-assign user)
- update() method (protect user field)
- Partial updates
- Boundary value testing
- Data type validation
- Null/None handling
- Invalid data handling
- Context requirements (request.user)
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime
import uuid

from measurement.models import Measurement
from measurement.serializers import MeasurementSerializer


User = get_user_model()


class MeasurementSerializerSerializationTests(TestCase):
    """Test serialization (model instance to dict/JSON)."""

    def setUp(self):
        """Set up test user and measurement instance."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal('38.50'),
            shoulder=Decimal('18.00'),
            neck=Decimal('15.50'),
            waist=Decimal('32.00')
        )

    def test_serialize_measurement_with_all_fields(self):
        """Test serializing a measurement instance includes all fields."""
        serializer = MeasurementSerializer(instance=self.measurement)
        data = serializer.data
        
        # Check all expected fields are present
        expected_fields = [
            'id', 'user', 'chest', 'shoulder', 'neck', 'sleeve_length',
            'sleeve_round', 'top_length', 'waist', 'thigh', 'knee',
            'ankle', 'hips', 'trouser_length', 'created_at', 'updated_at',
            'is_deleted'
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serialize_measurement_correct_values(self):
        """Test serialized data contains correct values."""
        serializer = MeasurementSerializer(instance=self.measurement)
        data = serializer.data
        
        self.assertEqual(data['chest'], '38.50')
        self.assertEqual(data['shoulder'], '18.00')
        self.assertEqual(data['neck'], '15.50')
        self.assertEqual(data['waist'], '32.00')
        self.assertEqual(data['user'], self.user.id)

    def test_serialize_measurement_with_null_fields(self):
        """Test serializing measurement with null optional fields."""
        measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal('38.00'),
            # Other fields are None
        )
        serializer = MeasurementSerializer(instance=measurement)
        data = serializer.data
        
        self.assertEqual(data['chest'], '38.00')
        self.assertIsNone(data['shoulder'])
        self.assertIsNone(data['neck'])
        self.assertIsNone(data['waist'])

    def test_serialize_measurement_uuid_as_string(self):
        """Test that UUID is serialized as string."""
        serializer = MeasurementSerializer(instance=self.measurement)
        data = serializer.data
        
        self.assertIsInstance(data['id'], str)
        # Verify it's a valid UUID string
        uuid.UUID(data['id'])

    def test_serialize_measurement_timestamps(self):
        """Test that timestamps are properly serialized."""
        serializer = MeasurementSerializer(instance=self.measurement)
        data = serializer.data
        
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIsNotNone(data['created_at'])
        self.assertIsNotNone(data['updated_at'])

    def test_serialize_measurement_is_deleted_field(self):
        """Test that is_deleted field is included in serialization."""
        serializer = MeasurementSerializer(instance=self.measurement)
        data = serializer.data
        
        self.assertIn('is_deleted', data)
        self.assertFalse(data['is_deleted'])

    def test_serialize_multiple_measurements(self):
        """Test serializing multiple measurements."""
        measurement2 = Measurement.objects.create(
            user=self.user,
            chest=Decimal('40.00')
        )
        
        measurements = Measurement.objects.filter(user=self.user)
        serializer = MeasurementSerializer(measurements, many=True)
        
        self.assertEqual(len(serializer.data), 2)
        self.assertIsInstance(serializer.data, list)


class MeasurementSerializerDeserializationTests(TestCase):
    """Test deserialization (dict/JSON to validated data)."""

    def setUp(self):
        """Set up test user and request factory."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = APIRequestFactory()

    def test_deserialize_valid_single_field(self):
        """Test deserializing valid data with single measurement field."""
        data = {'chest': '38.00'}
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = MeasurementSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['chest'], Decimal('38.00'))

    def test_deserialize_valid_all_fields(self):
        """Test deserializing valid data with all measurement fields."""
        data = {
            'chest': '38.50',
            'shoulder': '18.00',
            'neck': '15.50',
            'sleeve_length': '32.00',
            'sleeve_round': '14.00',
            'top_length': '28.50',
            'waist': '32.00',
            'thigh': '22.00',
            'knee': '16.00',
            'ankle': '10.00',
            'hips': '40.00',
            'trouser_length': '38.00'
        }
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = MeasurementSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        
        for field, value in data.items():
            self.assertEqual(serializer.validated_data[field], Decimal(value))

    def test_deserialize_decimal_precision(self):
        """Test that decimal values maintain 2 decimal places."""
        data = {'chest': '38.12'}
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = MeasurementSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['chest'], Decimal('38.12'))

    def test_deserialize_with_none_values(self):
        """Test deserializing with explicit None values for optional fields."""
        data = {
            'chest': '38.00',
            'shoulder': None,
            'neck': None
        }
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = MeasurementSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['chest'], Decimal('38.00'))
        self.assertIsNone(serializer.validated_data.get('shoulder'))


class MeasurementSerializerFieldValidationTests(TestCase):
    """Test field-level validation for all measurement fields."""

    def setUp(self):
        """Set up test user and request factory."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = APIRequestFactory()

    def get_context(self):
        """Helper to get request context."""
        request = self.factory.post('/')
        request.user = self.user
        return {'request': request}

    # CHEST FIELD VALIDATION
    def test_chest_min_validation(self):
        """Test chest field minimum value validation (20.00)."""
        data = {'chest': '19.99'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('chest', serializer.errors)
        self.assertIn('20 inches', str(serializer.errors['chest'][0]))

    def test_chest_max_validation(self):
        """Test chest field maximum value validation (70.00)."""
        data = {'chest': '70.01'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('chest', serializer.errors)
        self.assertIn('70 inches', str(serializer.errors['chest'][0]))

    def test_chest_valid_boundaries(self):
        """Test chest field accepts valid boundary values."""
        # Minimum boundary
        data_min = {'chest': '20.00'}
        serializer_min = MeasurementSerializer(data=data_min, context=self.get_context())
        self.assertTrue(serializer_min.is_valid())
        
        # Maximum boundary
        data_max = {'chest': '70.00'}
        serializer_max = MeasurementSerializer(data=data_max, context=self.get_context())
        self.assertTrue(serializer_max.is_valid())

    # SHOULDER FIELD VALIDATION
    def test_shoulder_min_validation(self):
        """Test shoulder field minimum value validation (12.00)."""
        data = {'shoulder': '11.99'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('shoulder', serializer.errors)
        self.assertIn('12 inches', str(serializer.errors['shoulder'][0]))

    def test_shoulder_max_validation(self):
        """Test shoulder field maximum value validation (30.00)."""
        data = {'shoulder': '30.01'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('shoulder', serializer.errors)
        self.assertIn('30 inches', str(serializer.errors['shoulder'][0]))

    def test_shoulder_valid_boundaries(self):
        """Test shoulder field accepts valid boundary values."""
        data_min = {'shoulder': '12.00'}
        serializer_min = MeasurementSerializer(data=data_min, context=self.get_context())
        self.assertTrue(serializer_min.is_valid())
        
        data_max = {'shoulder': '30.00'}
        serializer_max = MeasurementSerializer(data=data_max, context=self.get_context())
        self.assertTrue(serializer_max.is_valid())

    # NECK FIELD VALIDATION
    def test_neck_min_validation(self):
        """Test neck field minimum value validation (10.00)."""
        data = {'neck': '9.99'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('neck', serializer.errors)
        self.assertIn('10 inches', str(serializer.errors['neck'][0]))

    def test_neck_max_validation(self):
        """Test neck field maximum value validation (30.00)."""
        data = {'neck': '30.01'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('neck', serializer.errors)
        self.assertIn('30 inches', str(serializer.errors['neck'][0]))

    # SLEEVE_LENGTH FIELD VALIDATION
    def test_sleeve_length_min_validation(self):
        """Test sleeve_length field minimum value validation (20.00)."""
        data = {'sleeve_length': '19.99'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('sleeve_length', serializer.errors)
        self.assertIn('20 inches', str(serializer.errors['sleeve_length'][0]))

    def test_sleeve_length_max_validation(self):
        """Test sleeve_length field maximum value validation (40.00)."""
        data = {'sleeve_length': '40.01'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('sleeve_length', serializer.errors)
        self.assertIn('40 inches', str(serializer.errors['sleeve_length'][0]))

    # SLEEVE_ROUND FIELD VALIDATION
    def test_sleeve_round_min_validation(self):
        """Test sleeve_round field minimum value validation (8.00)."""
        data = {'sleeve_round': '7.99'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('sleeve_round', serializer.errors)
        self.assertIn('8 inches', str(serializer.errors['sleeve_round'][0]))

    def test_sleeve_round_max_validation(self):
        """Test sleeve_round field maximum value validation (20.00)."""
        data = {'sleeve_round': '20.01'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('sleeve_round', serializer.errors)
        self.assertIn('20 inches', str(serializer.errors['sleeve_round'][0]))

    # TOP_LENGTH FIELD VALIDATION
    def test_top_length_min_validation(self):
        """Test top_length field minimum value validation (20.00)."""
        data = {'top_length': '19.99'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('top_length', serializer.errors)
        self.assertIn('20 inches', str(serializer.errors['top_length'][0]))

    def test_top_length_max_validation(self):
        """Test top_length field maximum value validation (40.00)."""
        data = {'top_length': '40.01'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('top_length', serializer.errors)
        self.assertIn('40 inches', str(serializer.errors['top_length'][0]))

    # WAIST FIELD VALIDATION
    def test_waist_min_validation(self):
        """Test waist field minimum value validation (20.00)."""
        data = {'waist': '19.99'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('waist', serializer.errors)
        self.assertIn('20 inches', str(serializer.errors['waist'][0]))

    def test_waist_max_validation(self):
        """Test waist field maximum value validation (60.00)."""
        data = {'waist': '60.01'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('waist', serializer.errors)
        self.assertIn('60 inches', str(serializer.errors['waist'][0]))

    # THIGH FIELD VALIDATION
    def test_thigh_min_validation(self):
        """Test thigh field minimum value validation (12.00)."""
        data = {'thigh': '11.99'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('thigh', serializer.errors)
        self.assertIn('12 inches', str(serializer.errors['thigh'][0]))

    def test_thigh_max_validation(self):
        """Test thigh field maximum value validation (40.00)."""
        data = {'thigh': '40.01'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('thigh', serializer.errors)
        self.assertIn('40 inches', str(serializer.errors['thigh'][0]))

    # KNEE FIELD VALIDATION
    def test_knee_min_validation(self):
        """Test knee field minimum value validation (10.00)."""
        data = {'knee': '9.99'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('knee', serializer.errors)
        self.assertIn('10 inches', str(serializer.errors['knee'][0]))

    def test_knee_max_validation(self):
        """Test knee field maximum value validation (30.00)."""
        data = {'knee': '30.01'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('knee', serializer.errors)
        self.assertIn('30 inches', str(serializer.errors['knee'][0]))

    # ANKLE FIELD VALIDATION
    def test_ankle_min_validation(self):
        """Test ankle field minimum value validation (7.00)."""
        data = {'ankle': '6.99'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('ankle', serializer.errors)
        self.assertIn('7 inches', str(serializer.errors['ankle'][0]))

    def test_ankle_max_validation(self):
        """Test ankle field maximum value validation (20.00)."""
        data = {'ankle': '20.01'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('ankle', serializer.errors)
        self.assertIn('20 inches', str(serializer.errors['ankle'][0]))

    # HIPS FIELD VALIDATION
    def test_hips_min_validation(self):
        """Test hips field minimum value validation (25.00)."""
        data = {'hips': '24.99'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('hips', serializer.errors)
        self.assertIn('25 inches', str(serializer.errors['hips'][0]))

    def test_hips_max_validation(self):
        """Test hips field maximum value validation (70.00)."""
        data = {'hips': '70.01'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('hips', serializer.errors)
        self.assertIn('70 inches', str(serializer.errors['hips'][0]))

    # TROUSER_LENGTH FIELD VALIDATION
    def test_trouser_length_min_validation(self):
        """Test trouser_length field minimum value validation (25.00)."""
        data = {'trouser_length': '24.99'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('trouser_length', serializer.errors)
        self.assertIn('25 inches', str(serializer.errors['trouser_length'][0]))

    def test_trouser_length_max_validation(self):
        """Test trouser_length field maximum value validation (50.00)."""
        data = {'trouser_length': '50.01'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('trouser_length', serializer.errors)
        self.assertIn('50 inches', str(serializer.errors['trouser_length'][0]))

    # NEGATIVE VALUES
    def test_negative_values_rejected(self):
        """Test that negative values are rejected for all fields."""
        data = {'chest': '-10.00'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('chest', serializer.errors)

    # ZERO VALUES
    def test_zero_values_rejected(self):
        """Test that zero values are rejected (below minimum)."""
        data = {'chest': '0.00'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('chest', serializer.errors)


class MeasurementSerializerValidateMethodTests(TestCase):
    """Test the custom validate() method."""

    def setUp(self):
        """Set up test user and request factory."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = APIRequestFactory()

    def get_context(self):
        """Helper to get request context."""
        request = self.factory.post('/')
        request.user = self.user
        return {'request': request}

    def test_validate_fails_with_no_measurements(self):
        """Test that validate() fails when no measurement fields are provided."""
        data = {}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('at least one measurement', str(serializer.errors).lower())

    def test_validate_passes_with_one_measurement(self):
        """Test that validate() passes with at least one measurement field."""
        data = {'chest': '38.00'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertTrue(serializer.is_valid())

    def test_validate_passes_with_multiple_measurements(self):
        """Test that validate() passes with multiple measurement fields."""
        data = {
            'chest': '38.00',
            'waist': '32.00',
            'shoulder': '18.00'
        }
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertTrue(serializer.is_valid())

    def test_validate_with_all_none_values_fails(self):
        """Test that validate() fails when all measurement fields are None."""
        data = {
            'chest': None,
            'shoulder': None,
            'neck': None,
            'waist': None
        }
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_validate_on_update_with_existing_measurements(self):
        """Test that validate() passes on update even with no new measurements if instance has them."""
        # Create existing measurement
        measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal('38.00')
        )
        
        # Update with no measurement fields (but instance already has chest)
        data = {}  # Empty update
        serializer = MeasurementSerializer(
            instance=measurement,
            data=data,
            partial=True,
            context=self.get_context()
        )
        
        # Should be valid because instance already has chest measurement
        self.assertTrue(serializer.is_valid())

    def test_validate_on_partial_update_adding_new_field(self):
        """Test validate on partial update adding a new measurement field."""
        measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal('38.00')
        )
        
        data = {'waist': '32.00'}
        serializer = MeasurementSerializer(
            instance=measurement,
            data=data,
            partial=True,
            context=self.get_context()
        )
        
        self.assertTrue(serializer.is_valid())


class MeasurementSerializerReadOnlyFieldsTests(TestCase):
    """Test that read-only fields cannot be set via deserialization."""

    def setUp(self):
        """Set up test user and request factory."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = APIRequestFactory()

    def get_context(self):
        """Helper to get request context."""
        request = self.factory.post('/')
        request.user = self.user
        return {'request': request}

    def test_user_field_is_read_only(self):
        """Test that user field cannot be set via input data."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        data = {
            'chest': '38.00',
            'user': other_user.id  # Try to set different user
        }
        
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        self.assertTrue(serializer.is_valid())
        
        # User should not be in validated_data (read-only)
        self.assertNotIn('user', serializer.validated_data)

    def test_created_at_is_read_only(self):
        """Test that created_at field cannot be set via input data."""
        from django.utils import timezone
        future_date = timezone.now() + timezone.timedelta(days=10)
        
        data = {
            'chest': '38.00',
            'created_at': future_date.isoformat()
        }
        
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        self.assertTrue(serializer.is_valid())
        
        # created_at should not be in validated_data
        self.assertNotIn('created_at', serializer.validated_data)

    def test_updated_at_is_read_only(self):
        """Test that updated_at field cannot be set via input data."""
        from django.utils import timezone
        future_date = timezone.now() + timezone.timedelta(days=10)
        
        data = {
            'chest': '38.00',
            'updated_at': future_date.isoformat()
        }
        
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        self.assertTrue(serializer.is_valid())
        
        # updated_at should not be in validated_data
        self.assertNotIn('updated_at', serializer.validated_data)

    def test_is_deleted_is_read_only(self):
        """Test that is_deleted field cannot be set via input data."""
        data = {
            'chest': '38.00',
            'is_deleted': True
        }
        
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        self.assertTrue(serializer.is_valid())
        
        # is_deleted should not be in validated_data
        self.assertNotIn('is_deleted', serializer.validated_data)


class MeasurementSerializerCreateMethodTests(TestCase):
    """Test the create() method."""

    def setUp(self):
        """Set up test user and request factory."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = APIRequestFactory()

    def get_context(self):
        """Helper to get request context."""
        request = self.factory.post('/')
        request.user = self.user
        return {'request': request}

    def test_create_assigns_user_from_context(self):
        """Test that create() assigns user from request context."""
        data = {'chest': '38.00'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertTrue(serializer.is_valid())
        measurement = serializer.save()
        
        # User should be assigned from request.user
        self.assertEqual(measurement.user, self.user)

    def test_create_with_multiple_fields(self):
        """Test creating measurement with multiple fields."""
        data = {
            'chest': '38.00',
            'waist': '32.00',
            'shoulder': '18.00'
        }
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertTrue(serializer.is_valid())
        measurement = serializer.save()
        
        self.assertEqual(measurement.chest, Decimal('38.00'))
        self.assertEqual(measurement.waist, Decimal('32.00'))
        self.assertEqual(measurement.shoulder, Decimal('18.00'))
        self.assertEqual(measurement.user, self.user)

    def test_create_generates_uuid(self):
        """Test that create() generates a UUID for the measurement."""
        data = {'chest': '38.00'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertTrue(serializer.is_valid())
        measurement = serializer.save()
        
        self.assertIsNotNone(measurement.id)
        self.assertIsInstance(measurement.id, uuid.UUID)

    def test_create_sets_timestamps(self):
        """Test that create() sets created_at and updated_at."""
        data = {'chest': '38.00'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertTrue(serializer.is_valid())
        measurement = serializer.save()
        
        self.assertIsNotNone(measurement.created_at)
        self.assertIsNotNone(measurement.updated_at)

    def test_create_sets_is_deleted_to_false(self):
        """Test that create() sets is_deleted to False by default."""
        data = {'chest': '38.00'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertTrue(serializer.is_valid())
        measurement = serializer.save()
        
        self.assertFalse(measurement.is_deleted)


class MeasurementSerializerUpdateMethodTests(TestCase):
    """Test the update() method."""

    def setUp(self):
        """Set up test users, measurement, and request factory."""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.measurement = Measurement.objects.create(
            user=self.user1,
            chest=Decimal('38.00'),
            waist=Decimal('32.00')
        )
        self.factory = APIRequestFactory()

    def get_context(self, user=None):
        """Helper to get request context."""
        if user is None:
            user = self.user1
        request = self.factory.post('/')
        request.user = user
        return {'request': request}

    def test_update_modifies_existing_measurement(self):
        """Test that update() modifies existing measurement."""
        data = {'chest': '40.00'}
        serializer = MeasurementSerializer(
            instance=self.measurement,
            data=data,
            partial=True,
            context=self.get_context()
        )
        
        self.assertTrue(serializer.is_valid())
        updated_measurement = serializer.save()
        
        self.assertEqual(updated_measurement.chest, Decimal('40.00'))
        self.assertEqual(updated_measurement.waist, Decimal('32.00'))  # Unchanged

    def test_update_protects_user_field(self):
        """Test that update() protects user field from being changed."""
        data = {
            'chest': '40.00',
            'user': self.user2.id  # Try to change user
        }
        serializer = MeasurementSerializer(
            instance=self.measurement,
            data=data,
            partial=True,
            context=self.get_context()
        )
        
        self.assertTrue(serializer.is_valid())
        updated_measurement = serializer.save()
        
        # User should remain user1
        self.assertEqual(updated_measurement.user, self.user1)
        self.assertNotEqual(updated_measurement.user, self.user2)

    def test_update_partial_update(self):
        """Test partial update (PATCH) behavior."""
        data = {'waist': '34.00'}
        serializer = MeasurementSerializer(
            instance=self.measurement,
            data=data,
            partial=True,
            context=self.get_context()
        )
        
        self.assertTrue(serializer.is_valid())
        updated_measurement = serializer.save()
        
        self.assertEqual(updated_measurement.waist, Decimal('34.00'))
        self.assertEqual(updated_measurement.chest, Decimal('38.00'))  # Unchanged

    def test_update_full_update(self):
        """Test full update (PUT) behavior."""
        data = {
            'chest': '40.00',
            'waist': '34.00',
            'shoulder': '18.00'
        }
        serializer = MeasurementSerializer(
            instance=self.measurement,
            data=data,
            context=self.get_context()
        )
        
        self.assertTrue(serializer.is_valid())
        updated_measurement = serializer.save()
        
        self.assertEqual(updated_measurement.chest, Decimal('40.00'))
        self.assertEqual(updated_measurement.waist, Decimal('34.00'))
        self.assertEqual(updated_measurement.shoulder, Decimal('18.00'))

    def test_update_preserves_id(self):
        """Test that update() preserves the measurement ID."""
        original_id = self.measurement.id
        
        data = {'chest': '40.00'}
        serializer = MeasurementSerializer(
            instance=self.measurement,
            data=data,
            partial=True,
            context=self.get_context()
        )
        
        self.assertTrue(serializer.is_valid())
        updated_measurement = serializer.save()
        
        self.assertEqual(updated_measurement.id, original_id)

    def test_update_preserves_created_at(self):
        """Test that update() preserves created_at timestamp."""
        original_created_at = self.measurement.created_at
        
        data = {'chest': '40.00'}
        serializer = MeasurementSerializer(
            instance=self.measurement,
            data=data,
            partial=True,
            context=self.get_context()
        )
        
        self.assertTrue(serializer.is_valid())
        updated_measurement = serializer.save()
        
        self.assertEqual(updated_measurement.created_at, original_created_at)


class MeasurementSerializerEdgeCaseTests(TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test user and request factory."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = APIRequestFactory()

    def get_context(self):
        """Helper to get request context."""
        request = self.factory.post('/')
        request.user = self.user
        return {'request': request}

    def test_all_fields_at_minimum_boundaries(self):
        """Test serializer accepts all fields at minimum boundary values."""
        data = {
            'chest': '20.00',
            'shoulder': '12.00',
            'neck': '10.00',
            'sleeve_length': '20.00',
            'sleeve_round': '8.00',
            'top_length': '20.00',
            'waist': '20.00',
            'thigh': '12.00',
            'knee': '10.00',
            'ankle': '7.00',
            'hips': '25.00',
            'trouser_length': '25.00'
        }
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertTrue(serializer.is_valid())

    def test_all_fields_at_maximum_boundaries(self):
        """Test serializer accepts all fields at maximum boundary values."""
        data = {
            'chest': '70.00',
            'shoulder': '30.00',
            'neck': '30.00',
            'sleeve_length': '40.00',
            'sleeve_round': '20.00',
            'top_length': '40.00',
            'waist': '60.00',
            'thigh': '40.00',
            'knee': '30.00',
            'ankle': '20.00',
            'hips': '70.00',
            'trouser_length': '50.00'
        }
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertTrue(serializer.is_valid())

    def test_string_numbers_converted_to_decimal(self):
        """Test that string numbers are converted to Decimal."""
        data = {'chest': '38.50'}  # String
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertTrue(serializer.is_valid())
        self.assertIsInstance(serializer.validated_data['chest'], Decimal)
        self.assertEqual(serializer.validated_data['chest'], Decimal('38.50'))

    def test_integer_converted_to_decimal(self):
        """Test that integer values are converted to Decimal."""
        data = {'chest': 38}  # Integer
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertTrue(serializer.is_valid())
        self.assertIsInstance(serializer.validated_data['chest'], Decimal)

    def test_empty_string_rejected(self):
        """Test that empty string values are rejected."""
        data = {'chest': ''}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        # Empty string gets converted to None, triggering validate() method
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('at least one measurement', str(serializer.errors).lower())

    def test_whitespace_string_rejected(self):
        """Test that whitespace-only string values are rejected."""
        data = {'chest': '   '}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        # Whitespace gets converted to None or raises field error

    def test_invalid_data_type_rejected(self):
        """Test that invalid data types are rejected."""
        data = {'chest': 'not-a-number'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('chest', serializer.errors)

    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are reported."""
        data = {
            'chest': '10.00',  # Too small
            'waist': '70.00'   # Too large
        }
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('chest', serializer.errors)
        self.assertIn('waist', serializer.errors)

    def test_none_context_request(self):
        """Test behavior when context is missing request."""
        data = {'chest': '38.00'}
        serializer = MeasurementSerializer(data=data, context={})
        
        # Should fail validation or raise error when trying to save
        # because create() needs request.user
        if serializer.is_valid():
            with self.assertRaises((KeyError, AttributeError)):
                serializer.save()


class MeasurementSerializerCustomErrorMessageTests(TestCase):
    """Test custom error messages for all fields."""

    def setUp(self):
        """Set up test user and request factory."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = APIRequestFactory()

    def get_context(self):
        """Helper to get request context."""
        request = self.factory.post('/')
        request.user = self.user
        return {'request': request}

    def test_chest_min_error_message(self):
        """Test custom error message for chest minimum validation."""
        data = {'chest': '10.00'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        error_msg = str(serializer.errors['chest'][0])
        self.assertIn('Chest measurement must be at least 20 inches', error_msg)

    def test_chest_max_error_message(self):
        """Test custom error message for chest maximum validation."""
        data = {'chest': '80.00'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        error_msg = str(serializer.errors['chest'][0])
        self.assertIn('Chest measurement cannot exceed 70 inches', error_msg)

    def test_waist_min_error_message(self):
        """Test custom error message for waist minimum validation."""
        data = {'waist': '10.00'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        error_msg = str(serializer.errors['waist'][0])
        self.assertIn('Waist measurement must be at least 20 inches', error_msg)

    def test_ankle_max_error_message(self):
        """Test custom error message for ankle maximum validation."""
        data = {'ankle': '25.00'}
        serializer = MeasurementSerializer(data=data, context=self.get_context())
        
        self.assertFalse(serializer.is_valid())
        error_msg = str(serializer.errors['ankle'][0])
        self.assertIn('Ankle measurement cannot exceed 20 inches', error_msg)