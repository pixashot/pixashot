import sys
import os
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

import cProfile
import pstats
import io
from app import app
from capture_service import CaptureService
from capture_request import CaptureRequest


def profile_screenshot_capture():
    # Initialize the capture service
    capture_service = CaptureService()

    # Test data
    capture_options = CaptureRequest(
        url="https://siteorigin.com",
        format="png",
        window_width=1280,
        window_height=720,
        full_page=False
    )

    # Create a temporary file path for the screenshot
    temp_file_path = project_root / 'temp_screenshot.png'

    profiler = cProfile.Profile()
    profiler.enable()

    # Perform the screenshot capture
    capture_service.capture_screenshot(str(temp_file_path), capture_options)

    profiler.disable()

    # Print the profiling results
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    stats.print_stats()

    print(s.getvalue())

    # Clean up the temporary file
    if temp_file_path.exists():
        os.remove(temp_file_path)


if __name__ == '__main__':
    profile_screenshot_capture()
