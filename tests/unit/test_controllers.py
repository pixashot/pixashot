import pytest
from unittest.mock import Mock, patch, mock_open
from src.controllers.main_controller import MainBrowserController
from src.controllers.navigation_controller import NavigationController
from src.controllers.content_controller import ContentController
from src.controllers.screenshot_controller import ScreenshotController
from src.controllers.geolocation_controller import GeolocationController
from src.exceptions import TimeoutException, JavaScriptExecutionException


@pytest.fixture
def mock_page():
    return Mock()


@pytest.fixture
def mock_options():
    return Mock(
        dark_mode=False,
        geolocation=None,
        wait_for_timeout=5000,
        custom_js=None,
        wait_for_selector=None
    )


def test_main_controller_prepare_page(mock_page, mock_options):
    controller = MainBrowserController()
    controller.prepare_page(mock_page, mock_options)

    mock_page.evaluate.assert_called()
    mock_page.wait_for_timeout.assert_called_with(500)


def test_navigation_controller_goto_with_timeout(mock_page):
    controller = NavigationController()
    controller.goto_with_timeout(mock_page, "https://example.com", 5.0)

    mock_page.goto.assert_called_with("https://example.com", wait_until='domcontentloaded', timeout=5000)


def test_navigation_controller_goto_with_timeout_exception(mock_page):
    controller = NavigationController()
    mock_page.goto.side_effect = TimeoutException("Navigation timeout")

    with pytest.raises(TimeoutException):
        controller.goto_with_timeout(mock_page, "https://example.com", 5.0)


def test_content_controller_inject_scripts(mock_page):
    with patch('builtins.open', mock_open(read_data='test_script')):
        controller = ContentController()
        controller.inject_scripts(mock_page)

        mock_page.evaluate.assert_called_with('test_script')


def test_content_controller_apply_dark_mode(mock_page):
    with patch('builtins.open', mock_open(read_data='dark_mode_script')):
        controller = ContentController()
        controller.apply_dark_mode(mock_page)

        mock_page.evaluate.assert_called_with('dark_mode_script')


def test_screenshot_controller_prepare_for_full_page_screenshot(mock_page):
    controller = ScreenshotController()
    controller.prepare_for_full_page_screenshot(mock_page, 1280, 720)

    mock_page.evaluate.assert_called()
    mock_page.set_viewport_size.assert_called()


def test_geolocation_controller_set_geolocation(mock_page):
    controller = GeolocationController()
    location = {"latitude": 37.7749, "longitude": -122.4194, "accuracy": 100}
    controller.set_geolocation(mock_page, location)

    mock_page.context.grant_permissions.assert_called_with(['geolocation'])
    mock_page.context.set_geolocation.assert_called_with(location)
    mock_page.add_init_script.assert_called()