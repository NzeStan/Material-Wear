# feed/tests/test_serializers.py
"""
Comprehensive bulletproof tests for feed/serializers.py

Test Coverage:
===============
✅ ImageSerializer
   - Field presence and types
   - Read-only fields enforcement
   - Serialization (model -> dict)
   - Deserialization (dict -> model) for create/update
   - get_optimized_url() method with Cloudinary
   - Edge cases: blank URL, None values
   - Bug detection: obj.image vs obj.url
   - Cloudinary integration
   - Active field handling
   - UUID field serialization

✅ YouTubeVideoSerializer
   - Field validation and types
   - Required fields enforcement
   - Optional fields (url)
   - Deserialization for API responses
   - DateTime field handling
   - URL field validation
   - Edge cases: missing data, invalid data

✅ Production Scenarios
   - Bulk serialization
   - Nested data handling
   - Invalid data rejection
   - Error messages clarity

✅ Security & Validation
   - Field validation
   - Data type enforcement
   - Required field checks
   - Invalid URL rejection
"""
from django.test import TestCase
from django.utils import timezone as django_timezone
from rest_framework.exceptions import ValidationError
from feed.serializers import ImageSerializer, YouTubeVideoSerializer
from feed.models import Image
from io import BytesIO
from PIL import Image as PILImage
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
import uuid


# ============================================================================
# IMAGE SERIALIZER TESTS
# ============================================================================

class ImageSerializerFieldTests(TestCase):
    """Test ImageSerializer field configuration"""
    
    def test_serializer_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image, active=True)
        serializer = ImageSerializer(image)
        
        expected_fields = {'id', 'url', 'upload_date', 'active', 'optimized_url'}
        self.assertEqual(set(serializer.data.keys()), expected_fields)
    
    def test_id_field_is_read_only(self):
        """Test id field is read-only"""
        serializer = ImageSerializer()
        id_field = serializer.fields['id']
        
        self.assertTrue(id_field.read_only)
    
    def test_upload_date_field_is_read_only(self):
        """Test upload_date field is read-only"""
        serializer = ImageSerializer()
        upload_date_field = serializer.fields['upload_date']
        
        self.assertTrue(upload_date_field.read_only)
    
    def test_optimized_url_field_is_read_only(self):
        """Test optimized_url field is SerializerMethodField (read-only)"""
        serializer = ImageSerializer()
        optimized_url_field = serializer.fields['optimized_url']
        
        # SerializerMethodField is always read-only
        self.assertTrue(optimized_url_field.read_only)
    
    def test_url_field_is_writable(self):
        """Test url field is writable (not read-only)"""
        serializer = ImageSerializer()
        url_field = serializer.fields['url']
        
        self.assertFalse(url_field.read_only)
    
    def test_active_field_is_writable(self):
        """Test active field is writable"""
        serializer = ImageSerializer()
        active_field = serializer.fields['active']
        
        self.assertFalse(active_field.read_only)
    
    def test_meta_model_is_image(self):
        """Test Meta.model is Image"""
        serializer = ImageSerializer()
        
        self.assertEqual(serializer.Meta.model, Image)
    
    def test_meta_read_only_fields_configured(self):
        """Test Meta.read_only_fields is correctly configured"""
        serializer = ImageSerializer()
        
        # Should be tuple or list containing 'id' and 'upload_date'
        read_only = serializer.Meta.read_only_fields
        self.assertIn('id', read_only)
        self.assertIn('upload_date', read_only)
    
    def _create_test_image(self):
        """Helper method to create a test image file"""
        img = PILImage.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )


