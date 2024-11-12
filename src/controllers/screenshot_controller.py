from playwright.async_api import Page, TimeoutError
import logging
from exceptions import BrowserException, TimeoutException
from controllers.base_controller import BaseBrowserController

logger = logging.getLogger(__name__)


class ScreenshotController(BaseBrowserController):
    MAX_VIEWPORT_HEIGHT = 16384
    NETWORK_IDLE_TIMEOUT_MS = 5000
    SCROLL_PAUSE_MS = 500
    SCREENSHOT_TIMEOUT_MS = 10000

    async def take_screenshot(self, page: Page, options: dict) -> bytes:
        """Take a screenshot with graceful timeout handling."""
        screenshot_options = {
            'path': options.get('path'),
            'full_page': options.get('full_page', False),
            'type': options.get('format', 'png'),
            'quality': options.get('quality') if options.get('format') != 'png' else None,
            'omit_background': options.get('omit_background', False),
            'timeout': self.SCREENSHOT_TIMEOUT_MS
        }

        try:
            # First attempt with all options
            return await self._take_screenshot_with_retry(page, screenshot_options)
        except TimeoutError as e:
            logger.warning(f"Initial screenshot attempt timed out: {str(e)}. Attempting fallback capture...")

            # Remove timeout and try again with minimal options
            fallback_options = screenshot_options.copy()
            fallback_options.pop('timeout', None)  # Remove timeout

            try:
                # Attempt fallback screenshot with minimal waiting
                return await self._take_fallback_screenshot(page, fallback_options)
            except Exception as fallback_error:
                logger.error(f"Fallback screenshot also failed: {str(fallback_error)}")
                raise BrowserException(f"Both primary and fallback screenshot attempts failed: {str(fallback_error)}")

    async def _take_screenshot_with_retry(self, page: Page, options: dict) -> bytes:
        """Attempt to take a screenshot with retry logic."""
        try:
            if options.get('selector'):
                element = await page.query_selector(options['selector'])
                if element:
                    return await element.screenshot(**options)
                else:
                    logger.warning(f"Selector '{options['selector']}' not found. Falling back to full page.")

            return await page.screenshot(**options)
        except TimeoutError as e:
            raise e
        except Exception as e:
            logger.error(f"Error during screenshot capture: {str(e)}")
            raise

    async def _take_fallback_screenshot(self, page: Page, options: dict) -> bytes:
        """Take a fallback screenshot with minimal options."""
        try:
            # Remove potentially problematic options
            minimal_options = {
                'path': options.get('path'),
                'type': options.get('format', 'png'),
                'full_page': options.get('full_page', False)
            }

            # Try to stabilize the page state
            try:
                await page.evaluate('window.stop()')  # Stop any ongoing resource loading
            except Exception as e:
                logger.warning(f"Failed to stop page loading: {str(e)}")

            return await page.screenshot(**minimal_options)
        except Exception as e:
            logger.error(f"Fallback screenshot failed: {str(e)}")
            raise

    async def prepare_for_full_page_screenshot(self, page: Page, window_width: int):
        """Prepare page for full-page screenshot with improved timeout handling."""
        try:
            # Scroll to bottom with reduced timeout
            try:
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            except Exception as e:
                logger.warning(f"Initial scroll failed: {str(e)}. Continuing with capture...")

            # Try network idle wait with short timeout
            try:
                await page.wait_for_load_state('networkidle', timeout=1000)
            except TimeoutError:
                logger.warning("Network idle timeout reached, continuing with capture")

            # Get page height with fallback
            try:
                full_height = await page.evaluate('document.body.scrollHeight')
                if not isinstance(full_height, (int, float)) or full_height <= 0:
                    full_height = self.MAX_VIEWPORT_HEIGHT
            except Exception:
                full_height = self.MAX_VIEWPORT_HEIGHT
                logger.warning(f"Failed to get page height, using maximum: {self.MAX_VIEWPORT_HEIGHT}")

            # Enforce maximum height limit
            full_height = min(full_height, self.MAX_VIEWPORT_HEIGHT)

            # Set viewport size
            try:
                await page.set_viewport_size({'width': window_width, 'height': full_height})
            except Exception as e:
                logger.warning(f"Viewport size adjustment failed: {str(e)}")

            # Final scroll to top
            try:
                await page.evaluate('window.scrollTo(0, 0)')
            except Exception as e:
                logger.warning(f"Final scroll failed: {str(e)}")

            # Brief pause to let the page settle
            await page.wait_for_timeout(self.SCROLL_PAUSE_MS)

        except Exception as e:
            logger.error(f"Error in prepare_for_full_page_screenshot: {str(e)}")
            logger.warning("Continuing with capture despite preparation errors...")