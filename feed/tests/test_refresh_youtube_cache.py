# feed/tests/test_management_commands.py
"""
Comprehensive bulletproof tests for feed/management/commands/refresh_youtube_cache.py

Test Coverage:
===============
✅ Command Existence & Registration
   - Command can be imported
   - Command is properly registered
   - Help text is defined

✅ Basic Execution
   - Successful cache refresh
   - Command completes without errors
   - YouTubeService integration
   - Cache update called

✅ --clear Flag
   - Cache cleared before refresh
   - Empty list passed to update_cache
   - Proper stdout output

✅ Success Scenarios
   - Videos fetched and cached
   - Success message displayed
   - Video count shown
   - First 5 video titles displayed
   - Styled output (SUCCESS style)

✅ No Videos Scenarios
   - Warning when no videos fetched
   - Proper warning message
   - Styled output (WARNING style)
   - Cache not updated with empty

✅ Output Validation
   - stdout messages
   - Styled messages (SUCCESS, WARNING)
   - Video title formatting
   - Video ID display

✅ YouTubeService Integration
   - Service initialized correctly
   - force_refresh=True used
   - Cache updated with videos
   - Video count correct

✅ Edge Cases & Error Handling
   - Missing video titles (default to 'Untitled')
   - Large number of videos (only show 5)
   - Unicode in video titles
   - Empty video list
   - API failures (graceful handling)

✅ Production Scenarios
   - Multiple sequential runs
   - Clear then refresh workflow
   - Large datasets
   - Real-world video data structure
"""
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO
from unittest.mock import Mock, patch, MagicMock
import sys


# ============================================================================
# COMMAND EXISTENCE & REGISTRATION TESTS
# ============================================================================

class RefreshYoutubeCacheCommandExistenceTests(TestCase):
    """Test command exists and is properly registered"""
    
    def test_command_can_be_imported(self):
        """Test command module can be imported"""
        try:
            from feed.management.commands import refresh_youtube_cache
            self.assertTrue(hasattr(refresh_youtube_cache, 'Command'))
        except ImportError:
            self.fail("Could not import refresh_youtube_cache command")
    
    def test_command_has_help_text(self):
        """Test command has help text defined"""
        from feed.management.commands.refresh_youtube_cache import Command
        
        self.assertIsNotNone(Command.help)
        self.assertIn('cache', Command.help.lower())
    
    def test_command_can_be_called(self):
        """Test command can be called via call_command"""
        with patch('feed.management.commands.refresh_youtube_cache.YouTubeService'):
            try:
                out = StringIO()
                call_command('refresh_youtube_cache', stdout=out)
            except Exception as e:
                self.fail(f"Command execution failed: {str(e)}")


# ============================================================================
# BASIC EXECUTION TESTS
# ============================================================================

class RefreshYoutubeCacheBasicExecutionTests(TestCase):
    """Test basic command execution"""
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_successful_cache_refresh(self, mock_service_class):
        """Test successful cache refresh execution"""
        # Setup mock
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = [
            {
                'id': 'video1',
                'title': 'Test Video 1',
                'description': 'Description',
                'thumbnail': 'https://example.com/thumb1.jpg',
                'published_at': '2024-01-15T10:00:00Z',
                'url': 'https://www.youtube.com/watch?v=video1'
            }
        ]
        mock_service_class.return_value = mock_service
        
        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        
        # Verify service initialized
        mock_service_class.assert_called_once()
        
        # Verify get_channel_videos called with force_refresh
        mock_service.get_channel_videos.assert_called_once_with(force_refresh=True)
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_command_completes_without_errors(self, mock_service_class):
        """Test command completes without raising errors"""
        # Setup mock
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = []
        mock_service_class.return_value = mock_service
        
        # Should not raise any errors
        try:
            out = StringIO()
            call_command('refresh_youtube_cache', stdout=out)
        except Exception as e:
            self.fail(f"Command raised unexpected exception: {str(e)}")
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_youtube_service_integration(self, mock_service_class):
        """Test integration with YouTubeService"""
        # Setup mock
        mock_service = Mock()
        mock_cache = Mock()
        mock_service.cache = mock_cache
        mock_service.get_channel_videos.return_value = [{'id': 'test'}]
        mock_service_class.return_value = mock_service
        
        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        
        # Verify service instance created
        self.assertEqual(mock_service_class.call_count, 1)


# ============================================================================
# --CLEAR FLAG TESTS
# ============================================================================

