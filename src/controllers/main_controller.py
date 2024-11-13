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
        """Prepare page with improved error handling and more resilient network waiting."""
        try:
            await self.content_controller.prevent_horizontal_overflow(page)

            # Combine network waits into a single operation with better error handling
            if options.wait_for_network in ('idle', 'mostly_idle'):
                try:
                    # Use shorter timeout for network wait
                    timeout = min(options.wait_for_timeout, 5000)
                    if options.wait_for_network == 'idle':
                        try:
                            await self.interaction_controller.wait_for_network_idle(page, timeout)
                        except Exception as e:
                            logger.warning(f"Network idle wait failed, continuing: {str(e)}")
                    else:
                        try:
                            await self.interaction_controller.wait_for_network_mostly_idle(page, timeout)
                        except Exception as e:
                            logger.warning(f"Network mostly idle wait failed, continuing: {str(e)}")
                    setattr(page, '_waited_for_network', True)
                except Exception as e:
                    logger.warning(f"Network wait failed, continuing with page preparation: {str(e)}")

            # Execute independent operations in parallel with error handling
            tasks = []
            if options.dark_mode:
                tasks.append(self._apply_dark_mode(page, options))
            if options.geolocation:
                tasks.append(self._set_geolocation(page, options))

            if tasks:
                try:
                    await asyncio.gather(*tasks, return_exceptions=True)
                except Exception as e:
                    logger.warning(f"Some page preparation tasks failed: {str(e)}")

            if options.wait_for_animation:
                try:
                    await self.interaction_controller.wait_for_animations(page, timeout=2000)
                except Exception as e:
                    logger.warning(f"Animation wait failed, continuing: {str(e)}")

            if options.custom_js:
                try:
                    await self.content_controller.execute_custom_js(page, options.custom_js)
                except Exception as e:
                    logger.warning(f"Custom JS execution failed: {str(e)}")

            if options.wait_for_selector:
                try:
                    await self.interaction_controller.wait_for_selector(
                        page,
                        options.wait_for_selector,
                        min(options.wait_for_timeout, 5000)
                    )
                except Exception as e:
                    logger.warning(f"Selector wait failed: {str(e)}")

            logger.info('Page prepared successfully')
        except Exception as e:
            logger.error(f"Error preparing page: {str(e)}")
            # Convert the error to a BrowserException but include the original error details
            error_message = f"Failed to prepare page: {str(e)}"
            raise BrowserException(error_message) from e

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