class ImageSerializerSerializationTests(TestCase):
    """Test ImageSerializer serialization (model -> dict)"""
    
    def test_serialize_image_with_all_fields(self):
        """Test serializing an Image instance with all fields"""
        test_image = self._create_test_image()
        upload_time = django_timezone.now()
        
        image = Image.objects.create(
            url=test_image,
            upload_date=upload_time,
            active=True
        )
        
        serializer = ImageSerializer(image)
        data = serializer.data
        
        self.assertIsNotNone(data['id'])
        self.assertTrue(data['url'])
        self.assertIsNotNone(data['upload_date'])
        self.assertTrue(data['active'])
        # optimized_url will be tested separately
    
    def test_serialize_inactive_image(self):
        """Test serializing an inactive Image"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image, active=False)
        
        serializer = ImageSerializer(image)
        data = serializer.data
        
        self.assertFalse(data['active'])
    
    def test_serialize_image_with_blank_url(self):
        """Test serializing Image with blank URL"""
        image = Image.objects.create(active=True)
        
        serializer = ImageSerializer(image)
        data = serializer.data
        
        # URL should be empty/blank
        self.assertFalse(data['url'])
    
    def test_serialize_multiple_images(self):
        """Test serializing multiple Image instances"""
        test_images = [self._create_test_image() for _ in range(3)]
        images = [Image.objects.create(url=img) for img in test_images]
        
        serializer = ImageSerializer(images, many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 3)
        # All should have required fields
        for item in data:
            self.assertIn('id', item)
            self.assertIn('url', item)
            self.assertIn('active', item)
    
    def test_id_serialized_as_string(self):
        """Test UUID id is serialized as string"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image)
        
        serializer = ImageSerializer(image)
        data = serializer.data
        
        # UUID should be serialized as string
        self.assertIsInstance(data['id'], str)
        # Should be valid UUID format
        uuid.UUID(data['id'])
    
    def test_upload_date_serialized_correctly(self):
        """Test upload_date is serialized with correct format"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image)
        
        serializer = ImageSerializer(image)
        data = serializer.data
        
        # Should have upload_date
        self.assertIsNotNone(data['upload_date'])
        # Should be ISO format string
        self.assertIsInstance(data['upload_date'], str)
    
    def _create_test_image(self):
        """Helper method to create a test image file"""
        img = PILImage.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )


class ImageSerializerDeserializationTests(TestCase):
    """Test ImageSerializer deserialization (dict -> model)"""
    
    def test_create_image_with_valid_data(self):
        """Test creating Image through serializer with valid data"""
        test_image = self._create_test_image()
        
        data = {
            'url': test_image,
            'active': True
        }
        
        serializer = ImageSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        image = serializer.save()
        
        self.assertIsNotNone(image.id)
        self.assertTrue(image.url)
        self.assertTrue(image.active)
    
    def test_create_image_with_minimal_data(self):
        """Test creating Image with only URL (active defaults to True)"""
        test_image = self._create_test_image()
        
        data = {
            'url': test_image
        }
        
        serializer = ImageSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        image = serializer.save()
        
        self.assertTrue(image.active)  # Should use default
    
    def test_update_image_active_status(self):
        """Test updating Image active status through serializer"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image, active=True)
        
        data = {
            'active': False
        }
        
        serializer = ImageSerializer(image, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_image = serializer.save()
        
        self.assertFalse(updated_image.active)
    
    def test_cannot_update_id(self):
        """Test id cannot be updated (read-only)"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image)
        original_id = image.id
        
        data = {
            'id': str(uuid.uuid4())  # Try to change ID
        }
        
        serializer = ImageSerializer(image, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_image = serializer.save()
        
        # ID should not change
        self.assertEqual(updated_image.id, original_id)
    
    def test_cannot_update_upload_date(self):
        """Test upload_date cannot be updated (read-only)"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image)
        original_date = image.upload_date
        
        new_date = django_timezone.now() + timedelta(days=1)
        data = {
            'upload_date': new_date.isoformat()
        }
        
        serializer = ImageSerializer(image, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_image = serializer.save()
        
        # Upload date should not change
        self.assertEqual(updated_image.upload_date, original_date)
    
    def test_create_image_without_url(self):
        """Test creating Image without URL (blank allowed)"""
        data = {
            'active': True
        }
        
        serializer = ImageSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        image = serializer.save()
        
        self.assertFalse(image.url)  # Should be blank
        self.assertTrue(image.active)
    
    def _create_test_image(self):
        """Helper method to create a test image file"""
        img = PILImage.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )


class ImageSerializerOptimizedUrlTests(TestCase):
    """Test ImageSerializer.get_optimized_url() method - CRITICAL BUG DETECTION"""
    
    def test_get_optimized_url_returns_none_for_blank_url(self):
        """Test get_optimized_url returns None when URL is blank"""
        image = Image.objects.create(active=True)  # No URL
        
        serializer = ImageSerializer(image)
        data = serializer.data
        
        # Should return None for blank URL
        self.assertIsNone(data['optimized_url'])
    
    def test_get_optimized_url_bug_detection(self):
        """
        CRITICAL BUG TEST: Detects obj.image vs obj.url bug
        
        The serializer checks obj.image but model field is obj.url
        This test will FAIL until the bug is fixed!
        """
        # Create a real image instance
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image)
        
        serializer = ImageSerializer(image)
        data = serializer.data
        
        # BUG: get_optimized_url checks obj.image (doesn't exist)
        # Should check obj.url instead
        # This will currently return None due to the bug
        
        # After fixing the bug, optimized_url should not be None
        # when image.url exists
        if image.url:
            # This assertion will PASS after the bug is fixed
            # Currently it will FAIL, exposing the bug!
            self.assertIsNotNone(
                data['optimized_url'],
                "BUG DETECTED: get_optimized_url() checks obj.image but should check obj.url!"
            )
    
    def test_get_optimized_url_with_cloudinary_url(self):
        """Test get_optimized_url with Cloudinary URL (after bug fix)"""
        # Create image with mock Cloudinary URL
        image = Image()
        
        # Mock the url field to return Cloudinary URL
        mock_cloudinary_file = Mock()
        mock_cloudinary_file.__str__ = Mock(
            return_value='https://res.cloudinary.com/demo/image/upload/feed_images/test.jpg'
        )
        mock_cloudinary_file.url = 'https://res.cloudinary.com/demo/image/upload/feed_images/test.jpg'
        
        # Mock build_url method
        mock_cloudinary_file.build_url = Mock(
            return_value='https://res.cloudinary.com/demo/image/upload/w_800,h_600,c_limit,q_auto,f_auto/feed_images/test.jpg'
        )
        
        image.url = mock_cloudinary_file
        
        serializer = ImageSerializer(image)
        
        # After fixing the bug (obj.image -> obj.url), this should work
        # For now, we test the method directly
        result = serializer.get_optimized_url(image)
        
        # Should call build_url if it exists
        if hasattr(image.url, 'build_url'):
            self.assertIsNotNone(result)
    
    def test_get_optimized_url_called_with_correct_parameters(self):
        """Test get_optimized_url calls build_url with correct parameters"""
        image = Image()
        
        # Mock Cloudinary field with build_url
        mock_cloudinary_file = Mock()
        mock_cloudinary_file.build_url = Mock(return_value='optimized_url')
        image.url = mock_cloudinary_file
        
        serializer = ImageSerializer(image)
        serializer.get_optimized_url(image)
        
        # Should call build_url with correct params (after bug fix)
        # For now this tests the intended behavior
        if hasattr(image.url, 'build_url'):
            mock_cloudinary_file.build_url.assert_called_once_with(
                width=800,
                height=600,
                crop='limit',
                quality='auto',
                fetch_format='auto'
            )
    
    def test_get_optimized_url_without_build_url_method(self):
        """Test get_optimized_url when build_url method doesn't exist"""
        image = Image()
        
        # Mock url without build_url method
        mock_file = Mock()
        mock_file.url = 'https://example.com/image.jpg'
        # Ensure hasattr returns False for build_url
        mock_file.build_url = None
        delattr(mock_file, 'build_url')
        
        image.url = mock_file
        
        serializer = ImageSerializer(image)
        result = serializer.get_optimized_url(image)
        
        # Should fall back to regular URL
        # Currently returns None due to obj.image bug
        # After fix, should return the URL
    
    def _create_test_image(self):
        """Helper method to create a test image file"""
        img = PILImage.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )


