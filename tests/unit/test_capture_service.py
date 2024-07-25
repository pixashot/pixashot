import pytest
from unittest.mock import Mock, patch, call
from src.capture_service import CaptureService
from src.exceptions import ScreenshotServiceException

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
        geolocation={
            "latitude": 37.7749,
            "longitude": -122.4194,
            "accuracy": 100
        }
    )
    return options

@patch('src.capture_service.sync_playwright')
def test_capture_screenshot(mock_sync_playwright, capture_service, mock_playwright, mock_context, mock_page, mock_options):
    mock_sync_playwright.return_value.__enter__.return_value = mock_playwright
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    mock_set_geolocation = Mock()

    def mock_prepare_page(page, options):
        print(f"Inside mock_prepare_page")
        print(f"options.geolocation: {options.geolocation}")
        if options.geolocation:
            print("Calling set_geolocation")
            mock_set_geolocation(page, options.geolocation)

    with patch.object(capture_service.browser_controller, 'prepare_page', side_effect=mock_prepare_page):
        with patch.object(capture_service.browser_controller.geolocation_controller, 'set_geolocation', mock_set_geolocation):
            capture_service.capture_screenshot("output.png", mock_options)

    print(f"mock_set_geolocation.call_count: {mock_set_geolocation.call_count}")
    print(f"mock_set_geolocation.call_args_list: {mock_set_geolocation.call_args_list}")

    # Assert that goto was called
    mock_page.goto.assert_called_with(
        "https://example.com",
        wait_until='domcontentloaded',
        timeout=5000.0
    )

    # Assert that set_geolocation was called
    mock_set_geolocation.assert_called_once_with(mock_page, mock_options.geolocation)

    # Assert that screenshot was called
    mock_page.screenshot.assert_called_once()


@patch('src.capture_service.sync_playwright')
def test_capture_full_page_screenshot(mock_sync_playwright, capture_service, mock_playwright, mock_context, mock_page,
                                      mock_options):
    mock_sync_playwright.return_value.__enter__.return_value = mock_playwright
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_options.full_page = True

    capture_service.capture_screenshot("output.png", mock_options)

    mock_page.screenshot.assert_called_with(
        path="output.png",
        full_page=True,
        quality=80,
        omit_background=False,
        type="png"
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
def test_capture_screenshot_exception(mock_sync_playwright, capture_service, mock_playwright, mock_context, mock_page,
                                      mock_options):
    mock_sync_playwright.return_value.__enter__.return_value = mock_playwright
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.goto.side_effect = Exception("Navigation failed")

    with pytest.raises(ScreenshotServiceException):
        capture_service.capture_screenshot("output.png", mock_options)
