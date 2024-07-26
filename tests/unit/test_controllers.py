import pytest
from unittest.mock import Mock, patch, mock_open, call
from src.controllers.main_controller import MainBrowserController
from src.controllers.interaction_controller import InteractionController
from src.controllers.content_controller import ContentController
from src.controllers.screenshot_controller import ScreenshotController
from src.controllers.geolocation_controller import GeolocationController
from src.exceptions import TimeoutException, JavaScriptExecutionException, InteractionException
from src.capture_request import CaptureRequest, Geolocation, InteractionStep, WaitForOption

@pytest.fixture
def mock_page():
    return Mock()

@pytest.fixture
def mock_options():
    return CaptureRequest(
        url="https://example.com",
        dark_mode=False,
        geolocation=None,
        wait_for_timeout=5000,
        custom_js=None,
        wait_for_selector=None,
        wait_for_network="idle",
        wait_for_animation=False
    )

@pytest.mark.asyncio
async def test_main_controller_prepare_page(mock_page, mock_options):
    controller = MainBrowserController()
    await controller.prepare_page(mock_page, mock_options)

    mock_page.evaluate.assert_called()
    mock_page.wait_for_timeout.assert_called_with(500)

@pytest.mark.asyncio
async def test_main_controller_prepare_page_with_dark_mode(mock_page, mock_options):
    mock_options.dark_mode = True
    controller = MainBrowserController()
    await controller.prepare_page(mock_page, mock_options)

    controller.content_controller.apply_dark_mode.assert_called_once_with(mock_page)

@pytest.mark.asyncio
async def test_main_controller_prepare_page_with_geolocation(mock_page, mock_options):
    mock_options.geolocation = Geolocation(latitude=37.7749, longitude=-122.4194, accuracy=100)
    controller = MainBrowserController()
    await controller.prepare_page(mock_page, mock_options)

    controller.geolocation_controller.set_geolocation.assert_called_once_with(mock_page, mock_options.geolocation)

@pytest.mark.asyncio
async def test_main_controller_prepare_page_with_custom_js(mock_page, mock_options):
    mock_options.custom_js = "console.log('Hello, World!');"
    controller = MainBrowserController()
    await controller.prepare_page(mock_page, mock_options)

    controller.content_controller.execute_custom_js.assert_called_once_with(mock_page, mock_options.custom_js)

@pytest.mark.asyncio
async def test_interaction_controller_perform_interactions(mock_page):
    controller = InteractionController()
    interactions = [
        InteractionStep(action="click", selector="#button"),
        InteractionStep(action="type", selector="#input", text="Hello"),
        InteractionStep(action="hover", selector="#element"),
        InteractionStep(action="scroll", x=0, y=100),
        InteractionStep(action="wait_for", wait_for=WaitForOption(type="network_idle", value=5000))
    ]

    await controller.perform_interactions(mock_page, interactions)

    mock_page.click.assert_called_once_with("#button")
    mock_page.fill.assert_called_once_with("#input", "Hello")
    mock_page.hover.assert_called_once_with("#element")
    mock_page.evaluate.assert_called_once_with("window.scrollTo(0, 100)")
    mock_page.wait_for_load_state.assert_called_once_with('networkidle', timeout=5000)

@pytest.mark.asyncio
async def test_interaction_controller_perform_interactions_exception(mock_page):
    controller = InteractionController()
    interactions = [
        InteractionStep(action="click", selector="#non-existent-button")
    ]
    mock_page.click.side_effect = Exception("Element not found")

    with pytest.raises(InteractionException):
        await controller.perform_interactions(mock_page, interactions)

@pytest.mark.asyncio
async def test_content_controller_wait_for_dynamic_content(mock_page):
    controller = ContentController()
    with patch('builtins.open', mock_open(read_data='dynamic_content_detector_script')):
        await controller.wait_for_dynamic_content(mock_page)

    mock_page.evaluate.assert_called_with('dynamic_content_detector_script')
    mock_page.evaluate.assert_called_with('detectDynamicContentLoading(1000, 5)')

@pytest.mark.asyncio
async def test_content_controller_apply_dark_mode(mock_page):
    controller = ContentController()
    with patch('builtins.open', mock_open(read_data='dark_mode_script')):
        await controller.apply_dark_mode(mock_page)

    mock_page.evaluate.assert_called_with('dark_mode_script')

@pytest.mark.asyncio
async def test_content_controller_prevent_horizontal_overflow(mock_page):
    controller = ContentController()
    await controller.prevent_horizontal_overflow(mock_page)

    mock_page.evaluate.assert_called_once()

@pytest.mark.asyncio
async def test_screenshot_controller_prepare_for_full_page_screenshot(mock_page):
    controller = ScreenshotController()

    mock_page.evaluate.side_effect = [None, 10000, None]
    mock_page.wait_for_load_state.return_value = None
    mock_page.set_viewport_size.return_value = None
    mock_page.wait_for_timeout.return_value = None

    await controller.prepare_for_full_page_screenshot(mock_page, 1280)

    assert mock_page.evaluate.call_count == 3
    mock_page.evaluate.assert_has_calls([
        call('window.scrollTo(0, document.body.scrollHeight)'),
        call('document.body.scrollHeight'),
        call('window.scrollTo(0, 0)')
    ])
    mock_page.wait_for_load_state.assert_called_with('networkidle', timeout=controller.NETWORK_IDLE_TIMEOUT_MS)
    mock_page.set_viewport_size.assert_called_with({'width': 1280, 'height': 10000})
    mock_page.wait_for_timeout.assert_called_with(controller.SCROLL_PAUSE_MS)

@pytest.mark.asyncio
async def test_screenshot_controller_prepare_for_viewport_screenshot(mock_page):
    controller = ScreenshotController()
    await controller.prepare_for_viewport_screenshot(mock_page, 1280, 720)

    mock_page.set_viewport_size.assert_called_with({'width': 1280, 'height': 720})
    mock_page.wait_for_load_state.assert_called_with('networkidle', timeout=controller.NETWORK_IDLE_TIMEOUT_MS)
    mock_page.evaluate.assert_called_with('window.scrollTo(0, 0)')
    mock_page.wait_for_timeout.assert_called_with(controller.SCROLL_PAUSE_MS)

@pytest.mark.asyncio
async def test_geolocation_controller_set_geolocation(mock_page):
    controller = GeolocationController()
    location = Geolocation(latitude=37.7749, longitude=-122.4194, accuracy=100)
    await controller.set_geolocation(mock_page, location)

    mock_page.context.grant_permissions.assert_called_with(['geolocation'])
    mock_page.context.set_geolocation.assert_called_with(location.dict())
    mock_page.add_init_script.assert_called_once()

@pytest.mark.asyncio
async def test_geolocation_controller_set_geolocation_none(mock_page):
    controller = GeolocationController()
    await controller.set_geolocation(mock_page, None)

    mock_page.context.grant_permissions.assert_not_called()
    mock_page.context.set_geolocation.assert_not_called()
    mock_page.add_init_script.assert_not_called()