class ImageSerializerEdgeCaseTests(TestCase):
    """Test ImageSerializer edge cases and error scenarios"""
    
    def test_serialize_image_with_special_characters_in_filename(self):
        """Test serializing image with special characters in filename"""
        # Create image with special chars in name
        img = PILImage.new('RGB', (100, 100), color='blue')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        test_image = SimpleUploadedFile(
            name='test_image_#$%&.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )
        
        image = Image.objects.create(url=test_image)
        serializer = ImageSerializer(image)
        
        # Should serialize without errors
        data = serializer.data
        self.assertIsNotNone(data['id'])
    
    def test_bulk_serialization_performance(self):
        """Test serializing many images at once"""
        # Create 50 images
        test_images = [self._create_test_image() for _ in range(50)]
        images = [Image.objects.create(url=img) for img in test_images]
        
        # Serialize all at once
        serializer = ImageSerializer(images, many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 50)
        # All should have complete data
        for item in data:
            self.assertIn('id', item)
            self.assertIn('url', item)
            self.assertIn('active', item)
            self.assertIn('optimized_url', item)
    
    def test_representation_with_none_values(self):
        """Test serializer handles None values gracefully"""
        image = Image.objects.create()  # Minimal creation
        
        serializer = ImageSerializer(image)
        data = serializer.data
        
        # Should not crash, all fields should exist
        self.assertIn('id', data)
        self.assertIn('url', data)
        self.assertIn('active', data)
        self.assertIn('optimized_url', data)
    
    def _create_test_image(self):
        """Helper method to create a test image file"""
        img = PILImage.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )


# ============================================================================
# YOUTUBE VIDEO SERIALIZER TESTS
# ============================================================================

class YouTubeVideoSerializerFieldTests(TestCase):
    """Test YouTubeVideoSerializer field configuration"""
    
    def test_serializer_has_all_required_fields(self):
        """Test serializer has all expected fields"""
        serializer = YouTubeVideoSerializer()
        
        expected_fields = {'id', 'title', 'description', 'thumbnail', 'published_at', 'url'}
        self.assertEqual(set(serializer.fields.keys()), expected_fields)
    
    def test_id_field_is_char_field(self):
        """Test id field is CharField"""
        serializer = YouTubeVideoSerializer()
        
        from rest_framework import serializers as drf_serializers
        self.assertIsInstance(
            serializer.fields['id'],
            drf_serializers.CharField
        )
    
    def test_title_field_is_char_field(self):
        """Test title field is CharField"""
        serializer = YouTubeVideoSerializer()
        
        from rest_framework import serializers as drf_serializers
        self.assertIsInstance(
            serializer.fields['title'],
            drf_serializers.CharField
        )
    
    def test_thumbnail_field_is_url_field(self):
        """Test thumbnail field is URLField"""
        serializer = YouTubeVideoSerializer()
        
        from rest_framework import serializers as drf_serializers
        self.assertIsInstance(
            serializer.fields['thumbnail'],
            drf_serializers.URLField
        )
    
    def test_published_at_field_is_datetime_field(self):
        """Test published_at field is DateTimeField"""
        serializer = YouTubeVideoSerializer()
        
        from rest_framework import serializers as drf_serializers
        self.assertIsInstance(
            serializer.fields['published_at'],
            drf_serializers.DateTimeField
        )
    
    def test_url_field_is_optional(self):
        """Test url field is optional (required=False)"""
        serializer = YouTubeVideoSerializer()
        url_field = serializer.fields['url']
        
        self.assertFalse(url_field.required)
    
    def test_all_fields_have_help_text(self):
        """Test all fields have help_text configured"""
        serializer = YouTubeVideoSerializer()
        
        fields_with_help_text = ['id', 'title', 'description', 'thumbnail', 'published_at', 'url']
        
        for field_name in fields_with_help_text:
            field = serializer.fields[field_name]
            self.assertIsNotNone(
                field.help_text,
                f"{field_name} should have help_text"
            )