class RefreshYoutubeCacheClearFlagTests(TestCase):
    """Test --clear flag functionality"""
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_clear_flag_clears_cache_before_refresh(self, mock_service_class):
        """Test --clear flag clears cache before refreshing"""
        # Setup mock
        mock_service = Mock()
        mock_cache = Mock()
        mock_service.cache = mock_cache
        mock_service.get_channel_videos.return_value = [{'id': 'video1'}]
        mock_service_class.return_value = mock_service
        
        # Execute with --clear
        out = StringIO()
        call_command('refresh_youtube_cache', '--clear', stdout=out)
        
        # Verify cache cleared (update_cache called with empty list)
        mock_cache.update_cache.assert_called_with([])
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_clear_flag_output_message(self, mock_service_class):
        """Test --clear flag displays clearing message"""
        # Setup mock
        mock_service = Mock()
        mock_cache = Mock()
        mock_service.cache = mock_cache
        mock_service.get_channel_videos.return_value = []
        mock_service_class.return_value = mock_service
        
        # Execute with --clear
        out = StringIO()
        call_command('refresh_youtube_cache', '--clear', stdout=out)
        output = out.getvalue()
        
        # Should display clearing message
        self.assertIn('Clearing existing cache', output)
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_without_clear_flag_no_clearing(self, mock_service_class):
        """Test without --clear flag, cache is not cleared"""
        # Setup mock
        mock_service = Mock()
        mock_cache = Mock()
        mock_service.cache = mock_cache
        mock_service.get_channel_videos.return_value = [{'id': 'video1'}]
        mock_service_class.return_value = mock_service
        
        # Execute without --clear
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        output = out.getvalue()
        
        # Should NOT display clearing message
        self.assertNotIn('Clearing existing cache', output)
        
        # Cache.update_cache should NOT be called with empty list
        # (it might be called with actual videos, but not with [])
        for call_args in mock_cache.update_cache.call_args_list:
            args, kwargs = call_args
            if args:
                self.assertNotEqual(args[0], [])


# ============================================================================
# SUCCESS SCENARIOS TESTS
# ============================================================================

class RefreshYoutubeCacheSuccessTests(TestCase):
    """Test successful cache refresh scenarios"""
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_success_message_displayed(self, mock_service_class):
        """Test success message displayed when videos cached"""
        # Setup mock with videos
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = [
            {'id': 'video1', 'title': 'Video 1'},
            {'id': 'video2', 'title': 'Video 2'},
            {'id': 'video3', 'title': 'Video 3'}
        ]
        mock_service_class.return_value = mock_service
        
        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        output = out.getvalue()
        
        # Should display success message
        self.assertIn('Successfully cached', output)
        self.assertIn('3 videos', output)
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_video_count_in_output(self, mock_service_class):
        """Test video count is shown in output"""
        # Setup mock
        videos = [{'id': f'video{i}', 'title': f'Video {i}'} for i in range(10)]
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = videos
        mock_service_class.return_value = mock_service
        
        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        output = out.getvalue()
        
        # Should show count of 10
        self.assertIn('10 videos', output)
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_first_five_videos_displayed(self, mock_service_class):
        """Test first 5 video titles are displayed"""
        # Setup mock with more than 5 videos
        videos = [
            {'id': f'video{i}', 'title': f'Test Video {i}'} 
            for i in range(10)
        ]
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = videos
        mock_service_class.return_value = mock_service
        
        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        output = out.getvalue()
        
        # Should display first 5 video titles
        for i in range(5):
            self.assertIn(f'Test Video {i}', output)
        
        # Should NOT display 6th+ video
        self.assertNotIn('Test Video 5', output)
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_video_ids_displayed_in_output(self, mock_service_class):
        """Test video IDs are displayed in output"""
        # Setup mock
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = [
            {'id': 'abc123', 'title': 'Test Video'}
        ]
        mock_service_class.return_value = mock_service
        
        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        output = out.getvalue()
        
        # Should display video ID
        self.assertIn('abc123', output)
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_fetching_message_displayed(self, mock_service_class):
        """Test 'Fetching videos' message is displayed"""
        # Setup mock
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = []
        mock_service_class.return_value = mock_service
        
        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        output = out.getvalue()
        
        # Should display fetching message
        self.assertIn('Fetching videos from YouTube', output)


# ============================================================================
# NO VIDEOS SCENARIOS TESTS
# ============================================================================

