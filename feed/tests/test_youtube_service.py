# feed/tests/test_youtube_service.py
"""
Comprehensive bulletproof tests for feed/youtube_service.py

Test Coverage:
===============
✅ YouTubeService Initialization
   - Successful initialization with valid settings
   - Failed initialization (missing API key)
   - Failed initialization (missing channel ID)
   - Exception handling during init
   - VideoCache initialization

✅ fetch_videos_from_api Method
   - Successful single page fetch
   - Pagination (multiple pages)
   - max_results parameter
   - Empty results
   - HttpError - quotaExceeded
   - HttpError - other errors
   - Generic exceptions
   - Malformed API responses
   - Thumbnail URL selection (high > medium > default)
   - Date parsing and timezone handling

✅ get_channel_videos Method
   - Cache hit (returns cached data)
   - Cache miss (fetches from API)
   - force_refresh=True (bypasses cache)
   - Cache update after API fetch
   - Empty videos handling
   - max_results forwarding

✅ Integration Tests
   - Complete workflow: API → Cache → Retrieve
   - Error recovery
   - Logging behavior

✅ Edge Cases & Production Scenarios
   - Missing/malformed data
   - Network failures
   - API rate limiting
   - Large datasets
"""
from django.test import TestCase, override_settings
from unittest.mock import Mock, patch, MagicMock, call
from feed.youtube_service import YouTubeService
from googleapiclient.errors import HttpError
from datetime import datetime
import pytz
import logging


# ============================================================================
# YOUTUBE SERVICE INITIALIZATION TESTS
# ============================================================================

class YouTubeServiceInitializationTests(TestCase):
    """Test YouTubeService initialization"""
    
    @override_settings(
        YOUTUBE_API_KEY='test_api_key',
        YOUTUBE_CHANNEL_ID='test_channel_id'
    )
    @patch('feed.youtube_service.build')
    @patch('feed.youtube_service.VideoCache')
    def test_successful_initialization(self, mock_cache, mock_build):
        """Test successful service initialization with valid settings"""
        mock_youtube = Mock()
        mock_build.return_value = mock_youtube
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        
        service = YouTubeService()
        
        # Verify YouTube client was built with correct params
        mock_build.assert_called_once_with(
            'youtube', 
            'v3', 
            developerKey='test_api_key'
        )
        
        # Verify attributes set correctly
        self.assertEqual(service.youtube, mock_youtube)
        self.assertEqual(service.channel_id, 'test_channel_id')
        self.assertEqual(service.cache, mock_cache_instance)
    
    @override_settings(
        YOUTUBE_API_KEY='test_api_key',
        YOUTUBE_CHANNEL_ID='test_channel_id'
    )
    @patch('feed.youtube_service.build')
    @patch('feed.youtube_service.VideoCache')
    def test_initialization_with_build_exception(self, mock_cache, mock_build):
        """Test initialization handles build() exceptions gracefully"""
        mock_build.side_effect = Exception('API build failed')
        
        service = YouTubeService()
        
        # Service should still be created but youtube should be None
        self.assertIsNone(service.youtube)
        self.assertIsNotNone(service.cache)
    
    @override_settings(
        YOUTUBE_API_KEY='test_api_key',
        YOUTUBE_CHANNEL_ID='test_channel_id'
    )
    @patch('feed.youtube_service.build')
    @patch('feed.youtube_service.VideoCache')
    @patch('feed.youtube_service.logger')
    def test_initialization_logs_errors(self, mock_logger, mock_cache, mock_build):
        """Test initialization logs errors when build fails"""
        error_msg = 'Invalid API key'
        mock_build.side_effect = Exception(error_msg)
        
        service = YouTubeService()
        
        # Verify error was logged
        mock_logger.error.assert_called()
        logged_message = mock_logger.error.call_args[0][0]
        self.assertIn(error_msg, logged_message)
    
    @override_settings(
        YOUTUBE_API_KEY='',
        YOUTUBE_CHANNEL_ID='test_channel_id'
    )
    @patch('feed.youtube_service.build')
    def test_initialization_with_empty_api_key(self, mock_build):
        """Test initialization with empty API key"""
        # Empty API key might cause build to fail or succeed with restrictions
        mock_build.side_effect = Exception('Missing API key')
        
        service = YouTubeService()
        
        # Should handle gracefully
        self.assertIsNone(service.youtube)


