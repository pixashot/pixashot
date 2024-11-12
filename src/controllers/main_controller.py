import asyncio
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

            # Combine network waits into a single operation
            if options.wait_for_network in ('idle', 'mostly_idle'):
                if options.wait_for_network == 'idle':
                    await self.interaction_controller.wait_for_network_idle(
                        page,
                        min(options.wait_for_timeout, 5000)  # Cap at 5 seconds
                    )
                else:
                    await self.interaction_controller.wait_for_network_mostly_idle(
                        page,
                        min(options.wait_for_timeout, 5000)  # Cap at 5 seconds
                    )
                setattr(page, '_waited_for_network', True)

            # Parallel execution of independent operations
            await asyncio.gather(
                self._apply_dark_mode(page, options) if options.dark_mode else asyncio.sleep(0),
                self._set_geolocation(page, options) if options.geolocation else asyncio.sleep(0)
            )

            if options.wait_for_animation:
                await self.interaction_controller.wait_for_animations(page, timeout=2000)  # Cap animation wait at 2s

            if options.custom_js:
                await self.content_controller.execute_custom_js(page, options.custom_js)

            if options.wait_for_selector:
                await self.interaction_controller.wait_for_selector(
                    page,
                    options.wait_for_selector,
                    min(options.wait_for_timeout, 5000)  # Cap at 5 seconds
                )

            # Remove arbitrary delay
            # await page.wait_for_timeout(500)  # This line is removed

            logger.info('Page prepared successfully')
        except Exception as e:
            logger.error(f"Error preparing page: {str(e)}")
            raise BrowserException(f"Failed to prepare page: {str(e)}")

    async def _apply_dark_mode(self, page: Page, options):
        if options.dark_mode:
            await self.content_controller.apply_dark_mode(page)

    async def _set_geolocation(self, page: Page, options):
        if options.geolocation:
            await self.geolocation_controller.set_geolocation(page, options.geolocation)

    async def goto_with_timeout(self, page: Page, url: str, timeout: float = 5.0):
        return await self.interaction_controller.goto_with_timeout(page, url, timeout)

    async def perform_interactions(self, page: Page, interactions: list):
        return await self.interaction_controller.perform_interactions(page, interactions)

    async def prepare_for_full_page_screenshot(self, page: Page, window_width: int):
        return await self.screenshot_controller.prepare_for_full_page_screenshot(page, window_width)

    async def prepare_for_viewport_screenshot(self, page: Page, window_width: int, window_height: int):
        return await self.screenshot_controller.prepare_for_viewport_screenshot(page, window_width, window_height)