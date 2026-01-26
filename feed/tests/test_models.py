# feed/tests/test_models.py
"""
Comprehensive tests for Feed Models

Coverage:
- Image Model:
  * UUID primary key generation and uniqueness
  * ImageField with Cloudinary storage integration
  * upload_date auto-generation and timezone awareness
  * active field default behavior
  * Model ordering by upload_date descending
  * get_optimized_url() method for Cloudinary transformations
  * String representation
  * Edge cases: blank URLs, special characters, timezone handling
  * Production scenarios: concurrent creation, bulk operations

- YouTubeCache Model:
  * Unmanaged model behavior (no database operations)
  * Meta options for admin interface
  * Model doesn't interfere with database

Test Philosophy:
- Verify model creation succeeds with valid data
- Test all field defaults and auto-generation
- Validate model methods work correctly
- Test edge cases that could break in production
- Ensure constraints are enforced
- Verify Meta options are correct
- Test model relationships and inheritance
"""
from django.test import TestCase
from django.utils import timezone as django_timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from feed.models import Image, YouTubeCache
from io import BytesIO
from PIL import Image as PILImage
from django.core.files.uploadedfile import SimpleUploadedFile
import uuid
from datetime import timedelta, datetime, timezone
from unittest.mock import Mock, patch


class ImageModelCreationTests(TestCase):
    """Test Image model creation and field defaults"""
    
    def test_image_creation_with_all_fields(self):
        """Test creating Image with all fields specified"""
        # Create a simple test image
        test_image = self._create_test_image()
        
        upload_time = django_timezone.now()
        image = Image.objects.create(
            url=test_image,
            upload_date=upload_time,
            active=True
        )
        
        self.assertIsNotNone(image.id)
        self.assertIsInstance(image.id, uuid.UUID)
        self.assertTrue(image.url)
        self.assertEqual(image.upload_date, upload_time)
        self.assertTrue(image.active)
    
    def test_image_creation_with_minimal_fields(self):
        """Test creating Image with only required fields (defaults applied)"""
        test_image = self._create_test_image()
        
        image = Image.objects.create(url=test_image)
        
        self.assertIsNotNone(image.id)
        self.assertIsInstance(image.id, uuid.UUID)
        self.assertTrue(image.active)  # Default is True
        self.assertIsNotNone(image.upload_date)  # Auto-generated
    
    def test_image_creation_with_blank_url(self):
        """Test creating Image with blank URL (allowed by blank=True)"""
        image = Image.objects.create()
        
        self.assertIsNotNone(image.id)
        self.assertFalse(image.url)  # Should be empty/blank
        self.assertTrue(image.active)
        self.assertIsNotNone(image.upload_date)
    
    def test_image_id_is_uuid(self):
        """Test Image ID is a valid UUID"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image)
        
        self.assertIsInstance(image.id, uuid.UUID)
        # Verify it's a valid UUID4
        self.assertEqual(image.id.version, 4)
    
    def test_image_id_auto_generated(self):
        """Test Image ID is automatically generated if not provided"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image)
        
        self.assertIsNotNone(image.id)
        # Verify ID is not editable (can't be changed after creation)
        original_id = image.id
        image.save()
        self.assertEqual(image.id, original_id)
    
    def test_image_id_uniqueness(self):
        """Test Image IDs are unique across instances"""
        test_image1 = self._create_test_image()
        test_image2 = self._create_test_image()
        
        image1 = Image.objects.create(url=test_image1)
        image2 = Image.objects.create(url=test_image2)
        
        self.assertNotEqual(image1.id, image2.id)
    
    def test_upload_date_auto_generated(self):
        """Test upload_date is automatically set to current time"""
        before_creation = django_timezone.now()
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image)
        after_creation = django_timezone.now()
        
        self.assertIsNotNone(image.upload_date)
        self.assertGreaterEqual(image.upload_date, before_creation)
        self.assertLessEqual(image.upload_date, after_creation)
    
    def test_upload_date_timezone_aware(self):
        """Test upload_date is timezone-aware"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image)
        
        self.assertIsNotNone(image.upload_date.tzinfo)
    
    def test_active_field_default_true(self):
        """Test active field defaults to True"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image)
        
        self.assertTrue(image.active)
    
    def test_active_field_can_be_false(self):
        """Test active field can be explicitly set to False"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image, active=False)
        
        self.assertFalse(image.active)
    
    def _create_test_image(self):
        """Helper method to create a test image file"""
        # Create a simple 100x100 red image
        img = PILImage.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )


class ImageModelFieldTests(TestCase):
    """Test Image model field behavior and constraints"""
    
    def test_url_field_is_image_field(self):
        """Test url field is an ImageField (not URLField)"""
        url_field = Image._meta.get_field('url')
        
        self.assertEqual(url_field.__class__.__name__, 'ImageField')
    
    def test_url_field_uses_cloudinary_storage(self):
        """Test url field uses Cloudinary storage"""
        url_field = Image._meta.get_field('url')
        
        self.assertIsNotNone(url_field.storage)
        # Check storage class name contains Cloudinary
        storage_class = url_field.storage.__class__.__name__
        self.assertIn('Cloudinary', storage_class)
    
    def test_url_field_upload_to_path(self):
        """Test url field has correct upload_to path"""
        url_field = Image._meta.get_field('url')
        
        self.assertEqual(url_field.upload_to, 'feed_images/')
    
    def test_url_field_allows_blank(self):
        """Test url field allows blank values"""
        url_field = Image._meta.get_field('url')
        
        self.assertTrue(url_field.blank)
    
    def test_upload_date_field_has_default(self):
        """Test upload_date field has timezone.now as default"""
        upload_date_field = Image._meta.get_field('upload_date')
        
        self.assertIsNotNone(upload_date_field.default)
        # Test the default function returns a datetime
        default_value = upload_date_field.default()
        self.assertIsInstance(default_value, datetime)
    
    def test_id_field_not_editable(self):
        """Test id field is not editable"""
        id_field = Image._meta.get_field('id')
        
        self.assertFalse(id_field.editable)
    
    def test_id_field_is_primary_key(self):
        """Test id field is the primary key"""
        id_field = Image._meta.get_field('id')
        
        self.assertTrue(id_field.primary_key)


class ImageModelMethodTests(TestCase):
    """Test Image model methods"""
    
    def test_str_representation(self):
        """Test __str__ method returns expected format"""
        test_image = self._create_test_image()
        upload_time = django_timezone.now()
        image = Image.objects.create(
            url=test_image,
            upload_date=upload_time
        )
        
        expected_str = f"Image {image.id} - {upload_time}"
        self.assertEqual(str(image), expected_str)
    
    def test_str_representation_contains_id(self):
        """Test __str__ contains the image ID"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image)
        
        str_repr = str(image)
        self.assertIn(str(image.id), str_repr)
    
    def test_str_representation_contains_date(self):
        """Test __str__ contains the upload date"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image)
        
        str_repr = str(image)
        self.assertIn(str(image.upload_date), str_repr)
    
    @patch('feed.models.Image.url')
    def test_get_optimized_url_with_cloudinary_url(self, mock_url):
        """Test get_optimized_url adds transformations to Cloudinary URLs"""
        # Mock a Cloudinary URL without transformations
        mock_url.__str__ = Mock(return_value='https://res.cloudinary.com/demo/image/upload/feed_images/test.jpg')
        mock_url.url = 'https://res.cloudinary.com/demo/image/upload/feed_images/test.jpg'
        
        image = Image()
        image.url = mock_url
        
        optimized_url = image.get_optimized_url()
        
        # Should add transformation parameters
        self.assertIn('c_fill', optimized_url)
        self.assertIn('f_auto', optimized_url)
        self.assertIn('q_auto', optimized_url)
        self.assertIn('w_800', optimized_url)
    
    @patch('feed.models.Image.url')
    def test_get_optimized_url_with_existing_transformations(self, mock_url):
        """Test get_optimized_url doesn't duplicate transformations"""
        # Mock a Cloudinary URL with existing transformations
        mock_url.__str__ = Mock(
            return_value='https://res.cloudinary.com/demo/image/upload/c_fill,w_500/feed_images/test.jpg'
        )
        mock_url.url = 'https://res.cloudinary.com/demo/image/upload/c_fill,w_500/feed_images/test.jpg'
        
        image = Image()
        image.url = mock_url
        
        optimized_url = image.get_optimized_url()
        
        # Should return original URL (already has transformations)
        self.assertIn('c_fill', optimized_url)
        # Should not add duplicate upload/ segments
        self.assertEqual(optimized_url.count('/upload/'), 1)
    
    @patch('feed.models.Image.url')
    def test_get_optimized_url_with_non_cloudinary_url(self, mock_url):
        """Test get_optimized_url returns original URL for non-Cloudinary URLs"""
        # Mock a non-Cloudinary URL
        mock_url.__str__ = Mock(return_value='https://example.com/images/test.jpg')
        mock_url.url = 'https://example.com/images/test.jpg'
        
        image = Image()
        image.url = mock_url
        
        optimized_url = image.get_optimized_url()
        
        # Should return original URL unchanged
        self.assertEqual(optimized_url, 'https://example.com/images/test.jpg')
    
    @patch('feed.models.Image.url')
    def test_get_optimized_url_with_empty_url(self, mock_url):
        """Test get_optimized_url handles empty URL gracefully"""
        mock_url.__str__ = Mock(return_value='')
        mock_url.url = ''
        
        image = Image()
        image.url = mock_url
        
        optimized_url = image.get_optimized_url()
        
        # Should return empty string without errors
        self.assertEqual(optimized_url, '')
    
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