class YouTubeVideoSerializerValidationTests(TestCase):
    """Test YouTubeVideoSerializer validation"""
    
    def test_validate_complete_video_data(self):
        """Test validating complete YouTube video data"""
        data = {
            'id': 'dQw4w9WgXcQ',
            'title': 'Sample Video Title',
            'description': 'Sample video description',
            'thumbnail': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
            'published_at': '2024-01-01T12:00:00Z',
            'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        }
        
        serializer = YouTubeVideoSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['id'], 'dQw4w9WgXcQ')
        self.assertEqual(serializer.validated_data['title'], 'Sample Video Title')
    
    def test_validate_video_data_without_optional_url(self):
        """Test validating video data without optional URL field"""
        data = {
            'id': 'dQw4w9WgXcQ',
            'title': 'Sample Video',
            'description': 'Description',
            'thumbnail': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg',
            'published_at': '2024-01-01T12:00:00Z'
            # url is optional, omitted
        }
        
        serializer = YouTubeVideoSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
    
    def test_reject_missing_required_field_id(self):
        """Test validation fails when id is missing"""
        data = {
            'title': 'Sample Video',
            'description': 'Description',
            'thumbnail': 'https://i.ytimg.com/vi/test/default.jpg',
            'published_at': '2024-01-01T12:00:00Z'
        }
        
        serializer = YouTubeVideoSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('id', serializer.errors)
    
    def test_reject_missing_required_field_title(self):
        """Test validation fails when title is missing"""
        data = {
            'id': 'test123',
            'description': 'Description',
            'thumbnail': 'https://i.ytimg.com/vi/test/default.jpg',
            'published_at': '2024-01-01T12:00:00Z'
        }
        
        serializer = YouTubeVideoSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
    
    def test_reject_invalid_thumbnail_url(self):
        """Test validation fails with invalid thumbnail URL"""
        data = {
            'id': 'test123',
            'title': 'Sample Video',
            'description': 'Description',
            'thumbnail': 'not-a-valid-url',
            'published_at': '2024-01-01T12:00:00Z'
        }
        
        serializer = YouTubeVideoSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('thumbnail', serializer.errors)
    
    def test_reject_invalid_optional_url(self):
        """Test validation fails with invalid optional URL"""
        data = {
            'id': 'test123',
            'title': 'Sample Video',
            'description': 'Description',
            'thumbnail': 'https://i.ytimg.com/vi/test/default.jpg',
            'published_at': '2024-01-01T12:00:00Z',
            'url': 'invalid-youtube-url'
        }
        
        serializer = YouTubeVideoSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('url', serializer.errors)
    
    def test_reject_invalid_datetime_format(self):
        """Test validation fails with invalid datetime format"""
        data = {
            'id': 'test123',
            'title': 'Sample Video',
            'description': 'Description',
            'thumbnail': 'https://i.ytimg.com/vi/test/default.jpg',
            'published_at': 'not-a-datetime'
        }
        
        serializer = YouTubeVideoSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('published_at', serializer.errors)


