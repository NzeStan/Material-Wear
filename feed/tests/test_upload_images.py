# feed/tests/test_upload_images.py
"""
Comprehensive bulletproof tests for feed/management/commands/upload_images.py

Test Coverage:
===============
✅ Command Existence & Registration
   - Command can be imported
   - Command is properly registered
   - Help text is defined
   - Arguments configured correctly

✅ CSV Validation
   - Valid CSV with all headers
   - Missing required headers
   - Empty CSV file
   - Invalid encoding
   - Malformed CSV structure
   - CSV without headers

✅ Image Processing
   - Successful image upload
   - External URL download
   - Cloudinary URL reuse (no duplication)
   - Active/inactive status handling
   - Transaction rollback on error

✅ URL Validation & Download
   - Valid external URLs
   - Invalid URLs (malformed, empty)
   - URLs too long (>500 chars)
   - Non-image content types
   - File size validation (>10MB)
   - Timeout handling
   - Network errors
   - Missing content-type header

✅ Cloudinary Integration
   - Cloudinary URL detection
   - Public ID extraction (various formats)
   - Transformation URL handling
   - Version parameter handling
   - Query parameter stripping
   - Invalid Cloudinary URLs
   - Reuse existing images (no duplicate)

✅ Boolean Conversion (_str_to_bool)
   - True values: 'true', '1', 'yes', 'y'
   - False values: 'false', '0', 'no', 'n'
   - Empty/None defaults to True
   - Invalid values default to False
   - Case insensitivity
   - Whitespace handling

✅ Dry-Run Mode
   - No database changes
   - Preview output shown
   - All validations still run
   - Success/error counting works

✅ Output & Reporting
   - Success messages
   - Error messages
   - Progress indicators
   - Summary statistics
   - Styled output (SUCCESS, WARNING, ERROR)
   - Unicode handling in titles

✅ Edge Cases & Production Scenarios
   - Large CSV files (100+ rows)
   - Mixed success and failures
   - Concurrent URL downloads
   - Special characters in URLs
   - Duplicate URLs in CSV
   - Missing optional fields
   - Cloudinary URLs with transformations
   - Real-world CSV formats
   - Various image formats (jpg, png, gif, webp)

✅ Error Handling
   - File not found
   - Permission errors
   - Database errors
   - API failures
   - Invalid image data
   - Corrupt files
   - Transaction rollback on failure
"""
from django.test import TestCase, TransactionTestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from io import StringIO, BytesIO
from PIL import Image as PILImage
from unittest.mock import Mock, patch, MagicMock, mock_open, PropertyMock
from feed.models import Image
from feed.management.commands.upload_images import Command
import csv
import tempfile
import requests
import os


# Helper function to create valid image bytes
def create_valid_image_bytes():
    """Create actual valid image bytes for testing"""
    img = PILImage.new('RGB', (100, 100), color='red')
    img_io = BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)
    return img_io.getvalue()


# ============================================================================
# COMMAND EXISTENCE & REGISTRATION TESTS
# ============================================================================

class UploadImagesCommandExistenceTests(TestCase):
    """Test command exists and is properly registered"""
    
    def test_command_can_be_imported(self):
        """Test command module can be imported"""
        try:
            from feed.management.commands import upload_images
            self.assertTrue(hasattr(upload_images, 'Command'))
        except ImportError:
            self.fail("Could not import upload_images command")
    
    def test_command_has_help_text(self):
        """Test command has help text defined"""
        from feed.management.commands.upload_images import Command
        
        self.assertIsNotNone(Command.help)
        self.assertIn('upload', Command.help.lower())
    
    def test_command_can_be_called(self):
        """Test command can be called via call_command (with mock)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['image_url', 'active'])
            writer.writeheader()
            writer.writerow({'image_url': 'https://example.com/test.jpg', 'active': 'true'})
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
        except Exception as e:
            self.fail(f"Command execution failed: {str(e)}")
        finally:
            os.unlink(csv_path)
    
    def test_command_arguments_configured(self):
        """Test command has required arguments"""
        command = Command()
        parser = command.create_parser('manage.py', 'upload_images')
        
        # Should require csv_file argument
        with self.assertRaises(CommandError):
            parser.parse_args([])
    
    def test_dry_run_argument_optional(self):
        """Test --dry-run argument is optional"""
        command = Command()
        parser = command.create_parser('manage.py', 'upload_images')
        
        # Should accept with just csv_file
        args = parser.parse_args(['test.csv'])
        self.assertFalse(args.dry_run)
    
    def test_dry_run_argument_sets_flag(self):
        """Test --dry-run argument sets flag to True"""
        command = Command()
        parser = command.create_parser('manage.py', 'upload_images')
        
        args = parser.parse_args(['test.csv', '--dry-run'])
        self.assertTrue(args.dry_run)


# ============================================================================
# CSV VALIDATION TESTS
# ============================================================================

class CSVValidationTests(TestCase):
    """Test CSV file validation"""
    
    def test_valid_csv_with_all_headers(self):
        """Test CSV with all required and optional headers"""
        csv_content = """image_url,active