class ImageModelQueryingTests(TestCase):
    """Test Image model querying and ordering"""
    
    def test_default_ordering_by_upload_date_desc(self):
        """Test images are ordered by upload_date descending by default"""
        # Create images with different upload dates
        older_time = django_timezone.now() - timedelta(days=2)
        middle_time = django_timezone.now() - timedelta(days=1)
        newer_time = django_timezone.now()
        
        test_image1 = self._create_test_image()
        test_image2 = self._create_test_image()
        test_image3 = self._create_test_image()
        
        # Create in random order
        image2 = Image.objects.create(url=test_image2, upload_date=middle_time)
        image1 = Image.objects.create(url=test_image1, upload_date=older_time)
        image3 = Image.objects.create(url=test_image3, upload_date=newer_time)
        
        # Query all images
        images = list(Image.objects.all())
        
        # Should be ordered newest first
        self.assertEqual(images[0].id, image3.id)
        self.assertEqual(images[1].id, image2.id)
        self.assertEqual(images[2].id, image1.id)
    
    def test_filter_by_active_status(self):
        """Test filtering images by active status"""
        test_image1 = self._create_test_image()
        test_image2 = self._create_test_image()
        test_image3 = self._create_test_image()
        
        active_image1 = Image.objects.create(url=test_image1, active=True)
        inactive_image = Image.objects.create(url=test_image2, active=False)
        active_image2 = Image.objects.create(url=test_image3, active=True)
        
        # Filter active images
        active_images = Image.objects.filter(active=True)
        self.assertEqual(active_images.count(), 2)
        self.assertIn(active_image1, active_images)
        self.assertIn(active_image2, active_images)
        self.assertNotIn(inactive_image, active_images)
    
    def test_filter_by_upload_date_range(self):
        """Test filtering images by upload date range"""
        now = django_timezone.now()
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)
        
        test_image1 = self._create_test_image()
        test_image2 = self._create_test_image()
        test_image3 = self._create_test_image()
        
        old_image = Image.objects.create(url=test_image1, upload_date=two_days_ago)
        middle_image = Image.objects.create(url=test_image2, upload_date=yesterday)
        new_image = Image.objects.create(url=test_image3, upload_date=now)
        
        # Filter images from yesterday onwards
        recent_images = Image.objects.filter(upload_date__gte=yesterday)
        self.assertEqual(recent_images.count(), 2)
        self.assertIn(middle_image, recent_images)
        self.assertIn(new_image, recent_images)
        self.assertNotIn(old_image, recent_images)
    
    def test_update_active_status(self):
        """Test updating active status of existing image"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image, active=True)
        
        # Update to inactive
        image.active = False
        image.save()
        
        # Verify change persisted
        image.refresh_from_db()
        self.assertFalse(image.active)
    
    def test_bulk_create_images(self):
        """Test bulk creation of multiple images"""
        test_image1 = self._create_test_image()
        test_image2 = self._create_test_image()
        test_image3 = self._create_test_image()
        
        images_to_create = [
            Image(url=test_image1),
            Image(url=test_image2),
            Image(url=test_image3),
        ]
        
        created_images = Image.objects.bulk_create(images_to_create)
        
        self.assertEqual(len(created_images), 3)
        # All should have IDs assigned
        for image in created_images:
            self.assertIsNotNone(image.id)
            self.assertIsInstance(image.id, uuid.UUID)
    
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


class ImageModelMetaTests(TestCase):
    """Test Image model Meta options"""
    
    def test_meta_ordering(self):
        """Test Meta ordering is set to ['-upload_date']"""
        self.assertEqual(Image._meta.ordering, ['-upload_date'])
    
    def test_verbose_name(self):
        """Test model has correct verbose name"""
        # If not explicitly set, should be 'image'
        self.assertEqual(Image._meta.verbose_name, 'image')
    
    def test_verbose_name_plural(self):
        """Test model has correct verbose name plural"""
        # If not explicitly set, should be 'images'
        self.assertEqual(Image._meta.verbose_name_plural, 'images')
    
    def test_app_label(self):
        """Test model belongs to 'feed' app"""
        self.assertEqual(Image._meta.app_label, 'feed')


class ImageModelEdgeCaseTests(TestCase):
    """Test Image model edge cases and error handling"""
    
    def test_image_creation_with_very_old_date(self):
        """Test creating image with very old upload date"""
        test_image = self._create_test_image()
        old_date = datetime(2000, 1, 1, tzinfo=timezone.utc)
        
        image = Image.objects.create(
            url=test_image,
            upload_date=old_date
        )
        
        self.assertEqual(image.upload_date, old_date)
    
    def test_image_creation_with_future_date(self):
        """Test creating image with future upload date"""
        test_image = self._create_test_image()
        future_date = django_timezone.now() + timedelta(days=365)
        
        image = Image.objects.create(
            url=test_image,
            upload_date=future_date
        )
        
        self.assertEqual(image.upload_date, future_date)
    
    def test_multiple_images_same_upload_time(self):
        """Test multiple images can have the same upload time"""
        test_image1 = self._create_test_image()
        test_image2 = self._create_test_image()
        
        same_time = django_timezone.now()
        image1 = Image.objects.create(url=test_image1, upload_date=same_time)
        image2 = Image.objects.create(url=test_image2, upload_date=same_time)
        
        self.assertEqual(image1.upload_date, image2.upload_date)
        # But they should still have different IDs
        self.assertNotEqual(image1.id, image2.id)
    
    def test_image_deletion(self):
        """Test deleting an image removes it from database"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image)
        image_id = image.id
        
        image.delete()
        
        # Should not exist anymore
        with self.assertRaises(Image.DoesNotExist):
            Image.objects.get(id=image_id)
    
    def test_image_update_preserves_id(self):
        """Test updating image doesn't change its ID"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image, active=True)
        original_id = image.id
        
        # Update multiple times
        image.active = False
        image.save()
        
        image.active = True
        image.save()
        
        self.assertEqual(image.id, original_id)
    
    def test_concurrent_image_creation(self):
        """Test multiple images can be created concurrently without ID collision"""
        test_images = [self._create_test_image() for _ in range(10)]
        
        images = [Image.objects.create(url=img) for img in test_images]
        
        # All should have unique IDs
        ids = [img.id for img in images]
        self.assertEqual(len(ids), len(set(ids)))  # No duplicates
    
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


class YouTubeCacheModelTests(TestCase):
    """Test YouTubeCache model (unmanaged dummy model)"""
    
    def test_youtube_cache_is_unmanaged(self):
        """Test YouTubeCache has managed=False in Meta"""
        self.assertFalse(YouTubeCache._meta.managed)
    
    def test_youtube_cache_verbose_name_plural(self):
        """Test YouTubeCache has correct verbose_name_plural"""
        self.assertEqual(
            YouTubeCache._meta.verbose_name_plural,
            'YouTube Cache'
        )
    
    def test_youtube_cache_app_label(self):
        """Test YouTubeCache belongs to 'feed' app"""
        self.assertEqual(YouTubeCache._meta.app_label, 'feed')
    
    def test_youtube_cache_no_database_table(self):
        """Test YouTubeCache doesn't create a database table"""
        # Since it's unmanaged, db_table should not be created
        # We verify this by checking the managed flag
        self.assertFalse(YouTubeCache._meta.managed)
    
    def test_youtube_cache_model_manager_exists(self):
        """Test YouTubeCache has a model manager (for admin compatibility)"""
        # Should have objects manager even though unmanaged
        self.assertTrue(hasattr(YouTubeCache, 'objects'))
    
    def test_youtube_cache_has_id_field(self):
        """Test YouTubeCache has default id field"""
        # Even though unmanaged, it should have the default id field
        id_field = YouTubeCache._meta.get_field('id')
        self.assertIsNotNone(id_field)
    
    def test_youtube_cache_model_exists_for_admin(self):
        """Test YouTubeCache exists as a model (for admin interface)"""
        # Verify the model class exists and can be referenced
        self.assertIsNotNone(YouTubeCache)
        self.assertTrue(hasattr(YouTubeCache, '_meta'))
    
    def test_youtube_cache_cannot_be_instantiated_in_db(self):
        """Test YouTubeCache instance cannot be saved to database"""
        # Create instance in memory (should work)
        cache = YouTubeCache()
        
        # But saving should fail since no table exists
        with self.assertRaises(Exception):
            cache.save()


