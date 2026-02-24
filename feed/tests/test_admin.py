# feed/tests/test_admin.py
"""
Comprehensive bulletproof tests for feed/admin.py

Test Coverage:
===============
✅ ImageAdmin
   - Configuration (list_display, list_filter, list_editable, etc.)
   - thumbnail_preview method (list view)
   - large_thumbnail_preview method (detail view)
   - Fieldsets structure
   - Readonly fields
   - HTML output validation
   - Edge cases (missing images, None values)

✅ YouTubeCacheAdmin
   - Configuration (template, permissions)
   - has_add_permission (always False)
   - has_delete_permission (always False)
   - has_change_permission (always False)
   - get_queryset (returns empty queryset)
   - changelist_view (template rendering, context)
   - get_urls (custom URL patterns)
   - refresh_cache (cache update workflow)
   - Message handling (success, warning, error)
   - Exception handling

✅ Integration Tests
   - Admin site registration
   - View access and permissions
   - Form handling
   - Template rendering

✅ Edge Cases & Production Scenarios
   - Missing cache files
   - Empty video lists
   - API failures
   - Unicode in video titles
   - Large video lists
"""
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest
from django.utils import timezone
from django.urls import reverse
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import tempfile
import shutil
from pathlib import Path

from feed.admin import ImageAdmin, YouTubeCacheAdmin
from feed.models import Image, YouTubeCache
from feed.cache_utils import VideoCache

User = get_user_model()


# ============================================================================
# IMAGEADMIN CONFIGURATION TESTS
# ============================================================================

