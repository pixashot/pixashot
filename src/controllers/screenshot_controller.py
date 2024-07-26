import logging
from playwright.sync_api import Page
from exceptions import BrowserException
from controllers.base_controller import BaseBrowserController

logger = logging.getLogger(__name__)


class ScreenshotController(BaseBrowserController):
    MAX_VIEWPORT_HEIGHT = 16384
    NETWORK_IDLE_TIMEOUT_MS = 1000
    SCROLL_PAUSE_MS = 500

    def prepare_for_full_page_screenshot(self, page: Page, window_width: int):
        try:
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_load_state('networkidle', timeout=self.NETWORK_IDLE_TIMEOUT_MS)
            full_height = page.evaluate('document.body.scrollHeight')
            if full_height > self.MAX_VIEWPORT_HEIGHT:
                full_height = self.MAX_VIEWPORT_HEIGHT

            self._set_viewport_and_scroll(page, window_width, full_height)
        except Exception as e:
            logger.error(f"Error preparing for full page screenshot: {str(e)}")
            raise BrowserException(f"Failed to prepare for full page screenshot: {str(e)}")

    def prepare_for_viewport_screenshot(self, page: Page, window_width: int, window_height: int):
        try:
            self._set_viewport_and_scroll(page, window_width, window_height)
        except Exception as e:
            logger.error(f"Error preparing for viewport screenshot: {str(e)}")
            raise BrowserException(f"Failed to prepare for viewport screenshot: {str(e)}")

    def _set_viewport_and_scroll(self, page: Page, width: int, height: int):
        try:
            page.set_viewport_size({'width': width, 'height': height})
            page.wait_for_load_state('networkidle', timeout=self.NETWORK_IDLE_TIMEOUT_MS)
            page.evaluate('window.scrollTo(0, 0)')
            page.wait_for_timeout(self.SCROLL_PAUSE_MS)
        except Exception as e:
            logger.error(f"Error setting viewport and scrolling: {str(e)}")
            raise BrowserException(f"Failed to set viewport and scroll: {str(e)}")
