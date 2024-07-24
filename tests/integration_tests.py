import unittest
import json
import os
import tempfile
from src.app import app
from src.capture_service import CaptureService


class TestPixashotIntegration(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Ensure the ScreenshotCaptureService is initialized
        app.capture_service = CaptureService()

    def test_screenshot_endpoint(self):
        # Test data
        test_data = {
            "url": "https://example.com",
            "format": "png",
            "window_width": 1280,
            "window_height": 720,
            "full_page": False
        }

        # Make a POST request to the /capture endpoint
        response = self.app.post('/capture',
                                 data=json.dumps(test_data),
                                 content_type='application/json')

        # Check if the request was successful
        self.assertEqual(response.status_code, 200)

        # Check if the response is a PNG image
        self.assertEqual(response.headers['Content-Type'], 'image/png')

        # Check if the response has content
        self.assertGreater(len(response.data), 0)

    def test_screenshot_endpoint_with_html_content(self):
        # Test data with HTML content instead of URL
        test_data = {
            "html_content": "<html><body><h1>Test Page</h1></body></html>",
            "format": "jpeg",
            "window_width": 800,
            "window_height": 600,
            "full_page": True
        }

        # Make a POST request to the /capture endpoint
        response = self.app.post('/capture',
                                 data=json.dumps(test_data),
                                 content_type='application/json')

        # Check if the request was successful
        self.assertEqual(response.status_code, 200)

        # Check if the response is a JPEG image
        self.assertEqual(response.headers['Content-Type'], 'image/jpeg')

        # Check if the response has content
        self.assertGreater(len(response.data), 0)

    def test_screenshot_endpoint_with_invalid_data(self):
        # Test data with missing required fields
        test_data = {
            "format": "png"
        }

        # Make a POST request to the /capture endpoint
        response = self.app.post('/capture',
                                 data=json.dumps(test_data),
                                 content_type='application/json')

        # Check if the request was unsuccessful
        self.assertEqual(response.status_code, 400)

        # Check if the response contains an error message
        response_data = json.loads(response.data)
        self.assertIn('error', response_data['status'])
        self.assertIn('message', response_data)

    def test_screenshot_endpoint_with_pdf_format(self):
        # Test data for PDF capture
        test_data = {
            "url": "https://example.com",
            "format": "pdf",
            "window_width": 1280,
            "window_height": 720,
            "full_page": True,
            "pdf_print_background": True,
            "pdf_scale": 1.0,
            "pdf_format": "A4"
        }

        # Make a POST request to the /capture endpoint
        response = self.app.post('/capture',
                                 data=json.dumps(test_data),
                                 content_type='application/json')

        # Check if the request was successful
        self.assertEqual(response.status_code, 200)

        # Check if the response is a PDF
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')

        # Check if the response has content
        self.assertGreater(len(response.data), 0)

        # Optionally, save the PDF to a temporary file and check its validity
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(response.data)

        # Clean up the temporary file
        os.unlink(temp_file.name)


if __name__ == '__main__':
    unittest.main()
