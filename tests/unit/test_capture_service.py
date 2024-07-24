import pytest
from unittest.mock import Mock, patch
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
    return Mock(
        url="https://example.com",
        format="png",
        full_page=False,
        selector=None,
        wait_for_timeout=5000,
        image_quality=80,
        omit_background=False
    )

@patch('src.capture_service.sync_playwright')
def test_capture_screenshot(mock_sync_playwright, capture_service, mock_playwright, mock_context, mock_page, mock_options):
    mock_sync_playwright.return_value.__enter__.return_value = mock_playwright
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    capture_service.capture_screenshot("output.png", mock_options)

    mock_page.goto.assert_called_with("https://example.com")
    mock_page.screenshot.assert_called()

@patch('src.capture_service.sync_playwright')
def test_capture_full_page_screenshot(mock_sync_playwright, capture_service, mock_playwright, mock_context, mock_page, mock_options):
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
def test_capture_element_screenshot(mock_sync_playwright, capture_service, mock_playwright, mock_context, mock_page, mock_options):
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
def test_capture_screenshot_exception(mock_sync_playwright, capture_service, mock_playwright, mock_context, mock_page, mock_options):
    mock_sync_playwright.return_value.__enter__.return_value = mock_playwright
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.goto.side_effect = Exception("Navigation failed")

    with pytest.raises(ScreenshotServiceException):
        capture_service.capture_screenshot("output.png", mock_options)