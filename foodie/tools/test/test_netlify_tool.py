import unittest
from unittest.mock import patch, Mock, mock_open
from foodie.tools.netlify_tool import upload_to_netlify, create_netlify_map


class TestNetlifyTool(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.test_html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Map</title></head>
        <body><h1>Test Map Content</h1></body>
        </html>
        """

    @patch('foodie.tools.netlify_tool.os.unlink')
    @patch('foodie.tools.netlify_tool.requests.post')
    @patch('foodie.tools.netlify_tool.os.path.exists')
    @patch('foodie.tools.netlify_tool.tempfile.NamedTemporaryFile')
    @patch('foodie.tools.netlify_tool.zipfile.ZipFile')
    @patch('builtins.open', new_callable=mock_open, read_data="<html>Test</html>")
    def test_upload_to_netlify_success_anonymous(self, mock_file_open, mock_zipfile, mock_tempfile, mock_exists, mock_post, mock_unlink):
        """Test successful anonymous upload to Netlify"""

        # Mock file exists check
        mock_exists.return_value = True

        # Mock tempfile.NamedTemporaryFile context manager
        mock_temp_obj = Mock()
        mock_temp_obj.name = '/tmp/test123.zip'
        mock_tempfile.return_value.__enter__.return_value = mock_temp_obj
        mock_tempfile.return_value.__exit__.return_value = None

        # Mock zipfile.ZipFile context manager
        mock_zip_obj = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_obj
        mock_zipfile.return_value.__exit__.return_value = None

        # Mock the second open() call for reading zip file
        mock_zip_file_data = Mock()
        mock_zip_file_data.read.return_value = b'fake zip content'
        mock_zip_file_data.seek = Mock()

        # Configure open to behave differently based on call
        original_open = mock_file_open.return_value
        def open_side_effect(*args, **kwargs):
            # If opening in binary read mode (for zip file)
            if len(args) > 1 and 'rb' in args[1]:
                zip_file_mock = Mock()
                zip_file_mock.__enter__.return_value = mock_zip_file_data
                zip_file_mock.__exit__.return_value = None
                return zip_file_mock
            # Otherwise return the original mock
            return original_open

        mock_file_open.side_effect = open_side_effect

        # Mock successful Netlify API response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'test-site-123',
            'name': 'amazing-site-456',
            'ssl_url': 'https://amazing-site-456.netlify.app',
            'url': 'http://amazing-site-456.netlify.app',
            'admin_url': 'https://app.netlify.com/sites/amazing-site-456',
            'deploy_url': 'https://deploy-preview-1--amazing-site-456.netlify.app'
        }
        mock_post.return_value = mock_response

        # Call the function under test
        result = upload_to_netlify('/path/to/test.html')

        # Assertions
        self.assertTrue(result['success'], f"Expected success=True, got result: {result}")
        self.assertEqual(result['url'], 'https://amazing-site-456.netlify.app')
        self.assertEqual(result['site_id'], 'test-site-123')
        self.assertEqual(result['expires'], '24 hours')
        self.assertIn('deployed successfully', result['message'])

        # Verify mocks were called correctly
        mock_exists.assert_called_once_with('/path/to/test.html')
        mock_tempfile.assert_called_once()
        mock_zipfile.assert_called_once_with('/tmp/test123.zip', 'w', zipfile.ZIP_DEFLATED)
        mock_zip_obj.write.assert_called_once_with('/path/to/test.html', 'index.html')
        mock_post.assert_called_once()
        mock_unlink.assert_called_once_with('/tmp/test123.zip')

        # Verify API call details
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], 'https://api.netlify.com/api/v1/sites')
        self.assertEqual(call_args[1]['headers']['Content-Type'], 'application/zip')

    @patch('foodie.tools.netlify_tool.requests.post')
    @patch('foodie.tools.netlify_tool.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="<html>Test</html>")
    @patch('foodie.tools.netlify_tool.zipfile.ZipFile')
    @patch('foodie.tools.netlify_tool.tempfile.NamedTemporaryFile')
    def test_upload_to_netlify_success_authenticated(self, mock_temp, mock_zip, mock_file, mock_exists, mock_post):
        """Test successful authenticated upload to Netlify with custom site name"""

        # Mock file exists check
        mock_exists.return_value = True

        # Mock temporary file
        mock_temp_file = Mock()
        mock_temp_file.name = '/tmp/test.zip'
        mock_temp.__enter__.return_value = mock_temp_file

        # Mock zip file
        mock_zip_instance = Mock()
        mock_zip.return_value.__enter__.return_value = mock_zip_instance

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'custom-site-id-789',
            'name': 'my-custom-foodie-site',
            'ssl_url': 'https://my-custom-foodie-site.netlify.app',
            'url': 'http://my-custom-foodie-site.netlify.app',
            'admin_url': 'https://app.netlify.com/sites/my-custom-foodie-site'
        }
        mock_post.return_value = mock_response

        # Test authenticated upload with custom site name
        result = upload_to_netlify(
            '/path/to/test.html',
            site_name='my-custom-foodie-site',
            access_token='netlify_token_123'
        )

        # Verify success
        self.assertTrue(result['success'])
        self.assertEqual(result['url'], 'https://my-custom-foodie-site.netlify.app')
        self.assertEqual(result['site_name'], 'my-custom-foodie-site')
        self.assertEqual(result['expires'], 'permanent')

        # Verify API was called with authentication
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('Authorization', call_args[1]['headers'])
        self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer netlify_token_123')

    @patch('foodie.tools.netlify_tool.os.path.exists')
    def test_upload_to_netlify_file_not_found(self, mock_exists):
        """Test error handling when local file doesn't exist"""

        # Mock file doesn't exist
        mock_exists.return_value = False

        # Test the upload
        result = upload_to_netlify('/nonexistent/file.html')

        # Verify error handling
        self.assertFalse(result['success'])
        self.assertIn('Local file not found', result['error'])

    @patch('foodie.tools.netlify_tool.requests.post')
    @patch('foodie.tools.netlify_tool.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="<html>Test</html>")
    @patch('foodie.tools.netlify_tool.zipfile.ZipFile')
    @patch('foodie.tools.netlify_tool.tempfile.NamedTemporaryFile')
    def test_upload_to_netlify_api_error(self, mock_temp, mock_zip, mock_file, mock_exists, mock_post):
        """Test error handling when Netlify API returns an error"""

        # Mock file exists check
        mock_exists.return_value = True

        # Mock temporary file
        mock_temp_file = Mock()
        mock_temp_file.name = '/tmp/test.zip'
        mock_temp.__enter__.return_value = mock_temp_file

        # Mock zip file
        mock_zip_instance = Mock()
        mock_zip.return_value.__enter__.return_value = mock_zip_instance

        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request: Invalid zip file'
        mock_post.return_value = mock_response

        # Test the upload
        result = upload_to_netlify('/path/to/test.html')

        # Verify error handling
        self.assertFalse(result['success'])
        self.assertIn('Netlify deployment failed: HTTP 400', result['error'])
        self.assertIn('Bad Request', result['details'])

    @patch('foodie.tools.netlify_tool.upload_to_netlify')
    @patch('foodie.tools.netlify_tool.folium.Map')
    @patch('foodie.tools.netlify_tool.folium.Marker')
    @patch('foodie.tools.map_tool.address_to_coordinates')
    @patch('foodie.tools.netlify_tool.os.path.abspath')
    @patch('foodie.tools.netlify_tool.os.remove')
    def test_create_netlify_map_success(self, mock_remove, mock_abspath, mock_geocode, mock_marker, mock_map, mock_upload):
        """Test successful creation and deployment of map to Netlify"""

        # Mock geocoding results
        mock_geocode.side_effect = [
            (40.7580, -73.9855),  # Times Square
            (40.7812, -73.9665),  # Central Park
            (40.7488, -73.9857),  # Empire State Building
        ]

        # Mock map creation
        mock_map_instance = Mock()
        mock_map.return_value = mock_map_instance

        # Mock marker creation
        mock_marker_instance = Mock()
        mock_marker.return_value = mock_marker_instance

        # Mock file path
        mock_abspath.return_value = '/tmp/netlify_map.html'

        # Mock successful Netlify upload
        mock_upload.return_value = {
            'success': True,
            'url': 'https://wonderful-map-123.netlify.app',
            'site_id': 'site-123',
            'expires': '24 hours'
        }

        # Test map creation
        addresses = "Times Square, New York, NY | Central Park, New York, NY | Empire State Building, New York, NY"
        result = create_netlify_map(addresses)

        # Verify success
        self.assertIn('content', result)
        content = result['content'][0]['text']
        self.assertIn('Map Deployed to Netlify!', content)
        self.assertIn('https://wonderful-map-123.netlify.app', content)
        self.assertIn('Locations: 3 mapped', content)
        self.assertIn('Expires: 24 hours', content)

        # Verify geocoding was called for each address
        self.assertEqual(mock_geocode.call_count, 3)

        # Verify map was created
        mock_map.assert_called_once()
        map_call_args = mock_map.call_args[1]
        self.assertIn('location', map_call_args)
        self.assertEqual(map_call_args['zoom_start'], 12)

        # Verify markers were added
        self.assertEqual(mock_marker.call_count, 3)

        # Verify map was saved and uploaded
        mock_map_instance.save.assert_called_once()
        mock_upload.assert_called_once()

        # Verify cleanup
        mock_remove.assert_called_once_with('/tmp/netlify_map.html')

    @patch('foodie.tools.map_tool.address_to_coordinates')
    def test_create_netlify_map_no_valid_addresses(self, mock_geocode):
        """Test error handling when no addresses can be geocoded"""

        # Mock failed geocoding for all addresses
        mock_geocode.return_value = (None, None)

        # Test map creation with invalid addresses
        addresses = "Invalid Address 1 | Invalid Address 2"
        result = create_netlify_map(addresses)

        # Verify error handling
        self.assertIn('content', result)
        content = result['content'][0]['text']
        self.assertIn('[error] No valid addresses found!', content)

    @patch('foodie.tools.netlify_tool.upload_to_netlify')
    @patch('foodie.tools.netlify_tool.folium.Map')
    @patch('foodie.tools.map_tool.address_to_coordinates')
    def test_create_netlify_map_upload_failure(self, mock_geocode, mock_map, mock_upload):
        """Test error handling when Netlify upload fails"""

        # Mock successful geocoding
        mock_geocode.return_value = (40.7580, -73.9855)

        # Mock map creation
        mock_map_instance = Mock()
        mock_map.return_value = mock_map_instance

        # Mock failed Netlify upload
        mock_upload.return_value = {
            'success': False,
            'error': 'Network connection failed'
        }

        # Test map creation
        addresses = "Times Square, New York, NY"
        result = create_netlify_map(addresses)

        # Verify error handling
        self.assertIn('content', result)
        content = result['content'][0]['text']
        self.assertIn('[error] Netlify deployment failed', content)
        self.assertIn('Network connection failed', content)

    def test_run_real_addresses(self):
        """Integration test with real addresses (for manual testing)"""
        # This test is for manual verification - it will actually call the geocoding API
        # Uncomment and run manually when you want to test with real data

        # addresses = "Golden Gate Bridge, San Francisco, CA | Alcatraz Island, San Francisco, CA"
        # result = create_netlify_map(addresses, file_name="test_netlify_map")
        # print("Real test result:", result)
        pass

    def test_run_johns_creek_addresses(self):
        """Integration test with Johns Creek addresses (for manual testing)"""
        # This test matches your existing test pattern
        # Uncomment and run manually when you want to test with real data

        # addresses = ("10305 Medlock Bridge Rd, Johns Creek, GA|" +
        #             "10970 State Bridge Rd, Johns Creek, GA|" +
        #             "6955 McGinnis Ferry Rd, Johns Creek, GA")
        # result = create_netlify_map(addresses, file_name="test_netlify_johns_creek")
        # print("Johns Creek test result:", result)
        pass


if __name__ == '__main__':
    unittest.main()