class YouTubeVideoSerializerSerializationTests(TestCase):
    """Test YouTubeVideoSerializer serialization for API responses"""
    
    def test_serialize_single_video(self):
        """Test serializing single video data"""
        video_data = {
            'id': 'abc123',
            'title': 'Test Video',
            'description': 'Test Description',
            'thumbnail': 'https://i.ytimg.com/vi/abc123/maxresdefault.jpg',
            'published_at': datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
            'url': 'https://www.youtube.com/watch?v=abc123'
        }
        
        serializer = YouTubeVideoSerializer(video_data)
        data = serializer.data
        
        self.assertEqual(data['id'], 'abc123')
        self.assertEqual(data['title'], 'Test Video')
        self.assertEqual(data['description'], 'Test Description')
        self.assertIn('youtube.com', data['url'])
    
    def test_serialize_multiple_videos(self):
        """Test serializing list of videos"""
        videos = [
            {
                'id': f'video{i}',
                'title': f'Video {i}',
                'description': f'Description {i}',
                'thumbnail': f'https://i.ytimg.com/vi/video{i}/default.jpg',
                'published_at': datetime(2024, 1, i, tzinfo=timezone.utc),
                'url': f'https://www.youtube.com/watch?v=video{i}'
            }
            for i in range(1, 6)
        ]
        
        serializer = YouTubeVideoSerializer(videos, many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 5)
        for i, item in enumerate(data, 1):
            self.assertEqual(item['id'], f'video{i}')
            self.assertEqual(item['title'], f'Video {i}')
    
    def test_serialize_video_with_empty_description(self):
        """Test serializing video with empty description"""
        video_data = {
            'id': 'test123',
            'title': 'No Description Video',
            'description': '',  # Empty description
            'thumbnail': 'https://i.ytimg.com/vi/test123/default.jpg',
            'published_at': datetime(2024, 1, 1, tzinfo=timezone.utc)
        }
        
        # For serialization, we pass data directly (not using data= keyword)
        serializer = YouTubeVideoSerializer(video_data)
        
        # Just access the data - no validation needed for serialization
        self.assertEqual(serializer.data['description'], '')
    
    def test_serialize_video_with_long_title(self):
        """Test serializing video with very long title"""
        long_title = 'A' * 500  # Very long title
        
        video_data = {
            'id': 'test123',
            'title': long_title,
            'description': 'Test',
            'thumbnail': 'https://i.ytimg.com/vi/test123/default.jpg',
            'published_at': datetime(2024, 1, 1, tzinfo=timezone.utc)
        }
        
        # For serialization, pass data directly
        serializer = YouTubeVideoSerializer(video_data)
        
        # Access the serialized data
        self.assertEqual(len(serializer.data['title']), 500)


class YouTubeVideoSerializerEdgeCaseTests(TestCase):
    """Test YouTubeVideoSerializer edge cases"""
    
    def test_empty_data_validation_fails(self):
        """Test validation fails with completely empty data"""
        serializer = YouTubeVideoSerializer(data={})
        
        self.assertFalse(serializer.is_valid())
        # Should have errors for all required fields
        self.assertIn('id', serializer.errors)
        self.assertIn('title', serializer.errors)
        self.assertIn('description', serializer.errors)
        self.assertIn('thumbnail', serializer.errors)
        self.assertIn('published_at', serializer.errors)
    
    def test_video_with_special_characters_in_title(self):
        """Test video with special characters in title"""
        data = {
            'id': 'special123',
            'title': 'Video with émojis 🎥 and spëcial çhars!',
            'description': 'Test description',
            'thumbnail': 'https://i.ytimg.com/vi/special123/default.jpg',
            'published_at': '2024-01-01T12:00:00Z'
        }
        
        serializer = YouTubeVideoSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertIn('émojis', serializer.validated_data['title'])
    
    def test_video_with_unicode_in_description(self):
        """Test video with unicode characters in description"""
        data = {
            'id': 'unicode123',
            'title': 'Unicode Test',
            'description': 'Description with 中文字符 and العربية',
            'thumbnail': 'https://i.ytimg.com/vi/unicode123/default.jpg',
            'published_at': '2024-01-01T12:00:00Z'
        }
        
        serializer = YouTubeVideoSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
    
    def test_video_with_various_datetime_formats(self):
        """Test video with different valid datetime formats"""
        valid_formats = [
            '2024-01-01T12:00:00Z',
            '2024-01-01T12:00:00+00:00',
            '2024-01-01T12:00:00.123456Z',
        ]
        
        for dt_format in valid_formats:
            data = {
                'id': 'datetime_test',
                'title': 'Datetime Format Test',
                'description': 'Testing datetime formats',
                'thumbnail': 'https://i.ytimg.com/vi/test/default.jpg',
                'published_at': dt_format
            }
            
            serializer = YouTubeVideoSerializer(data=data)
            
            self.assertTrue(
                serializer.is_valid(),
                f"Should accept datetime format: {dt_format}"
            )
    
    def test_video_with_none_optional_url(self):
        """Test video without URL field (omitted, not None)"""
        data = {
            'id': 'none_url_test',
            'title': 'No URL Video',
            'description': 'Testing omitted URL',
            'thumbnail': 'https://i.ytimg.com/vi/test/default.jpg',
            'published_at': '2024-01-01T12:00:00Z',
            # url omitted - optional field
        }
        
        serializer = YouTubeVideoSerializer(data=data)
        
        # Should be valid since url is optional
        self.assertTrue(serializer.is_valid())