class ImageModelProductionScenarioTests(TestCase):
    """Test Image model production scenarios and realistic use cases"""
    
    def test_deactivate_multiple_images_at_once(self):
        """Test bulk deactivating images (common admin operation)"""
        test_images = [self._create_test_image() for _ in range(5)]
        images = [Image.objects.create(url=img, active=True) for img in test_images]
        
        # Bulk update to inactive
        Image.objects.filter(id__in=[img.id for img in images]).update(active=False)
        
        # Verify all are inactive
        for image in images:
            image.refresh_from_db()
            self.assertFalse(image.active)
    
    def test_get_active_images_ordered(self):
        """Test common query: get all active images in order"""
        now = django_timezone.now()
        test_images = [self._create_test_image() for _ in range(3)]
        
        # Create with varying active status and dates
        active_new = Image.objects.create(
            url=test_images[0],
            upload_date=now,
            active=True
        )
        inactive_middle = Image.objects.create(
            url=test_images[1],
            upload_date=now - timedelta(days=1),
            active=False
        )
        active_old = Image.objects.create(
            url=test_images[2],
            upload_date=now - timedelta(days=2),
            active=True
        )
        
        # Query active images (should be ordered newest first)
        active_images = list(Image.objects.filter(active=True))
        
        self.assertEqual(len(active_images), 2)
        self.assertEqual(active_images[0].id, active_new.id)
        self.assertEqual(active_images[1].id, active_old.id)
    
    def test_archive_old_images(self):
        """Test archiving images older than certain date"""
        cutoff_date = django_timezone.now() - timedelta(days=30)
        
        test_images = [self._create_test_image() for _ in range(3)]
        
        old_image = Image.objects.create(
            url=test_images[0],
            upload_date=cutoff_date - timedelta(days=1),
            active=True
        )
        recent_image = Image.objects.create(
            url=test_images[1],
            upload_date=cutoff_date + timedelta(days=1),
            active=True
        )
        
        # Archive old images
        Image.objects.filter(
            upload_date__lt=cutoff_date,
            active=True
        ).update(active=False)
        
        old_image.refresh_from_db()
        recent_image.refresh_from_db()
        
        self.assertFalse(old_image.active)
        self.assertTrue(recent_image.active)
    
    def test_get_latest_n_images(self):
        """Test getting latest N images (common for feed display)"""
        test_images = [self._create_test_image() for _ in range(10)]
        created_images = [
            Image.objects.create(url=img) for img in test_images
        ]
        
        # Get latest 5
        latest_5 = list(Image.objects.all()[:5])
        
        self.assertEqual(len(latest_5), 5)
        # Should be in descending order (newest first)
        for i in range(len(latest_5) - 1):
            self.assertGreaterEqual(
                latest_5[i].upload_date,
                latest_5[i + 1].upload_date
            )
    
    def test_reactivate_archived_image(self):
        """Test reactivating a previously archived image"""
        test_image = self._create_test_image()
        image = Image.objects.create(url=test_image, active=False)
        
        # Reactivate
        image.active = True
        image.save()
        
        image.refresh_from_db()
        self.assertTrue(image.active)
    
    def test_image_count_by_status(self):
        """Test counting images by active status"""
        test_images = [self._create_test_image() for _ in range(7)]
        
        # Create 4 active, 3 inactive
        for i, img in enumerate(test_images):
            Image.objects.create(url=img, active=(i < 4))
        
        active_count = Image.objects.filter(active=True).count()
        inactive_count = Image.objects.filter(active=False).count()
        
        self.assertEqual(active_count, 4)
        self.assertEqual(inactive_count, 3)
    
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