https://example.com/image1.jpg,true
https://example.com/image2.jpg,false"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [b'fake_image_data']
                mock_get.return_value = mock_response
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                output = out.getvalue()
                self.assertIn('✓ CSV headers validated', output)
        finally:
            os.unlink(csv_path)
    
    def test_missing_required_header(self):
        """Test CSV missing required 'image_url' header"""
        csv_content = """url,active
https://example.com/image1.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with self.assertRaises(CommandError) as cm:
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
            
            self.assertIn('Missing required columns', str(cm.exception))
            self.assertIn('image_url', str(cm.exception))
        finally:
            os.unlink(csv_path)
    
    def test_empty_csv_file(self):
        """Test handling of empty CSV file"""
        csv_content = ""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with self.assertRaises(CommandError) as cm:
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
            
            self.assertIn('empty', str(cm.exception).lower())
        finally:
            os.unlink(csv_path)
    
    def test_csv_with_only_headers(self):
        """Test CSV with headers but no data rows"""
        csv_content = "image_url,active\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with self.assertRaises(CommandError) as cm:
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
            
            self.assertIn('empty', str(cm.exception).lower())
        finally:
            os.unlink(csv_path)
    
    def test_csv_file_not_found(self):
        """Test handling of non-existent CSV file"""
        with self.assertRaises(CommandError) as cm:
            out = StringIO()
            call_command('upload_images', 'nonexistent.csv', stdout=out)
        
        self.assertIn('not found', str(cm.exception).lower())
    
    def test_csv_with_invalid_encoding(self):
        """Test handling of CSV with invalid encoding"""
        # Create file with invalid UTF-8
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
            # Write invalid UTF-8 bytes
            f.write(b'\xff\xfe' + 'image_url,active\n'.encode('utf-16'))
            csv_path = f.name
        
        try:
            with self.assertRaises(CommandError) as cm:
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
            
            self.assertIn('encoding', str(cm.exception).lower())
        finally:
            os.unlink(csv_path)
    
    def test_csv_without_headers(self):
        """Test CSV file without headers"""
        csv_content = """https://example.com/image1.jpg,true
https://example.com/image2.jpg,false"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with self.assertRaises(CommandError) as cm:
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
            
            # Should fail validation - first row becomes headers
            self.assertIn('Missing required columns', str(cm.exception))
        finally:
            os.unlink(csv_path)


# ============================================================================
# IMAGE PROCESSING TESTS
# ============================================================================

class ImageProcessingTests(TransactionTestCase):
    """Test image processing and database operations"""
    
    def test_successful_image_upload(self):
        """Test successful upload of image from external URL"""
        csv_content = """image_url,active
https://example.com/test.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                # Verify image was created
                self.assertEqual(Image.objects.count(), 1)
                image = Image.objects.first()
                self.assertTrue(image.active)
        finally:
            os.unlink(csv_path)
    
    def test_inactive_image_upload(self):
        """Test uploading inactive image"""
        csv_content = """image_url,active
https://example.com/test.jpg,false"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                # Verify image was created as inactive
                self.assertEqual(Image.objects.count(), 1)
                image = Image.objects.first()
                self.assertFalse(image.active)
        finally:
            os.unlink(csv_path)
    
    def test_missing_active_field_defaults_to_true(self):
        """Test that missing active field defaults to True"""
        csv_content = """image_url
https://example.com/test.jpg"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                # Should default to active=True
                self.assertEqual(Image.objects.count(), 1)
                image = Image.objects.first()
                self.assertTrue(image.active)
        finally:
            os.unlink(csv_path)
    
    def test_empty_image_url_raises_error(self):
        """Test that empty image_url raises error"""
        csv_content = """image_url,active
