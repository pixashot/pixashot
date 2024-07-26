import pytest
from unittest.mock import Mock, patch, call
from src.capture_service import CaptureService
from src.exceptions import ScreenshotServiceException
from src.capture_request import CaptureRequest, Geolocation


@pytest.fixture
async def capture_service():
    service = CaptureService()
    await service.initialize(Mock())
    return service

@pytest.fixture
def mock_context():
    return Mock()

@pytest.fixture
def mock_page():
    return Mock()

@pytest.fixture
def mock_options():
    return CaptureRequest(
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
        delay_capture=0,
        geolocation=Geolocation(latitude=37.7749, longitude=-122.4194, accuracy=100)
    )

@pytest.mark.asyncio
async def test_capture_screenshot(capture_service, mock_context, mock_page, mock_options):
    with patch.object(capture_service.context_manager, 'get_context', return_value=mock_context):
        mock_context.new_page.return_value = mock_page

        await capture_service.capture_screenshot("output.png", mock_options)

        mock_page.goto.assert_called_with(
            "https://example.com",
            wait_until='domcontentloaded',
            timeout=5000.0
        )

        mock_page.screenshot.assert_called_once()

@pytest.mark.asyncio
async def test_capture_full_page_screenshot(capture_service, mock_context, mock_page, mock_options):
    with patch.object(capture_service.context_manager, 'get_context', return_value=mock_context):
        mock_context.new_page.return_value = mock_page
        mock_options.full_page = True
        mock_options.format = "png"
        mock_options.image_quality = None  # PNG doesn't use quality

        # Mock the evaluate method to return a valid height
        mock_page.evaluate.return_value = 10000

        await capture_service.capture_screenshot("output.png", mock_options)

        mock_page.screenshot.assert_called_with(
            path="output.png",
            full_page=True,
            quality=None,
            omit_background=False,
            type="png"
        )

@pytest.mark.asyncio
async def test_capture_element_screenshot(capture_service, mock_context, mock_page, mock_options):
    with patch.object(capture_service.context_manager, 'get_context', return_value=mock_context):
        mock_context.new_page.return_value = mock_page
        mock_options.selector = "#element"
        mock_element = Mock()
        mock_page.query_selector.return_value = mock_element

        await capture_service.capture_screenshot("output.png", mock_options)

        mock_page.query_selector.assert_called_with("#element")
        mock_element.screenshot.assert_called()

@pytest.mark.asyncio
async def test_capture_pdf(capture_service, mock_context, mock_page, mock_options):
    with patch.object(capture_service.context_manager, 'get_context', return_value=mock_context):
        mock_context.new_page.return_value = mock_page
        mock_options.format = "pdf"

        await capture_service.capture_screenshot("output.pdf", mock_options)

        mock_page.pdf.assert_called()

@pytest.mark.asyncio
async def test_perform_interactions(capture_service, mock_context, mock_page, mock_options):
    with patch.object(capture_service.context_manager, 'get_context', return_value=mock_context):
        mock_context.new_page.return_value = mock_page
        mock_options.interactions = [
            {"action": "click", "selector": "#button"},
            {"action": "type", "selector": "#input", "text": "Hello"}
        ]

        await capture_service.capture_screenshot("output.png", mock_options)

        mock_page.click.assert_called_with("#button")
        mock_page.fill.assert_called_with("#input", "Hello")

@pytest.fixture
def mock_ua_generator():
    with patch('src.capture_service.ua_generator') as mock_gen:
        mock_ua = Mock()
        mock_ua.headers.get.return_value = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        mock_gen.generate.return_value = mock_ua
        yield mock_gen

@pytest.mark.asyncio
async def test_user_agent_spoofing(capture_service, mock_context, mock_page, mock_options, mock_ua_generator):
    mock_options.use_random_user_agent = True
    mock_options.user_agent_device = 'desktop'
    mock_options.user_agent_platform = 'windows'
    mock_options.user_agent_browser = 'chrome'

    with patch.object(capture_service.context_manager, 'get_context', return_value=mock_context):
        mock_context.new_page.return_value = mock_page

        await capture_service.capture_screenshot("output.png", mock_options)

        # Verify that ua_generator was called with correct parameters
        mock_ua_generator.generate.assert_called_once_with(
            device='desktop',
            platform='windows',
            browser='chrome'
        )

        # Verify that the generated user agent was set on the page
        mock_page.set_extra_http_headers.assert_called_once_with({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        })

@pytest.mark.asyncio
async def test_user_agent_spoofing_disabled(capture_service, mock_context, mock_page, mock_options):
    mock_options.use_random_user_agent = False

    with patch.object(capture_service.context_manager, 'get_context', return_value=mock_context):
        mock_context.new_page.return_value = mock_page

        await capture_service.capture_screenshot("output.png", mock_options)

        # Verify that set_extra_http_headers was not called
        mock_page.set_extra_http_headers.assert_not_called()

@pytest.mark.asyncio
async def test_user_agent_spoofing_with_custom_headers(capture_service, mock_context, mock_page, mock_options, mock_ua_generator):
    mock_options.use_random_user_agent = True
    mock_options.user_agent_device = 'desktop'
    mock_options.user_agent_platform = 'windows'
    mock_options.user_agent_browser = 'chrome'
    mock_options.custom_headers = {'X-Custom-Header': 'CustomValue'}

    with patch.object(capture_service.context_manager, 'get_context', return_value=mock_context):
        mock_context.new_page.return_value = mock_page

        await capture_service.capture_screenshot("output.png", mock_options)

        # Verify that both the generated user agent and custom headers were set
        mock_page.set_extra_http_headers.assert_called_once_with({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Custom-Header': 'CustomValue'
        })