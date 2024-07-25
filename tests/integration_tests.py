import cProfile
import pstats
import io
import unittest
import json
from src.app import app
from src.capture_service import CaptureService


def profile_tests():
    profiler = cProfile.Profile()
    profiler.enable()

    # Run the tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPixashotIntegration)
    unittest.TextTestRunner(verbosity=2).run(suite)

    profiler.disable()

    # Print the profiling results
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    stats.print_stats()

    print(s.getvalue())


class TestPixashotIntegration(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
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

    # Add more test methods as needed


if __name__ == '__main__':
    profile_tests()