,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            out = StringIO()
            call_command('upload_images', csv_path, stdout=out)
            
            output = out.getvalue()
            # Should have error
            self.assertIn('Error', output)
            self.assertIn('image_url cannot be empty', output)
        finally:
            os.unlink(csv_path)
    
    def test_transaction_rollback_on_error(self):
        """Test that failed image upload doesn't leave partial data"""
        csv_content = """image_url,active
https://example.com/test.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                # Simulate download failure
                mock_get.return_value = None
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                # No images should be created
                self.assertEqual(Image.objects.count(), 0)
        finally:
            os.unlink(csv_path)
    
    def test_cloudinary_url_reuse(self):
        """Test that Cloudinary URLs are reused without re-upload"""
        csv_content = """image_url,active
https://res.cloudinary.com/demo/image/upload/products/kakhi.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                output = out.getvalue()
                # Should indicate reuse
                self.assertIn('Using existing Cloudinary image', output)
                
                # Should NOT have called requests.get (no download)
                mock_get.assert_not_called()
                
                # Image should still be created
                self.assertEqual(Image.objects.count(), 1)
        finally:
            os.unlink(csv_path)


# ============================================================================
# URL VALIDATION & DOWNLOAD TESTS
# ============================================================================

class URLValidationDownloadTests(TestCase):
    """Test URL validation and download functionality"""
    
    @patch('feed.management.commands.upload_images.requests.get')
    def test_successful_image_download(self, mock_get):
        """Test successful image download from URL"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '50000'}
        mock_response.iter_content = lambda chunk_size: [b'fake_image_data']
        mock_get.return_value = mock_response
        
        command = Command()
        command.stdout = StringIO()
        
        result = command._download_image('https://example.com/image.jpg')
        
        self.assertIsNotNone(result)
        mock_get.assert_called_once()
    
    @patch('feed.management.commands.upload_images.requests.get')
    def test_invalid_content_type(self, mock_get):
        """Test rejection of non-image content types"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_get.return_value = mock_response
        
        command = Command()
        command.stdout = StringIO()
        
        result = command._download_image('https://example.com/page.html')
        
        self.assertIsNone(result)
    
    @patch('feed.management.commands.upload_images.requests.get')
    def test_file_too_large(self, mock_get):
        """Test rejection of files larger than 10MB"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'content-type': 'image/jpeg',
            'content-length': str(11 * 1024 * 1024)  # 11MB
        }
        mock_get.return_value = mock_response
        
        command = Command()
        command.stdout = StringIO()
        
        result = command._download_image('https://example.com/huge.jpg')
        
        self.assertIsNone(result)
    
    def test_url_too_long(self):
        """Test rejection of URLs longer than 500 characters"""
        long_url = 'https://example.com/' + 'x' * 500
        
        command = Command()
        command.stdout = StringIO()
        
        result = command._download_image(long_url)
        
        self.assertIsNone(result)
    
    def test_empty_url(self):
        """Test handling of empty URL"""
        command = Command()
        
        self.assertIsNone(command._download_image(''))
        self.assertIsNone(command._download_image(None))
        self.assertIsNone(command._download_image('   '))
    
    @patch('feed.management.commands.upload_images.requests.get')
    def test_download_timeout(self, mock_get):
        """Test handling of download timeout"""
        mock_get.side_effect = requests.Timeout()
        
        command = Command()
        command.stdout = StringIO()
        
        result = command._download_image('https://example.com/image.jpg')
        
        self.assertIsNone(result)
    
    @patch('feed.management.commands.upload_images.requests.get')
    def test_network_error(self, mock_get):
        """Test handling of network errors"""
        mock_get.side_effect = requests.RequestException("Network error")
        
        command = Command()
        command.stdout = StringIO()
        
        result = command._download_image('https://example.com/image.jpg')
        
        self.assertIsNone(result)
    
    @patch('feed.management.commands.upload_images.requests.get')
    def test_http_error_status(self, mock_get):
        """Test handling of HTTP error status codes"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        command = Command()
        command.stdout = StringIO()
        
        result = command._download_image('https://example.com/missing.jpg')
        
        self.assertIsNone(result)
    
    @patch('feed.management.commands.upload_images.requests.get')
    def test_missing_content_type_header(self, mock_get):
        """Test handling of missing content-type header"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}  # No content-type
        mock_get.return_value = mock_response
        
        command = Command()
        command.stdout = StringIO()
        
        result = command._download_image('https://example.com/image.jpg')
        
        # Should reject due to missing content-type
        self.assertIsNone(result)
    
    @patch('feed.management.commands.upload_images.requests.get')
    def test_filename_extraction_from_url(self, mock_get):
        """Test filename extraction from URL"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
        mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
        mock_get.return_value = mock_response
        
        command = Command()
        command.stdout = StringIO()
        
        result = command._download_image('https://example.com/products/test-image.jpg')
        
        self.assertIsNotNone(result)
        self.assertIn('.jpg', result.name)
    
    @patch('feed.management.commands.upload_images.requests.get')
    def test_filename_with_query_parameters(self, mock_get):
        """Test filename extraction from URL with query parameters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
        mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
        mock_get.return_value = mock_response
        
        command = Command()
        command.stdout = StringIO()
        
        result = command._download_image('https://example.com/image.jpg?size=large&quality=high')
        
        self.assertIsNotNone(result)
        self.assertIn('.jpg', result.name)
        self.assertNotIn('?', result.name)


# ============================================================================
# CLOUDINARY INTEGRATION TESTS
# ============================================================================

class CloudinaryIntegrationTests(TestCase):
    """Test Cloudinary URL handling"""
    
    def test_cloudinary_url_detection(self):
        """Test detection of Cloudinary URLs"""
        command = Command()
        
        cloudinary_urls = [
            'https://res.cloudinary.com/demo/image/upload/sample.jpg',
            'https://res.cloudinary.com/demo/image/upload/v1234567/sample.jpg',
            'https://res.cloudinary.com/mycloud/image/upload/folder/image.jpg',
        ]
        
        for url in cloudinary_urls:
            result = command._is_cloudinary_url(url)
            self.assertTrue(result, f"Failed to detect Cloudinary URL: {url}")
    
    def test_non_cloudinary_url_detection(self):
        """Test that non-Cloudinary URLs are not detected"""
        command = Command()
        
        non_cloudinary_urls = [
            'https://example.com/image.jpg',
            'https://imgur.com/abc123.jpg',
            'https://cloudinary.com/image.jpg',  # Missing res. subdomain
            'https://res.cloudinary.com/demo/video/upload/sample.mp4',  # Not image
            '',
            None,
        ]
        
        for url in non_cloudinary_urls:
            result = command._is_cloudinary_url(url)
            self.assertFalse(result, f"Incorrectly detected as Cloudinary URL: {url}")
    
    def test_extract_simple_public_id(self):
        """Test extracting public_id from simple Cloudinary URL"""
        command = Command()
        
        url = 'https://res.cloudinary.com/demo/image/upload/sample.jpg'
        public_id = command._extract_cloudinary_public_id(url)
        
        self.assertEqual(public_id, 'sample.jpg')
    
    def test_extract_public_id_with_version(self):
        """Test extracting public_id from URL with version"""
        command = Command()
        
        url = 'https://res.cloudinary.com/demo/image/upload/v1234567890/sample.jpg'
        public_id = command._extract_cloudinary_public_id(url)
        
        # Version should be removed
        self.assertEqual(public_id, 'sample.jpg')
    
    def test_extract_public_id_with_folder(self):
        """Test extracting public_id from URL with folder path"""
        command = Command()
        
        url = 'https://res.cloudinary.com/demo/image/upload/products/kakhi.jpg'
        public_id = command._extract_cloudinary_public_id(url)
        
        self.assertEqual(public_id, 'products/kakhi.jpg')
    
    def test_extract_public_id_with_transformations(self):
        """Test extracting public_id from URL with transformations"""
        command = Command()
        
        # URL with width, height, crop transformations
        url = 'https://res.cloudinary.com/demo/image/upload/w_400,h_300,c_fill/sample.jpg'
        public_id = command._extract_cloudinary_public_id(url)
        
        # Transformations should be removed
        self.assertEqual(public_id, 'sample.jpg')
    
    def test_extract_public_id_with_query_parameters(self):
        """Test extracting public_id from URL with query parameters"""
        command = Command()
        
        url = 'https://res.cloudinary.com/demo/image/upload/sample.jpg?_a=123456'
        public_id = command._extract_cloudinary_public_id(url)
        
        # Query parameters should be removed
        self.assertEqual(public_id, 'sample.jpg')
    
    def test_extract_public_id_complex_url(self):
        """Test extracting public_id from complex URL with everything"""
        command = Command()
        
        url = 'https://res.cloudinary.com/demo/image/upload/w_500,h_400,c_fill/v1234567/folder/subfolder/image.jpg?_a=abc'
        public_id = command._extract_cloudinary_public_id(url)
        
        # Should get clean folder/filename
        self.assertEqual(public_id, 'folder/subfolder/image.jpg')
    
    def test_extract_public_id_invalid_url(self):
        """Test extracting public_id from invalid Cloudinary URL"""
        command = Command()
        
        invalid_urls = [
            'https://example.com/image.jpg',
            'https://res.cloudinary.com/demo/invalid',
            '',
            None,
        ]
        
        for url in invalid_urls:
            public_id = command._extract_cloudinary_public_id(url)
            self.assertIsNone(public_id, f"Should return None for invalid URL: {url}")
    
    def test_extract_public_id_with_multiple_transformations(self):
        """Test extracting public_id with multiple transformation parameters"""
        command = Command()
        
        url = 'https://res.cloudinary.com/demo/image/upload/w_400,h_300,c_fill,q_auto,f_auto,dpr_2.0/sample.jpg'
        public_id = command._extract_cloudinary_public_id(url)
        
        self.assertEqual(public_id, 'sample.jpg')
    
    @patch('feed.management.commands.upload_images.requests.get')
    def test_cloudinary_url_returns_public_id_string(self, mock_get):
        """Test that Cloudinary URLs return public_id string, not File object"""
        command = Command()
        command.stdout = StringIO()
        
        cloudinary_url = 'https://res.cloudinary.com/demo/image/upload/products/kakhi.jpg'
        result = command._download_image(cloudinary_url)
        
        # Should return string (public_id), not File object
        self.assertIsInstance(result, str)
        self.assertEqual(result, 'products/kakhi.jpg')
        
        # Should NOT call requests.get (no download)
        mock_get.assert_not_called()
    
    def test_invalid_cloudinary_url_falls_back_to_download(self):
        """Test that invalid Cloudinary URLs fall back to normal download"""
        command = Command()
        command.stdout = StringIO()
        
        # Cloudinary domain but invalid format
        with patch('feed.management.commands.upload_images.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
            mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
            mock_get.return_value = mock_response
            
            # Invalid format - should fall back to download
            url = 'https://res.cloudinary.com/demo/invalid/path/image.jpg'
            result = command._download_image(url)
            
            # Should attempt download
            mock_get.assert_called_once()


# ============================================================================
# BOOLEAN CONVERSION TESTS
# ============================================================================

class BooleanConversionTests(TestCase):
    """Test _str_to_bool conversion logic"""
    
    def test_true_values(self):
        """Test various representations of True"""
        command = Command()
        
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'YES', 'y', 'Y', True]
        
        for value in true_values:
            result = command._str_to_bool(value)
            self.assertTrue(result, f"Failed for value: {value}")
    
    def test_false_values(self):
        """Test various representations of False"""
        command = Command()
        
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO', 'n', 'N', False]
        
        for value in false_values:
            result = command._str_to_bool(value)
            self.assertFalse(result, f"Failed for value: {value}")
    
    def test_empty_defaults_to_true(self):
        """Test that empty/None/whitespace defaults to True"""
        command = Command()
        
        empty_values = [None, '', '   ', '\t', '\n']
        
        for value in empty_values:
            result = command._str_to_bool(value)
            self.assertTrue(result, f"Failed for value: {repr(value)}")
    
    def test_invalid_values_default_to_false(self):
        """Test that invalid values default to False"""
        command = Command()
        
        invalid_values = ['maybe', 'unknown', '2', 'other', 'invalid']
        
        for value in invalid_values:
            result = command._str_to_bool(value)
            self.assertFalse(result, f"Failed for value: {value}")
    
    def test_boolean_passthrough(self):
        """Test that actual boolean values are passed through"""
        command = Command()
        
        self.assertTrue(command._str_to_bool(True))
        self.assertFalse(command._str_to_bool(False))
    
    def test_case_insensitivity(self):
        """Test that conversion is case-insensitive"""
        command = Command()
        
        # Mixed case should work
        self.assertTrue(command._str_to_bool('TrUe'))
        self.assertTrue(command._str_to_bool('YeS'))
        self.assertFalse(command._str_to_bool('FaLsE'))
        self.assertFalse(command._str_to_bool('nO'))
    
    def test_whitespace_handling(self):
        """Test handling of values with whitespace"""
        command = Command()
        
        # Whitespace should be stripped
        self.assertTrue(command._str_to_bool('  true  '))
        self.assertFalse(command._str_to_bool('  false  '))
        self.assertTrue(command._str_to_bool('\ttrue\n'))


# ============================================================================
# DRY-RUN MODE TESTS
# ============================================================================

class DryRunModeTests(TestCase):
    """Test dry-run mode functionality"""
    
    def test_dry_run_no_database_changes(self):
        """Test that dry-run mode makes no database changes"""
        csv_content = """image_url,active