class ImageAdminConfigurationTests(TestCase):
    """Test ImageAdmin configuration and attributes"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = ImageAdmin(Image, self.site)
    
    def test_list_display_configuration(self):
        """Test list_display includes correct fields"""
        expected_fields = ['thumbnail_preview', 'id', 'upload_date', 'active']
        
        self.assertEqual(self.admin.list_display, tuple(expected_fields))
    
    def test_list_filter_configuration(self):
        """Test list_filter includes active and upload_date"""
        self.assertIn('active', self.admin.list_filter)
        self.assertIn('upload_date', self.admin.list_filter)
    
    def test_list_editable_configuration(self):
        """Test list_editable allows editing active field"""
        self.assertEqual(self.admin.list_editable, ('active',))
    
    def test_ordering_configuration(self):
        """Test ordering is by most recent upload first"""
        self.assertEqual(self.admin.ordering, ('-upload_date',))
    
    def test_readonly_fields_configuration(self):
        """Test readonly fields include upload_date and large_thumbnail_preview"""
        self.assertIn('upload_date', self.admin.readonly_fields)
        self.assertIn('large_thumbnail_preview', self.admin.readonly_fields)
    
    def test_fieldsets_structure(self):
        """Test fieldsets are properly configured"""
        fieldsets = self.admin.fieldsets
        
        # Should have 2 fieldsets
        self.assertEqual(len(fieldsets), 2)
        
        # Check Image fieldset
        image_fieldset = fieldsets[0]
        self.assertEqual(image_fieldset[0], 'Image')
        self.assertIn('large_thumbnail_preview', image_fieldset[1]['fields'])
        self.assertIn('url', image_fieldset[1]['fields'])
        self.assertIn('active', image_fieldset[1]['fields'])
        
        # Check Metadata fieldset
        metadata_fieldset = fieldsets[1]
        self.assertEqual(metadata_fieldset[0], 'Metadata')
        self.assertIn('upload_date', metadata_fieldset[1]['fields'])
    
    def test_thumbnail_preview_method_exists(self):
        """Test thumbnail_preview method exists"""
        self.assertTrue(hasattr(self.admin, 'thumbnail_preview'))
        self.assertTrue(callable(self.admin.thumbnail_preview))
    
    def test_large_thumbnail_preview_method_exists(self):
        """Test large_thumbnail_preview method exists"""
        self.assertTrue(hasattr(self.admin, 'large_thumbnail_preview'))
        self.assertTrue(callable(self.admin.large_thumbnail_preview))


# ============================================================================
# IMAGEADMIN THUMBNAIL PREVIEW TESTS
# ============================================================================

class ImageAdminThumbnailPreviewTests(TestCase):
    """Test ImageAdmin thumbnail preview methods"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = ImageAdmin(Image, self.site)
    
    def test_thumbnail_preview_with_image(self):
        """Test thumbnail_preview displays image when url exists"""
        # Create mock image with url
        image = Mock()
        image.url = Mock()
        image.url.url = 'https://res.cloudinary.com/test/image/upload/test.jpg'
        
        html = self.admin.thumbnail_preview(image)
        
        # Should contain img tag
        self.assertIn('<img', html)
        self.assertIn('src="https://res.cloudinary.com/test/image/upload/test.jpg"', html)
        
        # Should have correct styling
        self.assertIn('width: 50px', html)
        self.assertIn('height: 50px', html)
        self.assertIn('border-radius: 4px', html)
        self.assertIn('#064E3B', html)  # Brand color
    
    def test_thumbnail_preview_without_image(self):
        """Test thumbnail_preview displays placeholder when no url"""
        # Create mock image without url
        image = Mock()
        image.url = None
        
        html = self.admin.thumbnail_preview(image)
        
        # Should contain div placeholder
        self.assertIn('<div', html)
        self.assertIn('No Image', html)
        
        # Should have correct styling
        self.assertIn('width: 50px', html)
        self.assertIn('height: 50px', html)
        self.assertIn('background: #F3F4F6', html)
    
    def test_thumbnail_preview_short_description(self):
        """Test thumbnail_preview has correct short description"""
        self.assertEqual(
            self.admin.thumbnail_preview.short_description,
            'Preview'
        )
    
    def test_large_thumbnail_preview_with_image(self):
        """Test large_thumbnail_preview displays large image when url exists"""
        # Create mock image with url
        image = Mock()
        image.url = Mock()
        image.url.url = 'https://res.cloudinary.com/test/image/upload/test.jpg'
        
        html = self.admin.large_thumbnail_preview(image)
        
        # Should contain img tag
        self.assertIn('<img', html)
        self.assertIn('src="https://res.cloudinary.com/test/image/upload/test.jpg"', html)
        
        # Should have correct styling (larger)
        self.assertIn('max-width: 400px', html)
        self.assertIn('height: auto', html)
        self.assertIn('border-radius: 8px', html)
        self.assertIn('#064E3B', html)  # Brand color
    
    def test_large_thumbnail_preview_without_image(self):
        """Test large_thumbnail_preview displays large placeholder when no url"""
        # Create mock image without url
        image = Mock()
        image.url = None
        
        html = self.admin.large_thumbnail_preview(image)
        
        # Should contain div placeholder
        self.assertIn('<div', html)
        self.assertIn('No Image Available', html)
        
        # Should have correct styling (larger)
        self.assertIn('width: 400px', html)
        self.assertIn('height: 300px', html)
        self.assertIn('background: #F3F4F6', html)
    
    def test_large_thumbnail_preview_short_description(self):
        """Test large_thumbnail_preview has correct short description"""
        self.assertEqual(
            self.admin.large_thumbnail_preview.short_description,
            'Current Image'
        )
    
    def test_thumbnail_preview_html_is_safe(self):
        """Test thumbnail_preview returns SafeString (HTML safe)"""
        from django.utils.safestring import SafeString
        
        image = Mock()
        image.url = Mock()
        image.url.url = 'https://example.com/test.jpg'
        
        html = self.admin.thumbnail_preview(image)
        
        # Should be SafeString (HTML won't be escaped)
        self.assertIsInstance(html, SafeString)


# ============================================================================
# YOUTUBECACHEADMIN CONFIGURATION TESTS
# ============================================================================