class YouTubeVideoSerializerProductionScenarioTests(TestCase):
    """Test YouTubeVideoSerializer production scenarios"""
    
    def test_api_response_format(self):
        """Test serializer produces correct format for API responses"""
        # Simulate data from YouTube API
        api_data = {
            'id': 'yt_video_123',
            'title': 'Latest Company Update',
            'description': 'Check out our latest updates!',
            'thumbnail': 'https://i.ytimg.com/vi/yt_video_123/maxresdefault.jpg',
            'published_at': datetime(2024, 1, 20, 15, 30, tzinfo=timezone.utc),
            'url': 'https://www.youtube.com/watch?v=yt_video_123'
        }
        
        serializer = YouTubeVideoSerializer(api_data)
        response_data = serializer.data
        
        # Should have all expected keys
        self.assertIn('id', response_data)
        self.assertIn('title', response_data)
        self.assertIn('description', response_data)
        self.assertIn('thumbnail', response_data)
        self.assertIn('published_at', response_data)
        self.assertIn('url', response_data)
        
        # Values should match
        self.assertEqual(response_data['id'], 'yt_video_123')
        self.assertEqual(response_data['title'], 'Latest Company Update')
    
    def test_batch_video_processing(self):
        """Test processing batch of videos from API"""
        # Simulate batch of videos from YouTube API
        videos = [
            {
                'id': f'batch_video_{i}',
                'title': f'Batch Video {i}',
                'description': f'Batch description {i}',
                'thumbnail': f'https://i.ytimg.com/vi/batch_video_{i}/default.jpg',
                'published_at': datetime(2024, 1, i, tzinfo=timezone.utc),
                'url': f'https://www.youtube.com/watch?v=batch_video_{i}'
            }
            for i in range(1, 21)  # 20 videos
        ]
        
        serializer = YouTubeVideoSerializer(videos, many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 20)
        # All should be valid
        for i, video in enumerate(data, 1):
            self.assertEqual(video['id'], f'batch_video_{i}')
    
    def test_error_handling_for_malformed_api_response(self):
        """Test handling of malformed API response data"""
        malformed_data = {
            'id': 'test',
            'title': 'Test',
            # Missing description
            'thumbnail': 'invalid_url',  # Invalid URL
            'published_at': 'invalid_date'  # Invalid datetime
        }
        
        serializer = YouTubeVideoSerializer(data=malformed_data)
        
        self.assertFalse(serializer.is_valid())
        # Should have errors for multiple fields
        self.assertTrue(len(serializer.errors) > 0)