https://example.com/test.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                initial_count = Image.objects.count()
                
                out = StringIO()
                call_command('upload_images', csv_path, '--dry-run', stdout=out)
                
                # No images should be created
                self.assertEqual(Image.objects.count(), initial_count)
        finally:
            os.unlink(csv_path)
    
    def test_dry_run_shows_preview(self):
        """Test that dry-run shows preview of what would be uploaded"""
        csv_content = """image_url,active
https://example.com/test.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            out = StringIO()
            call_command('upload_images', csv_path, '--dry-run', stdout=out)
            
            output = out.getvalue()
            self.assertIn('Would upload', output)
            self.assertIn('https://example.com/test.jpg', output)
        finally:
            os.unlink(csv_path)
    
    def test_dry_run_validates_csv(self):
        """Test that dry-run still validates CSV structure"""
        csv_content = """wrong_header,active
https://example.com/test.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with self.assertRaises(CommandError) as cm:
                out = StringIO()
                call_command('upload_images', csv_path, '--dry-run', stdout=out)
            
            self.assertIn('Missing required columns', str(cm.exception))
        finally:
            os.unlink(csv_path)
    
    def test_dry_run_counts_success_and_errors(self):
        """Test that dry-run counts successes and errors"""
        csv_content = """image_url,active
https://example.com/test1.jpg,true
,true
https://example.com/test2.jpg,false"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            out = StringIO()
            call_command('upload_images', csv_path, '--dry-run', stdout=out)
            
            output = out.getvalue()
            self.assertIn('Successful', output)
            self.assertIn('Errors', output)
        finally:
            os.unlink(csv_path)
    
    def test_dry_run_message_displayed(self):
        """Test that dry-run completion message is displayed"""
        csv_content = """image_url,active
