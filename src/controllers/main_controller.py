import logging
from playwright.sync_api import Page

from controllers.interaction_controller import InteractionController
from exceptions import BrowserException
from controllers.navigation_controller import NavigationController
from controllers.content_controller import ContentController
from controllers.screenshot_controller import ScreenshotController
from controllers.geolocation_controller import GeolocationController

logger = logging.getLogger(__name__)


class MainBrowserController:
    def __init__(self):
        self.navigation_controller = NavigationController()
        self.content_controller = ContentController()
        self.screenshot_controller = ScreenshotController()
        self.geolocation_controller = GeolocationController()
        self.interaction_controller = InteractionController()

    def prepare_page(self, page: Page, options):
        try:
            self.content_controller.prevent_horizontal_overflow(page)
            self.content_controller.inject_scripts(page)
            if options.dark_mode:
                self.content_controller.apply_dark_mode(page)
            if options.geolocation:
                self.geolocation_controller.set_geolocation(page, options.geolocation)

            if options.wait_for_network == 'idle':
                self.navigation_controller.wait_for_network_idle(page, options.wait_for_timeout)
            elif options.wait_for_network == 'mostly_idle':
                self.navigation_controller.wait_for_network_mostly_idle(page, options.wait_for_timeout)

            if options.interact_before_capture:
                self.interaction_controller.perform_interactions(page, options.interact_before_capture)

            if options.wait_for_animation:
                self.interaction_controller.wait_for_animations(page)

            if options.custom_js:
                self.content_controller.execute_custom_js(page, options.custom_js)

            if options.wait_for_selector:
                self.navigation_controller.wait_for_selector(page, options.wait_for_selector, options.wait_for_timeout)

            page.wait_for_timeout(500)

            logger.info('Page prepared successfully')
        except Exception as e:
            logger.error(f"Error preparing page: {str(e)}")
            raise BrowserException(f"Failed to prepare page: {str(e)}")

    def goto_with_timeout(self, page: Page, url: str, timeout: float = 5.0):
        return self.navigation_controller.goto_with_timeout(page, url, timeout)

    def prepare_for_full_page_screenshot(self, page: Page, window_width: int, window_height: int):
        return self.screenshot_controller.prepare_for_full_page_screenshot(page, window_width, window_height)

    def prepare_for_viewport_screenshot(self, page: Page, window_width: int, window_height: int):
        return self.screenshot_controller.prepare_for_viewport_screenshot(page, window_width, window_height)

    def wait_for_dynamic_content(self, page: Page, check_interval: int = 1000, max_unchanged_checks: int = 5):
        return self.content_controller.wait_for_dynamic_content(page, check_interval, max_unchanged_checks)
