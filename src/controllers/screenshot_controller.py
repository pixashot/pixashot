import logging
from playwright.async_api import Page
from exceptions import BrowserException
from controllers.base_controller import BaseBrowserController

logger = logging.getLogger(__name__)


class ScreenshotController(BaseBrowserController):
    MAX_VIEWPORT_HEIGHT = 16384
    NETWORK_IDLE_TIMEOUT_MS = 1000
    SCROLL_PAUSE_MS = 500
    NETWORK_IDLE_TIMEOUT_MS = 500
    SCROLL_PAUSE_MS = 100

    async def prepare_for_full_page_screenshot(self, page: Page, window_width: int):
        try:
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_load_state('networkidle', timeout=self.NETWORK_IDLE_TIMEOUT_MS)
            full_height = await page.evaluate('document.body.scrollHeight')
            if full_height > self.MAX_VIEWPORT_HEIGHT:
                full_height = self.MAX_VIEWPORT_HEIGHT

            await self._set_viewport_and_scroll(page, window_width, full_height)
        except Exception as e:
            logger.error(f"Error preparing for full page screenshot: {str(e)}")
            raise BrowserException(f"Failed to prepare for full page screenshot: {str(e)}")

    async def prepare_for_viewport_screenshot(self, page: Page, window_width: int, window_height: int):
        try:
            await self._set_viewport_and_scroll(page, window_width, window_height)
        except Exception as e:
            logger.error(f"Error preparing for viewport screenshot: {str(e)}")
            raise BrowserException(f"Failed to prepare for viewport screenshot: {str(e)}")

    async def _set_viewport_and_scroll(self, page: Page, width: int, height: int):
        try:
            await page.set_viewport_size({'width': width, 'height': height})
            # Only wait for network idle if we're not already waiting elsewhere
            if not getattr(page, '_waited_for_network', False):
                await page.wait_for_load_state('networkidle', timeout=self.NETWORK_IDLE_TIMEOUT_MS)
                setattr(page, '_waited_for_network', True)
            await page.evaluate('window.scrollTo(0, 0)')
            await page.wait_for_timeout(self.SCROLL_PAUSE_MS)
        except Exception as e:
            logger.error(f"Error setting viewport and scrolling: {str(e)}")
            raise BrowserException(f"Failed to set viewport and scroll: {str(e)}")