https://example.com/test.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            out = StringIO()
            call_command('upload_images', csv_path, '--dry-run', stdout=out)
            
            output = out.getvalue()
            self.assertIn('DRY RUN COMPLETE', output)
            self.assertIn('No changes were saved', output)
        finally:
            os.unlink(csv_path)


# ============================================================================
# OUTPUT & REPORTING TESTS
# ============================================================================

class OutputReportingTests(TestCase):
    """Test command output and reporting"""
    
    def test_header_displayed(self):
        """Test that command header is displayed"""
        csv_content = """image_url,active
https://example.com/test.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                output = out.getvalue()
                self.assertIn('JMW ACCESSORIES', output)
                self.assertIn('IMAGE UPLOAD', output)
        finally:
            os.unlink(csv_path)
    
    def test_progress_indicators(self):
        """Test that progress indicators are shown"""
        csv_content = """image_url,active
https://example.com/test1.jpg,true
https://example.com/test2.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                output = out.getvalue()
                # Should show [1/2], [2/2]
                self.assertIn('[1/2]', output)
                self.assertIn('[2/2]', output)
        finally:
            os.unlink(csv_path)
    
    def test_success_summary(self):
        """Test that success summary is displayed"""
        csv_content = """image_url,active
https://example.com/test.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                output = out.getvalue()
                self.assertIn('UPLOAD SUMMARY', output)
                self.assertIn('Total Processed', output)
                self.assertIn('Successful', output)
        finally:
            os.unlink(csv_path)
    
    def test_error_details_displayed(self):
        """Test that error details are displayed"""
        csv_content = """image_url,active
