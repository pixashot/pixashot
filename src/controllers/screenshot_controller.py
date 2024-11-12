import logging
from playwright.async_api import Page, Error as PlaywrightError, TimeoutError
from exceptions import BrowserException, TimeoutException
from controllers.base_controller import BaseBrowserController

logger = logging.getLogger(__name__)


class ScreenshotController(BaseBrowserController):
    MAX_VIEWPORT_HEIGHT = 16384
    NETWORK_IDLE_TIMEOUT_MS = 5000
    SCROLL_PAUSE_MS = 500
    SCREENSHOT_TIMEOUT_MS = 10000  # Default screenshot timeout

    async def _take_screenshot_with_fallback(self, screenshot_func, *args, **kwargs):
        """
        Attempt to take a screenshot with timeout handling.
        If timeout occurs, attempts to take a basic screenshot of current state.
        """
        try:
            return await screenshot_func(*args, **kwargs)
        except TimeoutError as e:
            logger.warning(f"Screenshot timeout occurred: {str(e)}. Attempting fallback capture...")

            # Remove timeout for fallback attempt
            if 'timeout' in kwargs:
                del kwargs['timeout']

            try:
                # Attempt basic screenshot without waiting for additional resources
                return await screenshot_func(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(f"Fallback screenshot also failed: {str(fallback_error)}")
                raise BrowserException(f"Both primary and fallback screenshot attempts failed: {str(fallback_error)}")

    async def prepare_for_full_page_screenshot(self, page: Page, window_width: int):
        """Prepare page for full-page screenshot with enhanced error handling and timeout recovery."""
        try:
            # Scroll to bottom and wait for any dynamic content to load
            try:
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            except PlaywrightError as e:
                logger.warning(f"Scroll failed: {str(e)}. Continuing with capture...")

            # Try network idle wait, but don't fail if it times out
            try:
                await page.wait_for_load_state('networkidle', timeout=self.NETWORK_IDLE_TIMEOUT_MS)
            except TimeoutError:
                logger.warning("Network idle timeout reached, continuing with capture")

            # Get the full height with error handling
            try:
                full_height = await page.evaluate('document.body.scrollHeight')
                if not isinstance(full_height, (int, float)) or full_height <= 0:
                    logger.warning(f"Invalid page height detected: {full_height}. Using default height.")
                    full_height = self.MAX_VIEWPORT_HEIGHT
            except PlaywrightError as e:
                logger.warning(f"Failed to determine page height: {str(e)}. Using default height.")
                full_height = self.MAX_VIEWPORT_HEIGHT

            # Enforce maximum height limit
            full_height = min(full_height, self.MAX_VIEWPORT_HEIGHT)

            await self._set_viewport_and_scroll(page, window_width, full_height)

        except Exception as e:
            logger.error(f"Error in prepare_for_full_page_screenshot: {str(e)}")
            logger.warning("Continuing with capture despite preparation errors...")

    async def _set_viewport_and_scroll(self, page: Page, width: int, height: int):
        """Set viewport size and handle scrolling with fallback handling."""
        try:
            # Validate and adjust dimensions if needed
            width = max(1, min(width, 16384))  # Reasonable limits
            height = max(1, min(height, self.MAX_VIEWPORT_HEIGHT))

            # Set viewport size
            try:
                await page.set_viewport_size({'width': width, 'height': height})
            except PlaywrightError as e:
                logger.warning(f"Viewport size adjustment failed: {str(e)}. Using default viewport.")

            # Try network idle wait, but continue if it times out
            try:
                await page.wait_for_load_state('networkidle', timeout=self.NETWORK_IDLE_TIMEOUT_MS)
            except TimeoutError:
                logger.warning("Network idle timeout during viewport setup, continuing...")

            # Scroll back to top
            try:
                await page.evaluate('window.scrollTo(0, 0)')
            except PlaywrightError as e:
                logger.warning(f"Scroll to top failed: {str(e)}. Continuing with capture.")

            # Brief pause to let the page settle
            await page.wait_for_timeout(self.SCROLL_PAUSE_MS)

        except Exception as e:
            logger.error(f"Error in viewport setup: {str(e)}")
            logger.warning("Continuing with capture despite viewport setup issues...")

    async def take_screenshot(self, page: Page, options: dict):
        """Take a screenshot with timeout handling and fallback options."""
        screenshot_options = {
            'path': options.get('path'),
            'full_page': options.get('full_page', False),
            'type': options.get('format', 'png'),
            'quality': options.get('quality'),
            'omit_background': options.get('omit_background', False),
            'timeout': self.SCREENSHOT_TIMEOUT_MS
        }

        if options.get('selector'):
            try:
                element = await page.query_selector(options['selector'])
                if element:
                    return await self._take_screenshot_with_fallback(
                        element.screenshot,
                        **screenshot_options
                    )
                else:
                    logger.warning(f"Selector '{options['selector']}' not found. Capturing full page instead.")
            except Exception as e:
                logger.warning(f"Element screenshot failed: {str(e)}. Falling back to full page.")

        # If element screenshot fails or no selector specified, take full page screenshot
        return await self._take_screenshot_with_fallback(
            page.screenshot,
            **screenshot_options
        )