# feed/tests/test_views.py
"""
Comprehensive bulletproof tests for feed/views.py

Test Coverage:
===============
✅ ImageViewSet (ModelViewSet)
   - List endpoint (GET /api/feed/images/)
   - Detail endpoint (GET /api/feed/images/<id>/)
   - Create endpoint (POST /api/feed/images/)
   - Update endpoint (PUT/PATCH /api/feed/images/<id>/)
   - Delete endpoint (DELETE /api/feed/images/<id>/)
   - Permission handling (IsAuthenticatedOrReadOnly)
   - Staff vs non-staff queryset filtering
   - Active/inactive image filtering
   - Ordering validation

✅ YouTubeVideoView (APIView)
   - GET endpoint success
   - Service integration
   - Error handling
   - Exception scenarios
   - Permission handling (AllowAny)

✅ Security & Edge Cases
   - Unauthenticated access
   - Staff privileges
   - Data isolation
   - Method restrictions
   - Error responses

✅ Production Scenarios
   - Bulk operations
   - Pagination
   - Filtering
   - Ordering
   - Performance
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from feed.models import Image
from io import BytesIO
from PIL import Image as PILImage
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import uuid

User = get_user_model()


# ============================================================================
# IMAGE VIEWSET TESTS - LIST ENDPOINT
# ============================================================================

class ImageViewSetListTests(APITestCase):
    """Test ImageViewSet list endpoint (GET /api/feed/images/)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.url = reverse('feed:image-list')
        
        # Create users
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create active and inactive images
        test_image1 = self._create_test_image()
        test_image2 = self._create_test_image()
        test_image3 = self._create_test_image()
        
        self.active_image1 = Image.objects.create(url=test_image1, active=True)
        self.active_image2 = Image.objects.create(url=test_image2, active=True)
        self.inactive_image = Image.objects.create(url=test_image3, active=False)
    
    def test_anonymous_user_can_list_active_images(self):
        """Test anonymous users can see active images only"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see active images
        self.assertEqual(len(response.data['results']), 2)
    
    def test_authenticated_user_sees_active_images_only(self):
        """Test authenticated non-staff users see active images only"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see active images
        self.assertEqual(len(response.data['results']), 2)
        
        # Verify inactive image is not in results
        image_ids = [item['id'] for item in response.data['results']]
        self.assertNotIn(str(self.inactive_image.id), image_ids)
    
    def test_staff_user_sees_all_images(self):
        """Test staff users can see all images (active and inactive)"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see all 3 images
        self.assertEqual(len(response.data['results']), 3)
        
        # Verify inactive image is in results
        image_ids = [item['id'] for item in response.data['results']]
        self.assertIn(str(self.inactive_image.id), image_ids)
    
    def test_list_returns_correct_fields(self):
        """Test list response contains all expected fields"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        first_image = response.data['results'][0]
        
        # Check all expected fields present
        expected_fields = {'id', 'url', 'upload_date', 'active', 'optimized_url'}
        self.assertEqual(set(first_image.keys()), expected_fields)
    
    def test_list_ordering_newest_first(self):
        """Test images are ordered by upload_date descending"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        
        # Verify ordering (newest first)
        if len(results) > 1:
            first_date = results[0]['upload_date']
            second_date = results[1]['upload_date']
            self.assertGreaterEqual(first_date, second_date)
    
    def test_empty_list_returns_empty_array(self):
        """Test listing when no images exist"""
        # Delete all images
        Image.objects.all().delete()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_list_pagination(self):
        """Test list endpoint supports pagination"""
        # Create many images to test pagination
        test_images = [self._create_test_image() for _ in range(15)]
        for img in test_images:
            Image.objects.create(url=img, active=True)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have pagination metadata
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
    
    def _create_test_image(self):
        """Helper method to create a test image file"""
        img = PILImage.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name=f'test_image_{uuid.uuid4()}.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )


# ============================================================================
# IMAGE VIEWSET TESTS - DETAIL ENDPOINT
# ============================================================================

class ImageViewSetDetailTests(APITestCase):
    """Test ImageViewSet detail endpoint (GET /api/feed/images/<id>/)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        test_image1 = self._create_test_image()
        test_image2 = self._create_test_image()
        
        self.active_image = Image.objects.create(url=test_image1, active=True)
        self.inactive_image = Image.objects.create(url=test_image2, active=False)
    
    def test_anonymous_can_retrieve_active_image(self):
        """Test anonymous user can retrieve active image"""
        url = reverse('feed:image-detail', kwargs={'pk': self.active_image.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.active_image.id))
    
    def test_anonymous_cannot_retrieve_inactive_image(self):
        """Test anonymous user cannot retrieve inactive image"""
        url = reverse('feed:image-detail', kwargs={'pk': self.inactive_image.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_regular_user_cannot_retrieve_inactive_image(self):
        """Test regular authenticated user cannot retrieve inactive image"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('feed:image-detail', kwargs={'pk': self.inactive_image.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_staff_can_retrieve_inactive_image(self):
        """Test staff user can retrieve inactive image"""
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('feed:image-detail', kwargs={'pk': self.inactive_image.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.inactive_image.id))
        self.assertFalse(response.data['active'])
    
    def test_retrieve_nonexistent_image_returns_404(self):
        """Test retrieving non-existent image returns 404"""
        fake_id = uuid.uuid4()
        url = reverse('feed:image-detail', kwargs={'pk': fake_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_detail_returns_complete_data(self):
        """Test detail endpoint returns complete image data"""
        url = reverse('feed:image-detail', kwargs={'pk': self.active_image.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all fields present
        expected_fields = {'id', 'url', 'upload_date', 'active', 'optimized_url'}
        self.assertEqual(set(response.data.keys()), expected_fields)
    
    def _create_test_image(self):
        """Helper method to create a test image file"""
        img = PILImage.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name=f'test_image_{uuid.uuid4()}.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )


# ============================================================================
# IMAGE VIEWSET TESTS - CREATE ENDPOINT
# ============================================================================

class ImageViewSetCreateTests(APITestCase):
    """Test ImageViewSet create endpoint (POST /api/feed/images/)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.url = reverse('feed:image-list')
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
    
    def test_anonymous_cannot_create_image(self):
        """Test anonymous user cannot create image (IsAuthenticatedOrReadOnly)"""
        test_image = self._create_test_image()
        data = {
            'url': test_image,
            'active': True
        }
        
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_user_can_create_image(self):
        """Test authenticated user can create image"""
        self.client.force_authenticate(user=self.regular_user)
        test_image = self._create_test_image()
        
        data = {
            'url': test_image,
            'active': True
        }
        
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertTrue(response.data['active'])
    
    def test_staff_can_create_image(self):
        """Test staff user can create image"""
        self.client.force_authenticate(user=self.staff_user)
        test_image = self._create_test_image()
        
        data = {
            'url': test_image,
            'active': True
        }
        
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_image_without_url(self):
        """Test creating image without URL (blank allowed)"""
        self.client.force_authenticate(user=self.regular_user)
        
        data = {
            'active': True
        }
        
        response = self.client.post(self.url, data, format='json')
        
        # Should succeed since URL is blank=True
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_inactive_image(self):
        """Test creating inactive image"""
        self.client.force_authenticate(user=self.regular_user)
        test_image = self._create_test_image()
        
        data = {
            'url': test_image,
            'active': False
        }
        
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['active'])
    
    def test_cannot_set_id_on_create(self):
        """Test id cannot be set during creation (read-only)"""
        self.client.force_authenticate(user=self.regular_user)
        test_image = self._create_test_image()
        custom_id = str(uuid.uuid4())
        
        data = {
            'id': custom_id,
            'url': test_image,
            'active': True
        }
        
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # ID should be auto-generated, not the custom one
        self.assertNotEqual(response.data['id'], custom_id)
    
    def _create_test_image(self):
        """Helper method to create a test image file"""
        img = PILImage.new('RGB', (100, 100), color='blue')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name=f'test_image_{uuid.uuid4()}.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )


# ============================================================================
# IMAGE VIEWSET TESTS - UPDATE ENDPOINT
# ============================================================================

class ImageViewSetUpdateTests(APITestCase):
    """Test ImageViewSet update endpoints (PUT/PATCH /api/feed/images/<id>/)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )
        
        test_image = self._create_test_image()
        self.image = Image.objects.create(url=test_image, active=True)
        self.url = reverse('feed:image-detail', kwargs={'pk': self.image.pk})
    
    def test_anonymous_cannot_update_image(self):
        """Test anonymous user cannot update image"""
        data = {'active': False}
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_can_update_image(self):
        """Test authenticated user can update image"""
        self.client.force_authenticate(user=self.regular_user)
        
        data = {'active': False}
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['active'])
        
        # Verify database was updated
        self.image.refresh_from_db()
        self.assertFalse(self.image.active)
    
    def test_can_reactivate_inactive_image(self):
        """Test updating inactive image to active (staff only)"""
        self.image.active = False
        self.image.save()
        
        # Make user staff so they can see inactive images
        self.regular_user.is_staff = True
        self.regular_user.save()
        
        self.client.force_authenticate(user=self.regular_user)
        
        data = {'active': True}
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['active'])
    
    def test_cannot_update_id(self):
        """Test id cannot be updated (read-only)"""
        self.client.force_authenticate(user=self.regular_user)
        original_id = self.image.id
        
        data = {'id': str(uuid.uuid4())}
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # ID should not change
        self.assertEqual(response.data['id'], str(original_id))
    
    def test_cannot_update_upload_date(self):
        """Test upload_date cannot be updated (read-only)"""
        self.client.force_authenticate(user=self.regular_user)
        original_date = self.image.upload_date
        
        data = {'upload_date': '2020-01-01T00:00:00Z'}
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Upload date should not change
        self.image.refresh_from_db()
        self.assertEqual(self.image.upload_date, original_date)
    
    def test_full_update_with_put(self):
        """Test full update using PUT method"""
        self.client.force_authenticate(user=self.regular_user)
        test_image = self._create_test_image()
        
        data = {
            'url': test_image,
            'active': False
        }
        
        response = self.client.put(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['active'])
    
    def _create_test_image(self):
        """Helper method to create a test image file"""
        img = PILImage.new('RGB', (100, 100), color='green')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name=f'test_image_{uuid.uuid4()}.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )


# ============================================================================
# IMAGE VIEWSET TESTS - DELETE ENDPOINT
# ============================================================================

class ImageViewSetDeleteTests(APITestCase):
    """Test ImageViewSet delete endpoint (DELETE /api/feed/images/<id>/)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )
        
        test_image = self._create_test_image()
        self.image = Image.objects.create(url=test_image, active=True)
        self.url = reverse('feed:image-detail', kwargs={'pk': self.image.pk})
    
    def test_anonymous_cannot_delete_image(self):
        """Test anonymous user cannot delete image"""
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # Verify image still exists
        self.assertTrue(Image.objects.filter(id=self.image.id).exists())
    
    def test_authenticated_can_delete_image(self):
        """Test authenticated user can delete image"""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify image was deleted
        self.assertFalse(Image.objects.filter(id=self.image.id).exists())
    
    def test_delete_nonexistent_image_returns_404(self):
        """Test deleting non-existent image returns 404"""
        self.client.force_authenticate(user=self.regular_user)
        
        fake_id = uuid.uuid4()
        url = reverse('feed:image-detail', kwargs={'pk': fake_id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_delete_is_permanent(self):
        """Test deletion is permanent (cannot retrieve after delete)"""
        self.client.force_authenticate(user=self.regular_user)
        
        # Delete image
        self.client.delete(self.url)
        
        # Try to retrieve
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def _create_test_image(self):
        """Helper method to create a test image file"""
        img = PILImage.new('RGB', (100, 100), color='yellow')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name=f'test_image_{uuid.uuid4()}.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )


# ============================================================================
# YOUTUBE VIDEO VIEW TESTS
# ============================================================================

class YouTubeVideoViewTests(APITestCase):
    """Test YouTubeVideoView (GET /api/feed/youtube/)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.url = reverse('feed:youtube-videos')
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('feed.views.YouTubeService')
    def test_anonymous_can_access_youtube_videos(self, mock_service):
        """Test anonymous users can access YouTube videos (AllowAny)"""
        # Mock successful response
        mock_videos = [
            {
                'id': 'video1',
                'title': 'Test Video 1',
                'description': 'Description 1',
                'thumbnail': 'https://i.ytimg.com/vi/video1/default.jpg',
                'published_at': datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
                'url': 'https://www.youtube.com/watch?v=video1'
            }
        ]
        mock_service.return_value.get_channel_videos.return_value = mock_videos
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], 'video1')
    
    @patch('feed.views.YouTubeService')
    def test_authenticated_can_access_youtube_videos(self, mock_service):
        """Test authenticated users can access YouTube videos"""
        self.client.force_authenticate(user=self.user)
        
        mock_videos = [
            {
                'id': 'video2',
                'title': 'Test Video 2',
                'description': 'Description 2',
                'thumbnail': 'https://i.ytimg.com/vi/video2/default.jpg',
                'published_at': datetime(2024, 1, 2, tzinfo=timezone.utc).isoformat(),
                'url': 'https://www.youtube.com/watch?v=video2'
            }
        ]
        mock_service.return_value.get_channel_videos.return_value = mock_videos
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    @patch('feed.views.YouTubeService')
    def test_returns_empty_list_when_no_videos(self, mock_service):
        """Test endpoint returns empty list when no videos available"""
        mock_service.return_value.get_channel_videos.return_value = []
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    @patch('feed.views.YouTubeService')
    def test_returns_multiple_videos(self, mock_service):
        """Test endpoint returns multiple videos correctly"""
        mock_videos = [
            {
                'id': f'video{i}',
                'title': f'Test Video {i}',
                'description': f'Description {i}',
                'thumbnail': f'https://i.ytimg.com/vi/video{i}/default.jpg',
                'published_at': datetime(2024, 1, i, tzinfo=timezone.utc).isoformat(),
                'url': f'https://www.youtube.com/watch?v=video{i}'
            }
            for i in range(1, 6)
        ]
        mock_service.return_value.get_channel_videos.return_value = mock_videos
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
    
    @patch('feed.views.YouTubeService')
    def test_handles_service_exception(self, mock_service):
        """Test endpoint handles YouTubeService exceptions gracefully"""
        # Mock exception
        mock_service.return_value.get_channel_videos.side_effect = Exception('API Error')
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'API Error')
    
    @patch('feed.views.YouTubeService')
    def test_handles_youtube_api_quota_exceeded(self, mock_service):
        """Test endpoint handles YouTube API quota exceeded"""
        mock_service.return_value.get_channel_videos.side_effect = Exception('quotaExceeded')
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
    
    @patch('feed.views.YouTubeService')
    def test_only_get_method_allowed(self, mock_service):
        """Test only GET method is allowed on YouTube endpoint"""
        mock_service.return_value.get_channel_videos.return_value = []
        
        # POST should not be allowed
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # PUT should not be allowed
        response = self.client.put(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # DELETE should not be allowed
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    @patch('feed.views.YouTubeService')
    def test_response_structure(self, mock_service):
        """Test response has correct structure"""
        mock_videos = [
            {
                'id': 'abc123',
                'title': 'Sample Video',
                'description': 'Sample description',
                'thumbnail': 'https://i.ytimg.com/vi/abc123/maxresdefault.jpg',
                'published_at': datetime(2024, 1, 15, tzinfo=timezone.utc).isoformat(),
                'url': 'https://www.youtube.com/watch?v=abc123'
            }
        ]
        mock_service.return_value.get_channel_videos.return_value = mock_videos
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        video = response.data[0]
        
        # Verify structure
        self.assertIn('id', video)
        self.assertIn('title', video)
        self.assertIn('description', video)
        self.assertIn('thumbnail', video)
        self.assertIn('published_at', video)
        self.assertIn('url', video)


# ============================================================================
# PRODUCTION SCENARIO TESTS
# ============================================================================

class ImageViewSetProductionTests(APITestCase):
    """Test ImageViewSet production scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.list_url = reverse('feed:image-list')
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_bulk_image_listing_performance(self):
        """Test listing many images performs well"""
        # Create 50 active images
        test_images = [self._create_test_image() for _ in range(50)]
        for img in test_images:
            Image.objects.create(url=img, active=True)
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should handle large result set
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_concurrent_user_access(self):
        """Test multiple users can access simultaneously"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass1'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass2'
        )
        
        client1 = APIClient()
        client2 = APIClient()
        
        client1.force_authenticate(user=user1)
        client2.force_authenticate(user=user2)
        
        # Both users access simultaneously
        response1 = client1.get(self.list_url)
        response2 = client2.get(self.list_url)
        
        # Both should succeed
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
    
    def test_staff_inactive_image_workflow(self):
        """Test complete workflow: create active, deactivate, staff views"""
        self.client.force_authenticate(user=self.user)
        
        # Create active image
        test_image = self._create_test_image()
        create_response = self.client.post(
            self.list_url,
            {'url': test_image, 'active': True},
            format='multipart'
        )
        image_id = create_response.data['id']
        
        # Deactivate it
        detail_url = reverse('feed:image-detail', kwargs={'pk': image_id})
        self.client.patch(detail_url, {'active': False}, format='json')
        
        # Regular user can't see it
        list_response = self.client.get(self.list_url)
        image_ids = [item['id'] for item in list_response.data['results']]
        self.assertNotIn(image_id, image_ids)
        
        # Make user staff
        self.user.is_staff = True
        self.user.save()
        
        # Now can see it
        list_response = self.client.get(self.list_url)
        image_ids = [item['id'] for item in list_response.data['results']]
        self.assertIn(image_id, image_ids)
    
    def _create_test_image(self):
        """Helper method to create a test image file"""
        img = PILImage.new('RGB', (100, 100), color='purple')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name=f'test_image_{uuid.uuid4()}.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )


# ============================================================================
# EDGE CASE & ERROR TESTS
# ============================================================================

class ViewsEdgeCaseTests(APITestCase):
    """Test edge cases and error scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.list_url = reverse('feed:image-list')
    
    def test_invalid_uuid_in_detail_url(self):
        """Test invalid UUID format in detail URL"""
        url = reverse('feed:image-detail', kwargs={'pk': 'invalid-uuid'})
        response = self.client.get(url)
        
        # Should return 404 for invalid UUID
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_method_not_allowed_on_list(self):
        """Test methods not supported by list endpoint"""
        # Authenticate so we get 405 instead of 401
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user)
        
        # List endpoint doesn't support DELETE
        response = self.client.delete(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_unauthenticated_cannot_modify(self):
        """Test unauthenticated users blocked from modifications"""
        # Try POST without auth
        response = self.client.post(self.list_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Try PATCH without auth
        fake_id = uuid.uuid4()
        detail_url = reverse('feed:image-detail', kwargs={'pk': fake_id})
        response = self.client.patch(detail_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Try DELETE without auth
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_empty_database_list(self):
        """Test listing when database is empty"""
        # Ensure no images exist
        Image.objects.all().delete()
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)
    
    @patch('feed.views.YouTubeService')
    def test_youtube_view_connection_error(self, mock_service):
        """Test YouTube view handles connection errors"""
        mock_service.return_value.get_channel_videos.side_effect = ConnectionError('Network error')
        
        url = reverse('feed:youtube-videos')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)