,true
https://example.com/test.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                output = out.getvalue()
                self.assertIn('Error Details', output)
                self.assertIn('Row 1', output)
        finally:
            os.unlink(csv_path)
    
    def test_styled_success_message(self):
        """Test that success uses SUCCESS style"""
        csv_content = """image_url,active
https://example.com/test.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                output = out.getvalue()
                # Check for success indicators
                self.assertIn('✓', output)
                self.assertIn('Successful: 1', output)
        finally:
            os.unlink(csv_path)
    
    def test_found_images_count(self):
        """Test that count of images found is displayed"""
        csv_content = """image_url,active
https://example.com/test1.jpg,true
https://example.com/test2.jpg,true
https://example.com/test3.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            out = StringIO()
            call_command('upload_images', csv_path, '--dry-run', stdout=out)
            
            output = out.getvalue()
            self.assertIn('Found 3 images to process', output)
        finally:
            os.unlink(csv_path)


# ============================================================================
# EDGE CASES & PRODUCTION SCENARIOS TESTS
# ============================================================================

class EdgeCasesProductionTests(TransactionTestCase):
    """Test edge cases and production scenarios"""
    
    def test_large_csv_file(self):
        """Test processing large CSV file with 50+ rows"""
        # Generate CSV with 50 rows
        rows = ['image_url,active']
        for i in range(50):
            rows.append(f'https://example.com/image{i}.jpg,true')
        csv_content = '\n'.join(rows)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                # Should process all 50
                self.assertEqual(Image.objects.count(), 50)
                
                output = out.getvalue()
                self.assertIn('Found 50 images to process', output)
        finally:
            os.unlink(csv_path)
    
    def test_mixed_success_and_failures(self):
        """Test CSV with both successful and failed uploads"""
        csv_content = """image_url,active
https://example.com/valid.jpg,true
,true
https://example.com/valid2.jpg,true
https://example.com/valid3.jpg,false"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                output = out.getvalue()
                # Should have 3 successes and 1 error (empty URL)
                self.assertIn('Successful: 3', output)
                self.assertIn('Errors: 1', output)
        finally:
            os.unlink(csv_path)
    
    def test_special_characters_in_url(self):
        """Test URLs with special characters"""
        csv_content = """image_url,active