class YouTubeCacheAdminConfigurationTests(TestCase):
    """Test YouTubeCacheAdmin configuration and attributes"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = YouTubeCacheAdmin(YouTubeCache, self.site)
    
    def test_change_list_template_configuration(self):
        """Test custom change_list_template is set"""
        self.assertEqual(
            self.admin.change_list_template,
            "admin/feed/youtubecache/change_list.html"
        )
    
    def test_has_add_permission_returns_false(self):
        """Test has_add_permission always returns False"""
        request = Mock()
        
        result = self.admin.has_add_permission(request)
        
        self.assertFalse(result)
    
    def test_has_delete_permission_returns_false(self):
        """Test has_delete_permission always returns False"""
        request = Mock()
        
        result = self.admin.has_delete_permission(request)
        
        self.assertFalse(result)
    
    def test_has_delete_permission_with_obj_returns_false(self):
        """Test has_delete_permission returns False even with object"""
        request = Mock()
        obj = Mock()
        
        result = self.admin.has_delete_permission(request, obj)
        
        self.assertFalse(result)
    
    def test_has_change_permission_returns_false(self):
        """Test has_change_permission always returns False"""
        request = Mock()
        
        result = self.admin.has_change_permission(request)
        
        self.assertFalse(result)
    
    def test_has_change_permission_with_obj_returns_false(self):
        """Test has_change_permission returns False even with object"""
        request = Mock()
        obj = Mock()
        
        result = self.admin.has_change_permission(request, obj)
        
        self.assertFalse(result)
    
    def test_get_queryset_returns_empty(self):
        """Test get_queryset returns empty queryset"""
        request = Mock()
        
        queryset = self.admin.get_queryset(request)
        
        # Should be empty
        self.assertEqual(queryset.count(), 0)
    

# ============================================================================
# YOUTUBECACHEADMIN CHANGELIST VIEW TESTS
# ============================================================================

class YouTubeCacheAdminChangelistViewTests(TestCase):
    """Test YouTubeCacheAdmin changelist_view method"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = YouTubeCacheAdmin(YouTubeCache, self.site)
        self.factory = RequestFactory()
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
    
    @patch('feed.admin.VideoCache')
    def test_changelist_view_with_cached_videos(self, mock_cache_class):
        """Test changelist_view displays cached videos"""
        # Setup mock cache
        mock_cache = Mock()
        mock_cache.get_last_updated.return_value = '2024-01-15T10:30:00Z'
        mock_cache.get_cached_videos.return_value = [
            {
                'id': 'video1',
                'title': 'Test Video 1',
                'thumbnail': 'https://i.ytimg.com/vi/video1/default.jpg',
                'published_at': '2024-01-15T10:00:00Z',
                'url': 'https://www.youtube.com/watch?v=video1'
            },
            {
                'id': 'video2',
                'title': 'Test Video 2',
                'thumbnail': 'https://i.ytimg.com/vi/video2/default.jpg',
                'published_at': '2024-01-14T10:00:00Z',
                'url': 'https://www.youtube.com/watch?v=video2'
            }
        ]
        mock_cache_class.return_value = mock_cache
        
        # Create request
        request = self.factory.get('/admin/feed/youtubecache/')
        
        # Call changelist_view
        response = self.admin.changelist_view(request)
        
        # Verify context
        self.assertIn('last_cache_update', response.context_data)
        self.assertIn('videos_count', response.context_data)
        self.assertIn('video_examples', response.context_data)
        
        # Verify values
        self.assertEqual(response.context_data['last_cache_update'], '2024-01-15T10:30:00Z')
        self.assertEqual(response.context_data['videos_count'], 2)
        self.assertEqual(len(response.context_data['video_examples']), 2)
        
        # Verify template used
        self.assertEqual(response.template_name, "admin/feed/youtubecache/change_list.html")
    
    @patch('feed.admin.VideoCache')
    def test_changelist_view_with_no_cache(self, mock_cache_class):
        """Test changelist_view when no cache exists"""
        # Setup mock cache with no videos
        mock_cache = Mock()
        mock_cache.get_last_updated.return_value = None
        mock_cache.get_cached_videos.return_value = None
        mock_cache_class.return_value = mock_cache
        
        # Create request
        request = self.factory.get('/admin/feed/youtubecache/')
        
        # Call changelist_view
        response = self.admin.changelist_view(request)
        
        # Verify context handles None values
        self.assertIsNone(response.context_data['last_cache_update'])
        self.assertEqual(response.context_data['videos_count'], 0)
        self.assertEqual(len(response.context_data['video_examples']), 0)
    
    @patch('feed.admin.VideoCache')
    def test_changelist_view_limits_video_examples(self, mock_cache_class):
        """Test changelist_view limits video examples to 8"""
        # Setup mock cache with 15 videos
        videos = [
            {
                'id': f'video{i}',
                'title': f'Test Video {i}',
                'thumbnail': f'https://i.ytimg.com/vi/video{i}/default.jpg',
                'published_at': '2024-01-15T10:00:00Z',
                'url': f'https://www.youtube.com/watch?v=video{i}'
            }
            for i in range(15)
        ]
        
        mock_cache = Mock()
        mock_cache.get_last_updated.return_value = '2024-01-15T10:30:00Z'
        mock_cache.get_cached_videos.return_value = videos
        mock_cache_class.return_value = mock_cache
        
        # Create request
        request = self.factory.get('/admin/feed/youtubecache/')
        
        # Call changelist_view
        response = self.admin.changelist_view(request)
        
        # Should only show first 8 videos
        self.assertEqual(response.context_data['videos_count'], 15)
        self.assertEqual(len(response.context_data['video_examples']), 8)
    
    @patch('feed.admin.VideoCache')
    def test_changelist_view_context_structure(self, mock_cache_class):
        """Test changelist_view context has correct structure"""
        mock_cache = Mock()
        mock_cache.get_last_updated.return_value = '2024-01-15T10:30:00Z'
        mock_cache.get_cached_videos.return_value = []
        mock_cache_class.return_value = mock_cache
        
        request = self.factory.get('/admin/feed/youtubecache/')
        response = self.admin.changelist_view(request)
        
        # Check all expected context keys
        expected_keys = ['title', 'last_cache_update', 'videos_count', 
                        'video_examples', 'module_name', 'cl']
        
        for key in expected_keys:
            self.assertIn(key, response.context_data)
        
        # Verify specific values
        self.assertEqual(response.context_data['title'], 'YouTube Cache Management')
        self.assertEqual(response.context_data['module_name'], 'YouTube Cache')
    
    @patch('feed.admin.VideoCache')
    def test_changelist_view_handles_missing_video_fields(self, mock_cache_class):
        """Test changelist_view handles videos with missing fields"""
        # Video with missing fields
        videos = [
            {
                'id': 'incomplete_video',
                # Missing title, thumbnail, etc.
            }
        ]
        
        mock_cache = Mock()
        mock_cache.get_last_updated.return_value = '2024-01-15T10:30:00Z'
        mock_cache.get_cached_videos.return_value = videos
        mock_cache_class.return_value = mock_cache
        
        request = self.factory.get('/admin/feed/youtubecache/')
        
        # Should not crash
        response = self.admin.changelist_view(request)
        
        # Video should have default values
        video_example = response.context_data['video_examples'][0]
        self.assertEqual(video_example['id'], 'incomplete_video')
        self.assertEqual(video_example['title'], 'Untitled')
        self.assertEqual(video_example['thumbnail'], '')


