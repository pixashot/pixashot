import logging
from playwright.async_api import Page

from controllers.interaction_controller import InteractionController
from exceptions import BrowserException
from controllers.content_controller import ContentController
from controllers.screenshot_controller import ScreenshotController
from controllers.geolocation_controller import GeolocationController

logger = logging.getLogger(__name__)

class MainBrowserController:
    def __init__(self):
        self.interaction_controller = InteractionController()
        self.content_controller = ContentController()
        self.screenshot_controller = ScreenshotController()
        self.geolocation_controller = GeolocationController()

    async def prepare_page(self, page: Page, options):
        try:
            await self.content_controller.prevent_horizontal_overflow(page)
            if options.dark_mode:
                await self.content_controller.apply_dark_mode(page)
            if options.geolocation:
                await self.geolocation_controller.set_geolocation(page, options.geolocation)

            if options.wait_for_network == 'idle':
                await self.interaction_controller.wait_for_network_idle(page, options.wait_for_timeout)
            elif options.wait_for_network == 'mostly_idle':
                await self.interaction_controller.wait_for_network_mostly_idle(page, options.wait_for_timeout)

            if options.wait_for_animation:
                await self.interaction_controller.wait_for_animations(page)

            if options.custom_js:
                await self.content_controller.execute_custom_js(page, options.custom_js)

            if options.wait_for_selector:
                await self.interaction_controller.wait_for_selector(page, options.wait_for_selector, options.wait_for_timeout)

            await page.wait_for_timeout(500)

            logger.info('Page prepared successfully')
        except Exception as e:
            logger.error(f"Error preparing page: {str(e)}")
            raise BrowserException(f"Failed to prepare page: {str(e)}")

    async def goto_with_timeout(self, page: Page, url: str, timeout: float = 5.0):
        return await self.interaction_controller.goto_with_timeout(page, url, timeout)

    async def perform_interactions(self, page: Page, interactions: list):
        return await self.interaction_controller.perform_interactions(page, interactions)

    async def prepare_for_full_page_screenshot(self, page: Page, window_width: int):
        return await self.screenshot_controller.prepare_for_full_page_screenshot(page, window_width)

    async def prepare_for_viewport_screenshot(self, page: Page, window_width: int, window_height: int):
        return await self.screenshot_controller.prepare_for_viewport_screenshot(page, window_width, window_height)