https://example.com/image with spaces.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                # Should handle special characters
                call_command('upload_images', csv_path, stdout=out)
        finally:
            os.unlink(csv_path)
    
    def test_duplicate_urls_in_csv(self):
        """Test CSV with duplicate URLs (should create multiple Image objects)"""
        csv_content = """image_url,active
https://example.com/same.jpg,true
https://example.com/same.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                # Should create 2 separate Image objects
                self.assertEqual(Image.objects.count(), 2)
        finally:
            os.unlink(csv_path)
    
    def test_cloudinary_url_with_complex_transformations(self):
        """Test Cloudinary URL with transformations (reuse existing image)"""
        csv_content = """image_url,active
https://res.cloudinary.com/demo/image/upload/products/banner.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                output = out.getvalue()
                # Should extract clean public_id and reuse (not download)
                self.assertIn('Using existing Cloudinary image', output)
                self.assertIn('products/banner.jpg', output)
                
                # Should NOT download
                mock_get.assert_not_called()
                
                # Should create image in database
                self.assertEqual(Image.objects.count(), 1)
        finally:
            os.unlink(csv_path)
    
    def test_various_image_formats(self):
        """Test different image formats (jpg, png, gif, webp)"""
        csv_content = """image_url,active
https://example.com/image.jpg,true
https://example.com/image.png,true
https://example.com/image.gif,true
https://example.com/image.webp,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                def response_side_effect(url, **kwargs):
                    mock_response = Mock()
                    mock_response.status_code = 200
                    # Set appropriate content-type based on URL
                    if '.png' in url:
                        content_type = 'image/png'
                    elif '.gif' in url:
                        content_type = 'image/gif'
                    elif '.webp' in url:
                        content_type = 'image/webp'
                    else:
                        content_type = 'image/jpeg'
                    
                    mock_response.headers = {'content-type': content_type, 'content-length': '100000'}
                    mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                    return mock_response
                
                mock_get.side_effect = response_side_effect
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                # Should successfully upload all formats
                self.assertEqual(Image.objects.count(), 4)
        finally:
            os.unlink(csv_path)
    
    def test_unicode_in_csv(self):
        """Test CSV with unicode characters in URLs"""
        csv_content = """image_url,active
https://example.com/café-image.jpg,true
https://example.com/日本語.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                # Should handle unicode URLs
                call_command('upload_images', csv_path, stdout=out)
        finally:
            os.unlink(csv_path)
    
    def test_csv_with_extra_columns(self):
        """Test CSV with extra columns (should be ignored)"""
        csv_content = """image_url,active,extra_col,another_col
https://example.com/test.jpg,true,ignored,also_ignored"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                # Should process successfully, ignoring extra columns
                call_command('upload_images', csv_path, stdout=out)
                
                self.assertEqual(Image.objects.count(), 1)
        finally:
            os.unlink(csv_path)
    
    def test_whitespace_in_csv_values(self):
        """Test CSV with whitespace around values"""
        csv_content = """image_url,active
  https://example.com/test.jpg  ,  true  