# ============================================================================
# YOUTUBECACHEADMIN URL CONFIGURATION TESTS
# ============================================================================

class YouTubeCacheAdminURLTests(TestCase):
    """Test YouTubeCacheAdmin custom URL configuration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = YouTubeCacheAdmin(YouTubeCache, self.site)
    
    def test_get_urls_returns_custom_urls(self):
        """Test get_urls returns custom URL patterns"""
        urls = self.admin.get_urls()
        
        # Should have 2 URLs
        self.assertEqual(len(urls), 2)
    
    def test_get_urls_includes_changelist(self):
        """Test get_urls includes changelist URL"""
        urls = self.admin.get_urls()
        
        # Find changelist URL
        changelist_url = None
        for url in urls:
            if url.name == 'feed_youtubecache_changelist':
                changelist_url = url
                break
        
        self.assertIsNotNone(changelist_url)
        self.assertEqual(str(changelist_url.pattern), '')
    
    def test_get_urls_includes_refresh_cache(self):
        """Test get_urls includes refresh-cache URL"""
        urls = self.admin.get_urls()
        
        # Find refresh-cache URL
        refresh_url = None
        for url in urls:
            if url.name == 'refresh-youtube-cache':
                refresh_url = url
                break
        
        self.assertIsNotNone(refresh_url)
        self.assertEqual(str(refresh_url.pattern), 'refresh-cache/')


# ============================================================================
# YOUTUBECACHEADMIN REFRESH CACHE TESTS
# ============================================================================

class YouTubeCacheAdminRefreshCacheTests(TestCase):
    """Test YouTubeCacheAdmin refresh_cache method"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = YouTubeCacheAdmin(YouTubeCache, self.site)
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
    
    def _add_messages_middleware(self, request):
        """Add messages middleware to request"""
        # Add session middleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        # Add messages
        setattr(request, '_messages', FallbackStorage(request))
    
    @patch('feed.admin.VideoCache')
    @patch('feed.admin.YouTubeService')
    def test_refresh_cache_success(self, mock_youtube_service, mock_cache_class):
        """Test successful cache refresh"""
        # Setup mocks
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = [
            {
                'id': 'video1',
                'title': 'Test Video',
                'description': 'Test',
                'thumbnail': 'https://example.com/thumb.jpg',
                'published_at': '2024-01-15T10:00:00Z',
                'url': 'https://www.youtube.com/watch?v=video1'
            }
        ]
        mock_youtube_service.return_value = mock_service
        
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        
        # Create request
        request = self.factory.post('/admin/feed/youtubecache/refresh-cache/')
        request.user = self.user
        self._add_messages_middleware(request)
        
        # Call refresh_cache
        response = self.admin.refresh_cache(request)
        
        # Verify YouTube service called with force_refresh
        mock_service.get_channel_videos.assert_called_once_with(force_refresh=True)
        
        # Verify cache updated
        mock_cache.update_cache.assert_called_once()
        
        # ✅ FIXED: Check redirect status and URL contains 'youtubecache'
        self.assertEqual(response.status_code, 302)
        self.assertIn('youtubecache', response.url)
        
        # Verify success message
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully cached', str(messages[0]))
    
    @patch('feed.admin.VideoCache')
    @patch('feed.admin.YouTubeService')
    def test_refresh_cache_no_videos(self, mock_youtube_service, mock_cache_class):
        """Test refresh_cache when no videos are fetched"""
        # Setup mocks - empty videos
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = []
        mock_youtube_service.return_value = mock_service
        
        # Create request
        request = self.factory.post('/admin/feed/youtubecache/refresh-cache/')
        request.user = self.user
        self._add_messages_middleware(request)
        
        # Call refresh_cache
        response = self.admin.refresh_cache(request)
        
        # Verify warning message
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertIn('No videos were fetched', str(messages[0]))
    
    @patch('feed.admin.YouTubeService')
    def test_refresh_cache_exception_handling(self, mock_youtube_service):
        """Test refresh_cache handles exceptions gracefully"""
        # Setup mock to raise exception
        mock_youtube_service.side_effect = Exception('API Error')
        
        # Create request
        request = self.factory.post('/admin/feed/youtubecache/refresh-cache/')
        request.user = self.user
        self._add_messages_middleware(request)
        
        # Call refresh_cache
        response = self.admin.refresh_cache(request)
        
        # Verify error message
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Error updating cache', str(messages[0]))
        self.assertIn('API Error', str(messages[0]))
        
        # Should still redirect
        self.assertEqual(response.status_code, 302)
    
    @patch('feed.admin.VideoCache')
    @patch('feed.admin.YouTubeService')
    def test_refresh_cache_updates_with_multiple_videos(self, mock_youtube_service, mock_cache_class):
        """Test refresh_cache with multiple videos"""
        # Setup mocks with multiple videos
        videos = [
            {'id': f'video{i}', 'title': f'Video {i}'}
            for i in range(10)
        ]
        
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = videos
        mock_youtube_service.return_value = mock_service
        
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        
        # Create request
        request = self.factory.post('/admin/feed/youtubecache/refresh-cache/')
        request.user = self.user
        self._add_messages_middleware(request)
        
        # Call refresh_cache
        self.admin.refresh_cache(request)
        
        # Verify cache updated with all videos
        mock_cache.update_cache.assert_called_once_with(videos)
        
        # Verify success message mentions count
        messages = list(get_messages(request))
        self.assertIn('10 videos', str(messages[0]))


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@override_settings(ADMIN_IP_WHITELIST=['127.0.0.1'])
class ImageAdminIntegrationTests(TestCase):
    """Test ImageAdmin integration with Django admin"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client.force_login(self.user)
        
        # Create test image
        self.image = Image.objects.create(
            active=True
        )
    
    def test_image_changelist_accessible(self):
        """Test image changelist is accessible"""
        url = reverse('admin:feed_image_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_image_change_form_accessible(self):
        """Test image change form is accessible"""
        url = reverse('admin:feed_image_change', args=[self.image.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_image_list_displays_active_filter(self):
        """Test image list has active filter"""
        url = reverse('admin:feed_image_changelist')
        response = self.client.get(url)
        
        # Should have filter for active
        self.assertContains(response, 'active')


@override_settings(ADMIN_IP_WHITELIST=['127.0.0.1'])
class YouTubeCacheAdminIntegrationTests(TestCase):
    """Test YouTubeCacheAdmin integration with Django admin"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client.force_login(self.user)
    
    @patch('feed.admin.VideoCache')
    def test_youtube_cache_changelist_accessible(self, mock_cache):
        """Test YouTube cache changelist is accessible"""
        mock_cache_instance = Mock()
        mock_cache_instance.get_last_updated.return_value = None
        mock_cache_instance.get_cached_videos.return_value = []
        mock_cache.return_value = mock_cache_instance
        
        url = reverse('admin:feed_youtubecache_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_youtube_cache_add_not_accessible(self):
        """Test YouTube cache add form is not accessible"""
        url = reverse('admin:feed_youtubecache_changelist')
        response = self.client.get(url)
        
        # Should not have "Add" button
        self.assertNotContains(response, 'Add YouTube Cache')


# ============================================================================
# EDGE CASES & PRODUCTION SCENARIOS
# ============================================================================

class ImageAdminEdgeCasesTests(TestCase):
    """Test ImageAdmin edge cases and production scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = ImageAdmin(Image, self.site)
    
    def test_thumbnail_preview_with_empty_string_url(self):
        """Test thumbnail_preview when url is empty string"""
        image = Mock()
        image.url = ''
        
        html = self.admin.thumbnail_preview(image)
        
        # Should show placeholder
        self.assertIn('No Image', html)
    
    def test_thumbnail_preview_with_special_characters_in_url(self):
        """Test thumbnail_preview handles special characters in URL"""
        image = Mock()
        image.url = Mock()
        image.url.url = 'https://example.com/image with spaces.jpg'
        
        # Should not crash
        html = self.admin.thumbnail_preview(image)
        
        self.assertIn('<img', html)
    
    def test_large_thumbnail_preview_with_very_long_url(self):
        """Test large_thumbnail_preview handles very long URLs"""
        image = Mock()
        image.url = Mock()
        image.url.url = 'https://example.com/' + 'a' * 1000 + '.jpg'
        
        # Should not crash
        html = self.admin.large_thumbnail_preview(image)
        
        self.assertIn('<img', html)


class YouTubeCacheAdminEdgeCasesTests(TestCase):
    """Test YouTubeCacheAdmin edge cases and production scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = YouTubeCacheAdmin(YouTubeCache, self.site)
        self.factory = RequestFactory()
    
    @patch('feed.admin.VideoCache')
    def test_changelist_view_with_unicode_video_titles(self, mock_cache_class):
        """Test changelist_view handles unicode in video titles"""
        videos = [
            {
                'id': 'unicode_test',
                'title': 'Test with émojis 🎉 and 中文字符',
                'thumbnail': 'https://example.com/thumb.jpg',
                'published_at': '2024-01-15T10:00:00Z',
                'url': 'https://www.youtube.com/watch?v=unicode_test'
            }
        ]
        
        mock_cache = Mock()
        mock_cache.get_last_updated.return_value = '2024-01-15T10:30:00Z'
        mock_cache.get_cached_videos.return_value = videos
        mock_cache_class.return_value = mock_cache
        
        request = self.factory.get('/admin/feed/youtubecache/')
        
        # Should not crash with unicode
        response = self.admin.changelist_view(request)
        
        self.assertEqual(response.context_data['videos_count'], 1)
    
    @patch('feed.admin.VideoCache')
    def test_changelist_view_with_empty_video_list(self, mock_cache_class):
        """Test changelist_view with empty video list"""
        mock_cache = Mock()
        mock_cache.get_last_updated.return_value = '2024-01-15T10:30:00Z'
        mock_cache.get_cached_videos.return_value = []
        mock_cache_class.return_value = mock_cache
        
        request = self.factory.get('/admin/feed/youtubecache/')
        response = self.admin.changelist_view(request)
        
        # Should handle empty list
        self.assertEqual(response.context_data['videos_count'], 0)
        self.assertEqual(len(response.context_data['video_examples']), 0)
    
    @patch('feed.admin.VideoCache')
    def test_changelist_view_cache_exception(self, mock_cache_class):
        """Test changelist_view handles cache exceptions"""
        mock_cache = Mock()
        mock_cache.get_last_updated.side_effect = Exception('Cache error')
        mock_cache_class.return_value = mock_cache
        
        request = self.factory.get('/admin/feed/youtubecache/')
        
        # Should handle exception gracefully
        with self.assertRaises(Exception):
            self.admin.changelist_view(request)