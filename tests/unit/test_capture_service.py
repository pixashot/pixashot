import pytest
from unittest.mock import Mock, patch, call
from src.capture_service import CaptureService
from src.exceptions import ScreenshotServiceException
from src.capture_request import Geolocation


@pytest.fixture
def capture_service():
    return CaptureService()

@pytest.fixture
def mock_playwright():
    return Mock()

@pytest.fixture
def mock_context():
    return Mock()

@pytest.fixture
def mock_page():
    return Mock()

@pytest.fixture
def mock_options():
    options = Mock(
        url="https://example.com",
        format="png",
        full_page=False,
        selector=None,
        wait_for_timeout=5000,
        image_quality=80,
        omit_background=False,
        window_width=1280,
        window_height=720,
        pixel_density=2.0,
        geolocation=Geolocation(latitude=37.7749, longitude=-122.4194, accuracy=100)
    )
    return options

@patch('src.capture_service.sync_playwright')
def test_capture_screenshot(mock_sync_playwright, capture_service, mock_playwright, mock_context, mock_page, mock_options):
    mock_sync_playwright.return_value.__enter__.return_value = mock_playwright
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    mock_set_geolocation = Mock()

    def mock_prepare_page(page, options):
        if options.geolocation:
            mock_set_geolocation(page, options.geolocation)

    with patch.object(capture_service.browser_controller, 'prepare_page', side_effect=mock_prepare_page):
        with patch.object(capture_service.browser_controller.geolocation_controller, 'set_geolocation', mock_set_geolocation):
            capture_service.capture_screenshot("output.png", mock_options)

    mock_page.goto.assert_called_with(
        "https://example.com",
        wait_until='domcontentloaded',
        timeout=5000.0
    )

    mock_set_geolocation.assert_called_once_with(mock_page, mock_options.geolocation)

    mock_page.screenshot.assert_called_once()


@patch('src.capture_service.sync_playwright')
@patch('PIL.Image.open')
@patch('src.capture_service.CaptureService._crop_screenshot_if_necessary')
def test_capture_full_page_screenshot(mock_crop, mock_image_open, mock_sync_playwright, capture_service, mock_playwright, mock_context, mock_page, mock_options):
    mock_sync_playwright.return_value.__enter__.return_value = mock_playwright
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_options.full_page = True
    mock_options.window_width = 1280
    mock_options.window_height = 720
    mock_options.pixel_density = 2.0
    mock_options.format = "png"
    mock_options.image_quality = None  # PNG doesn't use quality

    # Mock the evaluate method to return a valid height
    mock_page.evaluate.return_value = 10000

    # Create a mock image
    mock_image = Mock()
    mock_image.width = 2560  # This is greater than window_width * pixel_density
    mock_image.height = 10000
    mock_image_open.return_value.__enter__.return_value = mock_image

    with patch.object(capture_service.browser_controller.screenshot_controller, 'MAX_VIEWPORT_HEIGHT', 20000):
        capture_service.capture_screenshot("output.png", mock_options)

    mock_page.screenshot.assert_called_with(
        path="output.png",
        full_page=True,
        quality=None,
        omit_background=False,
        type="png"
    )

    # Assert that _crop_screenshot_if_necessary was called
    mock_crop.assert_called_once_with("output.png", mock_options.window_width, mock_options.pixel_density)

    # Test with JPEG format
    mock_options.format = "jpeg"
    mock_options.image_quality = 80

    capture_service.capture_screenshot("output.jpg", mock_options)

    mock_page.screenshot.assert_called_with(
        path="output.jpg",
        full_page=True,
        quality=80,
        omit_background=False,
        type="jpeg"
    )


@patch('src.capture_service.sync_playwright')
def test_capture_element_screenshot(mock_sync_playwright, capture_service, mock_playwright, mock_context, mock_page,
                                    mock_options):
    mock_sync_playwright.return_value.__enter__.return_value = mock_playwright
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_options.selector = "#element"
    mock_element = Mock()
    mock_page.query_selector.return_value = mock_element

    capture_service.capture_screenshot("output.png", mock_options)

    mock_page.query_selector.assert_called_with("#element")
    mock_element.screenshot.assert_called()


@patch('src.capture_service.sync_playwright')
def test_capture_pdf(mock_sync_playwright, capture_service, mock_playwright, mock_context, mock_page, mock_options):
    mock_sync_playwright.return_value.__enter__.return_value = mock_playwright
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_options.format = "pdf"

    capture_service.capture_screenshot("output.pdf", mock_options)

    mock_page.pdf.assert_called()


@patch('src.capture_service.sync_playwright')
@patch('src.capture_service.time.sleep')
def test_capture_screenshot_exception(mock_sleep, mock_sync_playwright):
    capture_service = CaptureService()

    mock_playwright = Mock()
    mock_context = Mock()
    mock_page = Mock()
    mock_options = Mock()

    mock_sync_playwright.return_value.__enter__.return_value = mock_playwright
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    # Mock the browser_controller
    mock_browser_controller = Mock()
    mock_browser_controller.goto_with_timeout.side_effect = Exception("Navigation failed")
    capture_service.browser_controller = mock_browser_controller

    # Set the url attribute on the mock_options
    mock_options.url = "https://example.com"

    # Set a default value for the wait_for_timeout attribute
    mock_options.wait_for_timeout = 5000

    with pytest.raises(ScreenshotServiceException) as excinfo:
        capture_service.capture_screenshot("output.png", mock_options)

    # Print debugging information
    print(f"Exception message: {str(excinfo.value)}")
    print(f"goto_with_timeout call count: {mock_browser_controller.goto_with_timeout.call_count}")
    print(f"sleep call count: {mock_sleep.call_count}")

    # Check that the exception message contains the expected text
    assert "Failed to capture after 3 attempts: Navigation failed" in str(excinfo.value)

    # Check that goto_with_timeout was called 4 times (initial attempt + 3 retries)
    assert mock_browser_controller.goto_with_timeout.call_count == 4

    # Check that sleep was called 3 times (between retries)
    assert mock_sleep.call_count == 3

    # Check that the last call to goto_with_timeout had the correct arguments
    mock_browser_controller.goto_with_timeout.assert_called_with(mock_page, "https://example.com")