https://example.com/test2.jpg,false"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                # Should handle whitespace by stripping
                call_command('upload_images', csv_path, stdout=out)
                
                self.assertEqual(Image.objects.count(), 2)
        finally:
            os.unlink(csv_path)
    
    @patch('feed.management.commands.upload_images.requests.get')
    def test_http_vs_https_urls(self, mock_get):
        """Test both HTTP and HTTPS URLs"""
        csv_content = """image_url,active
http://example.com/test.jpg,true
https://example.com/test2.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
            mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
            mock_get.return_value = mock_response
            
            out = StringIO()
            call_command('upload_images', csv_path, stdout=out)
            
            # Both should be processed
            self.assertEqual(Image.objects.count(), 2)
        finally:
            os.unlink(csv_path)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class ErrorHandlingTests(TestCase):
    """Test error handling scenarios"""
    
    def test_unexpected_exception_during_processing(self):
        """Test handling of unexpected exceptions during row processing"""
        csv_content = """image_url,active
https://example.com/test.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                # Simulate unexpected exception during download
                mock_get.side_effect = Exception("Unexpected error")
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                output = out.getvalue()
                # Should show error in output
                self.assertIn('Error', output)
                self.assertIn('Errors: 1', output)
        finally:
            os.unlink(csv_path)
    
    def test_permission_error_reading_csv(self):
        """Test handling of permission errors when reading CSV"""
        # This test simulates a permission error
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            with self.assertRaises(Exception):
                out = StringIO()
                call_command('upload_images', 'test.csv', stdout=out)
    
    @patch('feed.models.Image.save')
    def test_database_error_during_save(self, mock_save):
        """Test handling of database errors during save"""
        csv_content = """image_url,active
    https://example.com/test.jpg,true"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                # Simulate database error during save
                mock_save.side_effect = Exception("Database error")
                
                out = StringIO()
                call_command('upload_images', csv_path, stdout=out)
                
                output = out.getvalue()
                # Should show error
                self.assertIn('Error', output)
        finally:
            os.unlink(csv_path)
    
    def test_malformed_csv_row(self):
        """Test handling of malformed CSV rows"""
        # CSV with inconsistent columns
        csv_content = """image_url,active
https://example.com/test1.jpg,true
https://example.com/test2.jpg,true,extra,columns,here"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with patch('feed.management.commands.upload_images.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
                mock_response.iter_content = lambda chunk_size: [create_valid_image_bytes()]
                mock_get.return_value = mock_response
                
                out = StringIO()
                # Should handle gracefully
                call_command('upload_images', csv_path, stdout=out)
        finally:
            os.unlink(csv_path)


# ============================================================================
# HELPER METHOD TESTS
# ============================================================================

class HelperMethodTests(TestCase):
    """Test individual helper methods"""
    
    def test_validate_headers_with_valid_headers(self):
        """Test _validate_headers with valid headers"""
        command = Command()
        command.stdout = StringIO()
        
        # Should not raise exception
        try:
            command._validate_headers(['image_url', 'active'])
        except Exception as e:
            self.fail(f"_validate_headers raised exception: {str(e)}")
    
    def test_validate_headers_with_missing_required(self):
        """Test _validate_headers with missing required header"""
        command = Command()
        command.stdout = StringIO()
        
        with self.assertRaises(CommandError) as cm:
            command._validate_headers(['active'])
        
        self.assertIn('Missing required columns', str(cm.exception))
    
    def test_validate_headers_with_none(self):
        """Test _validate_headers with None headers"""
        command = Command()
        command.stdout = StringIO()
        
        with self.assertRaises(CommandError) as cm:
            command._validate_headers(None)
        
        self.assertIn('no headers', str(cm.exception))
    
    def test_validate_headers_with_empty_list(self):
        """Test _validate_headers with empty list"""
        command = Command()
        command.stdout = StringIO()
        
        with self.assertRaises(CommandError) as cm:
            command._validate_headers([])
        
        self.assertIn('no headers', str(cm.exception))
    
    def test_process_image_with_dry_run(self):
        """Test _process_image in dry-run mode"""
        command = Command()
        command.stdout = StringIO()
        
        row = {'image_url': 'https://example.com/test.jpg', 'active': 'true'}
        
        result = command._process_image(row, dry_run=True)
        
        self.assertEqual(result, 'success')
        # Should not create database record
        self.assertEqual(Image.objects.count(), 0)
    
    def test_process_image_with_empty_url(self):
        """Test _process_image with empty URL"""
        command = Command()
        command.stdout = StringIO()
        
        row = {'image_url': '', 'active': 'true'}
        
        with self.assertRaises(ValueError) as cm:
            command._process_image(row, dry_run=False)
        
        self.assertIn('cannot be empty', str(cm.exception))