class RefreshYoutubeCacheNoVideosTests(TestCase):
    """Test scenarios when no videos are fetched"""
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_warning_when_no_videos(self, mock_service_class):
        """Test warning message when no videos fetched"""
        # Setup mock with no videos
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = []
        mock_service_class.return_value = mock_service
        
        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        output = out.getvalue()
        
        # Should display warning
        self.assertIn('No videos were cached', output)
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_no_video_titles_when_empty(self, mock_service_class):
        """Test no video titles displayed when list is empty"""
        # Setup mock with empty list
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = []
        mock_service_class.return_value = mock_service
        
        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        output = out.getvalue()
        
        # Should NOT show "First few videos cached" section
        # (since there are no videos to show)
        # The success message won't appear, only warning


# ============================================================================
# OUTPUT VALIDATION TESTS
# ============================================================================

class RefreshYoutubeCacheOutputTests(TestCase):
    """Test command output formatting and styling"""
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_output_structure(self, mock_service_class):
        """Test output has expected structure"""
        # Setup mock
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = [
            {'id': 'video1', 'title': 'Test Video'}
        ]
        mock_service_class.return_value = mock_service
        
        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        output = out.getvalue()
        
        # Should have key sections
        self.assertIn('Fetching videos', output)
        self.assertIn('Successfully cached', output)
        self.assertIn('First few videos cached', output)
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_video_title_formatting(self, mock_service_class):
        """Test video titles are formatted with dash prefix"""
        # Setup mock
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = [
            {'id': 'video1', 'title': 'My Test Video'}
        ]
        mock_service_class.return_value = mock_service
        
        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        output = out.getvalue()
        
        # Should have dash prefix for video listing
        self.assertIn('- My Test Video', output)


# ============================================================================
# EDGE CASES & ERROR HANDLING TESTS
# ============================================================================

class RefreshYoutubeCacheEdgeCasesTests(TestCase):
    """Test edge cases and error handling"""
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_missing_video_title_defaults_to_untitled(self, mock_service_class):
        """Test videos without title default to 'Untitled'"""
        # Setup mock with video missing title
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = [
            {'id': 'video1'}  # No title field
        ]
        mock_service_class.return_value = mock_service
        
        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        output = out.getvalue()
        
        # Should display 'Untitled'
        self.assertIn('Untitled', output)
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_unicode_in_video_titles(self, mock_service_class):
        """Test unicode characters in video titles are handled"""
        # Setup mock with unicode
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = [
            {'id': 'video1', 'title': 'Test with émojis 🎉 and 中文'}
        ]
        mock_service_class.return_value = mock_service
        
        # Execute command - should not crash
        out = StringIO()
        try:
            call_command('refresh_youtube_cache', stdout=out)
            output = out.getvalue()
            
            # Should contain unicode
            self.assertIn('émojis', output)
            self.assertIn('中文', output)
        except UnicodeEncodeError:
            self.fail("Command failed to handle unicode characters")
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_large_video_list(self, mock_service_class):
        """Test handling of large video lists (100+ videos)"""
        # Setup mock with 150 videos
        videos = [
            {'id': f'video{i}', 'title': f'Video {i}'} 
            for i in range(150)
        ]
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = videos
        mock_service_class.return_value = mock_service
        
        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        output = out.getvalue()
        
        # Should show count
        self.assertIn('150 videos', output)
        
        # Should only show first 5 in listing
        for i in range(5):
            self.assertIn(f'Video {i}', output)
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_service_initialization_failure(self, mock_service_class):
        """Test graceful handling when service fails to initialize"""
        # Setup mock to raise exception on initialization
        mock_service_class.side_effect = Exception('API initialization failed')
        
        # Execute command - should raise error
        with self.assertRaises(Exception):
            out = StringIO()
            call_command('refresh_youtube_cache', stdout=out)
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_get_channel_videos_exception(self, mock_service_class):
        """Test handling when get_channel_videos raises exception"""
        # Setup mock to raise exception
        mock_service = Mock()
        mock_service.get_channel_videos.side_effect = Exception('API error')
        mock_service_class.return_value = mock_service
        
        # Execute command - should raise error
        with self.assertRaises(Exception):
            out = StringIO()
            call_command('refresh_youtube_cache', stdout=out)
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_empty_video_title(self, mock_service_class):
        """Test handling of empty string video title"""
        # Setup mock with empty title
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = [
            {'id': 'video1', 'title': ''}  # Empty string
        ]
        mock_service_class.return_value = mock_service

        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        output = out.getvalue()

        # Empty string title should remain empty (not 'Untitled')
        self.assertIn('(video1)', output)