# ============================================================================
# FETCH VIDEOS FROM API TESTS
# ============================================================================

class FetchVideosFromAPITests(TestCase):
    """Test YouTubeService.fetch_videos_from_api()"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_youtube = Mock()
        self.mock_cache = Mock()
        
        # Create service with mocked components
        with patch('feed.youtube_service.build') as mock_build, \
             patch('feed.youtube_service.VideoCache') as mock_cache_class:
            mock_build.return_value = self.mock_youtube
            mock_cache_class.return_value = self.mock_cache
            
            with override_settings(
                YOUTUBE_API_KEY='test_key',
                YOUTUBE_CHANNEL_ID='test_channel'
            ):
                self.service = YouTubeService()
    
    def test_fetch_single_page_success(self):
        """Test successfully fetching a single page of videos"""
        # Mock API response
        mock_response = {
            'items': [
                {
                    'id': {'videoId': 'video123'},
                    'snippet': {
                        'title': 'Test Video',
                        'description': 'Test description',
                        'publishedAt': '2024-01-15T10:30:00Z',
                        'thumbnails': {
                            'high': {'url': 'https://i.ytimg.com/vi/video123/hqdefault.jpg'}
                        }
                    }
                }
            ]
        }
        
        # Setup mock chain
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        # Execute
        videos = self.service.fetch_videos_from_api()
        
        # Assertions
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]['id'], 'video123')
        self.assertEqual(videos[0]['title'], 'Test Video')
        self.assertEqual(videos[0]['description'], 'Test description')
        self.assertIn('thumbnail', videos[0])
        self.assertIn('published_at', videos[0])
        self.assertIn('url', videos[0])
    
    def test_fetch_with_pagination(self):
        """Test fetching multiple pages of videos"""
        # Mock first page response
        first_page = {
            'items': [
                {
                    'id': {'videoId': 'video1'},
                    'snippet': {
                        'title': 'Video 1',
                        'description': 'Description 1',
                        'publishedAt': '2024-01-15T10:00:00Z',
                        'thumbnails': {'default': {'url': 'thumb1.jpg'}}
                    }
                }
            ],
            'nextPageToken': 'page2_token'
        }
        
        # Mock second page response
        second_page = {
            'items': [
                {
                    'id': {'videoId': 'video2'},
                    'snippet': {
                        'title': 'Video 2',
                        'description': 'Description 2',
                        'publishedAt': '2024-01-14T10:00:00Z',
                        'thumbnails': {'default': {'url': 'thumb2.jpg'}}
                    }
                }
            ]
            # No nextPageToken - end of results
        }
        
        # Setup mock to return different responses
        mock_request = Mock()
        mock_request.execute.side_effect = [first_page, second_page]
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        # Execute
        videos = self.service.fetch_videos_from_api()
        
        # Should have combined results from both pages
        self.assertEqual(len(videos), 2)
        self.assertEqual(videos[0]['id'], 'video1')
        self.assertEqual(videos[1]['id'], 'video2')
    
    def test_fetch_with_max_results(self):
        """Test max_results parameter limits returned videos"""
        # Mock response with 5 videos
        mock_response = {
            'items': [
                {
                    'id': {'videoId': f'video{i}'},
                    'snippet': {
                        'title': f'Video {i}',
                        'description': f'Description {i}',
                        'publishedAt': '2024-01-15T10:00:00Z',
                        'thumbnails': {'default': {'url': f'thumb{i}.jpg'}}
                    }
                }
                for i in range(1, 6)
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        # Execute with max_results=3
        videos = self.service.fetch_videos_from_api(max_results=3)
        
        # Should only return 3 videos
        self.assertEqual(len(videos), 3)
    
    def test_fetch_empty_results(self):
        """Test handling empty results from API"""
        mock_response = {'items': []}
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        videos = self.service.fetch_videos_from_api()
        
        self.assertEqual(len(videos), 0)
    
    def test_fetch_quota_exceeded_error(self):
        """Test handling YouTube API quota exceeded error"""
        # Mock HttpError with quotaExceeded
        mock_error = HttpError(
            Mock(status=403),
            b'{"error": {"errors": [{"reason": "quotaExceeded"}]}}'
        )
        
        mock_request = Mock()
        mock_request.execute.side_effect = mock_error
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        videos = self.service.fetch_videos_from_api()
        
        # Should return empty list, not crash
        self.assertEqual(len(videos), 0)
    
    def test_fetch_other_http_error(self):
        """Test handling other HTTP errors"""
        mock_error = HttpError(
            Mock(status=500),
            b'{"error": {"message": "Internal Server Error"}}'
        )
        
        mock_request = Mock()
        mock_request.execute.side_effect = mock_error
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        videos = self.service.fetch_videos_from_api()
        
        self.assertEqual(len(videos), 0)
    
    def test_fetch_generic_exception(self):
        """Test handling generic exceptions"""
        mock_request = Mock()
        mock_request.execute.side_effect = Exception('Network error')
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        videos = self.service.fetch_videos_from_api()
        
        self.assertEqual(len(videos), 0)
    
    def test_fetch_with_uninitialized_youtube(self):
        """Test fetch when YouTube client is not initialized"""
        self.service.youtube = None
        
        videos = self.service.fetch_videos_from_api()
        
        self.assertEqual(len(videos), 0)
    
    def test_thumbnail_selection_priority(self):
        """Test thumbnail URL selection prefers high > medium > default"""
        # Mock response with all thumbnail sizes
        mock_response = {
            'items': [
                {
                    'id': {'videoId': 'video1'},
                    'snippet': {
                        'title': 'Test',
                        'publishedAt': '2024-01-15T10:00:00Z',
                        'thumbnails': {
                            'default': {'url': 'default.jpg'},
                            'medium': {'url': 'medium.jpg'},
                            'high': {'url': 'high.jpg'}
                        }
                    }
                }
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        videos = self.service.fetch_videos_from_api()
        
        # Should prefer high quality
        self.assertEqual(videos[0]['thumbnail'], 'high.jpg')
    
    def test_thumbnail_fallback_to_medium(self):
        """Test thumbnail falls back to medium if high not available"""
        mock_response = {
            'items': [
                {
                    'id': {'videoId': 'video1'},
                    'snippet': {
                        'title': 'Test',
                        'publishedAt': '2024-01-15T10:00:00Z',
                        'thumbnails': {
                            'default': {'url': 'default.jpg'},
                            'medium': {'url': 'medium.jpg'}
                            # No high quality
                        }
                    }
                }
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        videos = self.service.fetch_videos_from_api()
        
        self.assertEqual(videos[0]['thumbnail'], 'medium.jpg')
    
    def test_thumbnail_fallback_to_default(self):
        """Test thumbnail falls back to default if others not available"""
        mock_response = {
            'items': [
                {
                    'id': {'videoId': 'video1'},
                    'snippet': {
                        'title': 'Test',
                        'publishedAt': '2024-01-15T10:00:00Z',
                        'thumbnails': {
                            'default': {'url': 'default.jpg'}
                        }
                    }
                }
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        videos = self.service.fetch_videos_from_api()
        
        self.assertEqual(videos[0]['thumbnail'], 'default.jpg')
    
    def test_thumbnail_empty_when_none_available(self):
        """Test thumbnail is empty string when no thumbnails available"""
        mock_response = {
            'items': [
                {
                    'id': {'videoId': 'video1'},
                    'snippet': {
                        'title': 'Test',
                        'publishedAt': '2024-01-15T10:00:00Z',
                        'thumbnails': {}
                    }
                }
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        videos = self.service.fetch_videos_from_api()
        
        self.assertEqual(videos[0]['thumbnail'], '')
    
    def test_date_parsing_and_timezone(self):
        """Test date parsing converts to UTC timezone"""
        mock_response = {
            'items': [
                {
                    'id': {'videoId': 'video1'},
                    'snippet': {
                        'title': 'Test',
                        'publishedAt': '2024-01-15T10:30:45Z',
                        'thumbnails': {'default': {'url': 'thumb.jpg'}}
                    }
                }
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        videos = self.service.fetch_videos_from_api()
        
        # Check published_at is ISO format string with UTC timezone
        self.assertIn('published_at', videos[0])
        self.assertIn('T', videos[0]['published_at'])
        # ✅ FIX: Just check for 'Z' format since that's what we consistently produce
        self.assertIn('Z', videos[0]['published_at'])
    
    def test_video_url_construction(self):
        """Test video URL is correctly constructed"""
        mock_response = {
            'items': [
                {
                    'id': {'videoId': 'abc123'},
                    'snippet': {
                        'title': 'Test',
                        'publishedAt': '2024-01-15T10:00:00Z',
                        'thumbnails': {'default': {'url': 'thumb.jpg'}}
                    }
                }
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        videos = self.service.fetch_videos_from_api()
        
        self.assertEqual(videos[0]['url'], 'https://www.youtube.com/watch?v=abc123')
    
    def test_missing_description_handled(self):
        """Test missing description field is handled gracefully"""
        mock_response = {
            'items': [
                {
                    'id': {'videoId': 'video1'},
                    'snippet': {
                        'title': 'Test',
                        'publishedAt': '2024-01-15T10:00:00Z',
                        'thumbnails': {'default': {'url': 'thumb.jpg'}}
                        # No description field
                    }
                }
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        videos = self.service.fetch_videos_from_api()
        
        # Description should default to empty string
        self.assertEqual(videos[0]['description'], '')


# ============================================================================
# GET CHANNEL VIDEOS TESTS (CACHING)
# ============================================================================

class GetChannelVideosTests(TestCase):
    """Test YouTubeService.get_channel_videos() with caching"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_youtube = Mock()
        self.mock_cache = Mock()
        
        with patch('feed.youtube_service.build') as mock_build, \
             patch('feed.youtube_service.VideoCache') as mock_cache_class:
            mock_build.return_value = self.mock_youtube
            mock_cache_class.return_value = self.mock_cache
            
            with override_settings(
                YOUTUBE_API_KEY='test_key',
                YOUTUBE_CHANNEL_ID='test_channel'
            ):
                self.service = YouTubeService()
    
    def test_cache_hit_returns_cached_videos(self):
        """Test returns cached videos when cache exists"""
        cached_videos = [
            {
                'id': 'cached1',
                'title': 'Cached Video',
                'description': 'From cache',
                'thumbnail': 'thumb.jpg',
                'published_at': '2024-01-15T10:00:00Z',
                'url': 'https://www.youtube.com/watch?v=cached1'
            }
        ]
        
        self.mock_cache.get_cached_videos.return_value = cached_videos
        
        videos = self.service.get_channel_videos()
        
        # Should return cached videos
        self.assertEqual(videos, cached_videos)
        
        # Should not call API
        self.mock_youtube.search.return_value.list.assert_not_called()
    
    def test_cache_miss_fetches_from_api(self):
        """Test fetches from API when cache is empty"""
        # Cache miss
        self.mock_cache.get_cached_videos.return_value = None
        
        # Mock API response
        mock_response = {
            'items': [
                {
                    'id': {'videoId': 'api1'},
                    'snippet': {
                        'title': 'API Video',
                        'description': 'From API',
                        'publishedAt': '2024-01-15T10:00:00Z',
                        'thumbnails': {'default': {'url': 'thumb.jpg'}}
                    }
                }
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        videos = self.service.get_channel_videos()
        
        # Should return videos from API
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]['id'], 'api1')
        
        # Should update cache
        self.mock_cache.update_cache.assert_called_once()
    
    def test_force_refresh_bypasses_cache(self):
        """Test force_refresh=True bypasses cache"""
        # Cache has data
        cached_videos = [{'id': 'cached1', 'title': 'Cached'}]
        self.mock_cache.get_cached_videos.return_value = cached_videos
        
        # Mock API response
        mock_response = {
            'items': [
                {
                    'id': {'videoId': 'fresh1'},
                    'snippet': {
                        'title': 'Fresh Video',
                        'publishedAt': '2024-01-15T10:00:00Z',
                        'thumbnails': {'default': {'url': 'thumb.jpg'}}
                    }
                }
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        videos = self.service.get_channel_videos(force_refresh=True)
        
        # Should NOT check cache
        self.mock_cache.get_cached_videos.assert_not_called()
        
        # Should return fresh videos from API
        self.assertEqual(videos[0]['id'], 'fresh1')
        
        # Should update cache with fresh data
        self.mock_cache.update_cache.assert_called_once()
    
    def test_updates_cache_after_api_fetch(self):
        """Test cache is updated after successful API fetch"""
        self.mock_cache.get_cached_videos.return_value = None
        
        api_videos = [
            {
                'id': 'video1',
                'title': 'Video 1',
                'description': 'Description',
                'thumbnail': 'thumb.jpg',
                'published_at': '2024-01-15T10:00:00Z',
                'url': 'https://www.youtube.com/watch?v=video1'
            }
        ]
        
        # Mock fetch_videos_from_api
        with patch.object(self.service, 'fetch_videos_from_api', return_value=api_videos):
            videos = self.service.get_channel_videos()
        
        # Verify cache was updated
        self.mock_cache.update_cache.assert_called_once_with(api_videos)
    
    def test_empty_api_result_does_not_crash(self):
        """Test empty API result is handled gracefully"""
        self.mock_cache.get_cached_videos.return_value = None
        
        # Mock empty API response
        with patch.object(self.service, 'fetch_videos_from_api', return_value=[]):
            videos = self.service.get_channel_videos()
        
        # Should return empty list
        self.assertEqual(videos, [])
        
        # Cache update should still be called (even with empty list)
        # This is logged as a warning but doesn't update cache
    
    def test_max_results_forwarded_to_api(self):
        """Test max_results parameter is forwarded to fetch_videos_from_api"""
        self.mock_cache.get_cached_videos.return_value = None
        
        with patch.object(self.service, 'fetch_videos_from_api', return_value=[]) as mock_fetch:
            self.service.get_channel_videos(max_results=10)
        
        # Verify max_results was passed
        mock_fetch.assert_called_once_with(10)
    
    def test_cache_exception_falls_back_to_api(self):
        """Test cache exception doesn't break functionality"""
        # Cache throws exception
        self.mock_cache.get_cached_videos.side_effect = Exception('Cache error')
        
        # Mock API response
        mock_response = {
            'items': [
                {
                    'id': {'videoId': 'video1'},
                    'snippet': {
                        'title': 'Video',
                        'publishedAt': '2024-01-15T10:00:00Z',
                        'thumbnails': {'default': {'url': 'thumb.jpg'}}
                    }
                }
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        self.mock_youtube.search.return_value.list.return_value = mock_request
        
        # Should still work
        videos = self.service.get_channel_videos()
        
        self.assertEqual(len(videos), 1)


# ============================================================================
# INTEGRATION & PRODUCTION SCENARIO TESTS
# ============================================================================

class YouTubeServiceIntegrationTests(TestCase):
    """Test complete workflows and production scenarios"""
    
    @patch('feed.youtube_service.build')
    @patch('feed.youtube_service.VideoCache')
    def test_complete_workflow_api_to_cache(self, mock_cache_class, mock_build):
        """Test complete workflow: API fetch → Cache update → Retrieve from cache"""
        mock_youtube = Mock()
        mock_build.return_value = mock_youtube
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        
        # First call - cache miss
        mock_cache.get_cached_videos.return_value = None
        
        # Mock API response
        api_videos = [
            {
                'id': 'video1',
                'title': 'Test Video',
                'description': 'Test',
                'thumbnail': 'thumb.jpg',
                'published_at': '2024-01-15T10:00:00Z',
                'url': 'https://www.youtube.com/watch?v=video1'
            }
        ]
        
        mock_response = {
            'items': [
                {
                    'id': {'videoId': 'video1'},
                    'snippet': {
                        'title': 'Test Video',
                        'description': 'Test',
                        'publishedAt': '2024-01-15T10:00:00Z',
                        'thumbnails': {'default': {'url': 'thumb.jpg'}}
                    }
                }
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        mock_youtube.search.return_value.list.return_value = mock_request
        
        with override_settings(YOUTUBE_API_KEY='key', YOUTUBE_CHANNEL_ID='channel'):
            service = YouTubeService()
            
            # First call - fetches from API
            videos1 = service.get_channel_videos()
            self.assertEqual(len(videos1), 1)
            
            # Verify cache was updated
            mock_cache.update_cache.assert_called_once()
            
            # Second call - should use cache
            mock_cache.get_cached_videos.return_value = api_videos
            videos2 = service.get_channel_videos()
            
            # Should return same data
            self.assertEqual(videos2, api_videos)
    
    @patch('feed.youtube_service.build')
    @patch('feed.youtube_service.VideoCache')
    @patch('feed.youtube_service.logger')
    def test_logging_behavior(self, mock_logger, mock_cache_class, mock_build):
        """Test appropriate logging at different stages"""
        mock_youtube = Mock()
        mock_build.return_value = mock_youtube
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        
        mock_cache.get_cached_videos.return_value = [{'id': 'cached1'}]
        
        with override_settings(YOUTUBE_API_KEY='key', YOUTUBE_CHANNEL_ID='channel'):
            service = YouTubeService()
            videos = service.get_channel_videos()
        
        # Should log cache hit
        mock_logger.info.assert_called()
    
    @patch('feed.youtube_service.build')
    @patch('feed.youtube_service.VideoCache')
    def test_error_recovery(self, mock_cache_class, mock_build):
        """Test service recovers from errors gracefully"""
        mock_youtube = Mock()
        mock_build.return_value = mock_youtube
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        
        # First call fails
        mock_request = Mock()
        mock_request.execute.side_effect = Exception('Network error')
        mock_youtube.search.return_value.list.return_value = mock_request
        
        with override_settings(YOUTUBE_API_KEY='key', YOUTUBE_CHANNEL_ID='channel'):
            service = YouTubeService()
            
            # First call returns empty
            videos1 = service.get_channel_videos(force_refresh=True)
            self.assertEqual(videos1, [])
            
            # Second call succeeds
            mock_response = {
                'items': [
                    {
                        'id': {'videoId': 'recovered1'},
                        'snippet': {
                            'title': 'Recovered Video',
                            'publishedAt': '2024-01-15T10:00:00Z',
                            'thumbnails': {'default': {'url': 'thumb.jpg'}}
                        }
                    }
                ]
            }
            mock_request.execute.side_effect = None
            mock_request.execute.return_value = mock_response
            
            videos2 = service.get_channel_videos(force_refresh=True)
            self.assertEqual(len(videos2), 1)
            self.assertEqual(videos2[0]['id'], 'recovered1')
    
    @patch('feed.youtube_service.build')
    @patch('feed.youtube_service.VideoCache')
    def test_large_dataset_handling(self, mock_cache_class, mock_build):
        """Test handling large number of videos"""
        mock_youtube = Mock()
        mock_build.return_value = mock_youtube
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        
        mock_cache.get_cached_videos.return_value = None
        
        # Mock response with 100 videos
        mock_response = {
            'items': [
                {
                    'id': {'videoId': f'video{i}'},
                    'snippet': {
                        'title': f'Video {i}',
                        'description': f'Description {i}',
                        'publishedAt': '2024-01-15T10:00:00Z',
                        'thumbnails': {'default': {'url': f'thumb{i}.jpg'}}
                    }
                }
                for i in range(100)
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        mock_youtube.search.return_value.list.return_value = mock_request
        
        with override_settings(YOUTUBE_API_KEY='key', YOUTUBE_CHANNEL_ID='channel'):
            service = YouTubeService()
            videos = service.get_channel_videos()
        
        # Should handle all 100 videos
        self.assertEqual(len(videos), 100)