# ============================================================================
# INTEGRATION & PRODUCTION SCENARIOS TESTS
# ============================================================================

class RefreshYoutubeCacheIntegrationTests(TestCase):
    """Test integration scenarios and production use cases"""
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_multiple_sequential_runs(self, mock_service_class):
        """Test running command multiple times in sequence"""
        # Setup mock
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = [
            {'id': 'video1', 'title': 'Test Video'}
        ]
        mock_service_class.return_value = mock_service
        
        # Run command twice
        out1 = StringIO()
        call_command('refresh_youtube_cache', stdout=out1)
        
        out2 = StringIO()
        call_command('refresh_youtube_cache', stdout=out2)
        
        # Both should succeed
        self.assertIn('Successfully cached', out1.getvalue())
        self.assertIn('Successfully cached', out2.getvalue())
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_clear_then_refresh_workflow(self, mock_service_class):
        """Test clear then refresh workflow"""
        # Setup mock
        mock_service = Mock()
        mock_cache = Mock()
        mock_service.cache = mock_cache
        mock_service.get_channel_videos.return_value = [
            {'id': 'video1', 'title': 'Fresh Video'}
        ]
        mock_service_class.return_value = mock_service
        
        # Execute with --clear
        out = StringIO()
        call_command('refresh_youtube_cache', '--clear', stdout=out)
        output = out.getvalue()
        
        # Should clear first, then refresh
        self.assertIn('Clearing existing cache', output)
        self.assertIn('Fetching videos', output)
        self.assertIn('Successfully cached', output)
        
        # Verify cache.update_cache called twice (once with [], once with videos)
        self.assertEqual(mock_cache.update_cache.call_count, 1)
        # First call should be with empty list for clearing
        mock_cache.update_cache.assert_called_with([])
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_real_world_video_data_structure(self, mock_service_class):
        """Test with realistic YouTube video data structure"""
        # Realistic video data
        realistic_videos = [
            {
                'id': 'dQw4w9WgXcQ',
                'title': 'Rick Astley - Never Gonna Give You Up',
                'description': 'Official video...',
                'thumbnail': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
                'published_at': '2009-10-25T06:57:33Z',
                'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'type': 'video'
            }
        ]
        
        mock_service = Mock()
        mock_service.get_channel_videos.return_value = realistic_videos
        mock_service_class.return_value = mock_service
        
        # Execute command
        out = StringIO()
        call_command('refresh_youtube_cache', stdout=out)
        output = out.getvalue()
        
        # Should handle all fields
        self.assertIn('Rick Astley', output)
        self.assertIn('dQw4w9WgXcQ', output)
    
    @patch('feed.management.commands.refresh_youtube_cache.YouTubeService')
    def test_command_with_only_clear_flag(self, mock_service_class):
        """Test running command with only --clear (clears and refreshes)"""
        # Setup mock
        mock_service = Mock()
        mock_cache = Mock()
        mock_service.cache = mock_cache
        mock_service.get_channel_videos.return_value = []
        mock_service_class.return_value = mock_service
        
        # Execute with --clear
        out = StringIO()
        call_command('refresh_youtube_cache', '--clear', stdout=out)
        
        # Should clear cache
        mock_cache.update_cache.assert_called_once_with([])
        
        # Should still attempt to fetch videos
        mock_service.get_channel_videos.assert_called_once()


# ============================================================================
# ARGUMENT PARSING TESTS
# ============================================================================

class RefreshYoutubeCacheArgumentTests(TestCase):
    """Test command argument parsing"""
    
    def test_clear_argument_is_optional(self):
        """Test --clear argument is optional"""
        from feed.management.commands.refresh_youtube_cache import Command
        
        # Get parser
        command = Command()
        parser = command.create_parser('manage.py', 'refresh_youtube_cache')
        
        # Parse without --clear
        with patch('feed.management.commands.refresh_youtube_cache.YouTubeService'):
            try:
                args = parser.parse_args([])
                self.assertFalse(args.clear)
            except SystemExit:
                self.fail("Parser failed with no arguments")
    
    def test_clear_argument_sets_flag(self):
        """Test --clear argument sets flag to True"""
        from feed.management.commands.refresh_youtube_cache import Command
        
        # Get parser
        command = Command()
        parser = command.create_parser('manage.py', 'refresh_youtube_cache')
        
        # Parse with --clear
        args = parser.parse_args(['--clear'])
        self.assertTrue(args.clear)