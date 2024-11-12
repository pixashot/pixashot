import logging
from playwright.async_api import Page, Error as PlaywrightError, TimeoutError
from exceptions import BrowserException
from controllers.base_controller import BaseBrowserController

logger = logging.getLogger(__name__)


class ScreenshotController(BaseBrowserController):
    MAX_VIEWPORT_HEIGHT = 16384  # Max height for full-page screenshots
    NETWORK_IDLE_TIMEOUT_MS = 5000  # Increased from 500ms to 5000ms
    SCROLL_PAUSE_MS = 500  # Increased scroll pause time

    async def prepare_for_full_page_screenshot(self, page: Page, window_width: int):
        """Prepare page for full-page screenshot with enhanced error handling."""
        try:
            # Scroll to bottom and wait for any dynamic content to load
            try:
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            except PlaywrightError as e:
                raise BrowserException(
                    f"Failed to scroll page: Page might have been closed or javascript disabled. Details: {str(e)}"
                )

            # Wait for network idle with timeout handling
            try:
                await page.wait_for_load_state('networkidle', timeout=self.NETWORK_IDLE_TIMEOUT_MS)
            except TimeoutError:
                logger.warning("Network idle timeout reached, continuing with capture")

            # Get the full height with error handling
            try:
                full_height = await page.evaluate('document.body.scrollHeight')
                if not isinstance(full_height, (int, float)) or full_height <= 0:
                    raise BrowserException(
                        f"Invalid page height detected: {full_height}. Page might not be properly loaded."
                    )
            except PlaywrightError as e:
                raise BrowserException(
                    f"Failed to determine page height: Page might be invalid or unresponsive. Details: {str(e)}"
                )

            # Check height limits
            if full_height > self.MAX_VIEWPORT_HEIGHT:
                full_height = self.MAX_VIEWPORT_HEIGHT
                logger.warning(
                    f"Page height exceeds maximum ({full_height}px > {self.MAX_VIEWPORT_HEIGHT}px). "
                    "Screenshot will be truncated."
                )

            await self._set_viewport_and_scroll(page, window_width, full_height)

        except PlaywrightError as e:
            error_msg = str(e)
            if "Target closed" in error_msg:
                raise BrowserException(
                    "Page was closed unexpectedly during full-page screenshot preparation. "
                    "This might be due to a navigation, redirect, or page crash."
                )
            elif "javascript" in error_msg.lower():
                raise BrowserException(
                    "JavaScript execution failed during full-page screenshot preparation. "
                    f"The page might have JavaScript disabled or errors. Details: {error_msg}"
                )
            else:
                raise BrowserException(
                    f"Playwright error during full-page screenshot preparation: {error_msg}"
                )
        except Exception as e:
            logger.error(f"Error preparing for full page screenshot: {str(e)}", exc_info=True)
            raise BrowserException(
                f"Failed to prepare for full page screenshot. "
                f"Type: {type(e).__name__}, Details: {str(e)}"
            )

    async def _set_viewport_and_scroll(self, page: Page, width: int, height: int):
        """Set viewport size and handle scrolling with detailed error handling."""
        try:
            # Validate dimensions
            if width <= 0 or height <= 0:
                raise BrowserException(
                    f"Invalid viewport dimensions: width={width}, height={height}"
                )

            # Set viewport size with error handling
            try:
                await page.set_viewport_size({'width': width, 'height': height})
            except PlaywrightError as e:
                raise BrowserException(
                    f"Failed to set viewport size ({width}x{height}). "
                    f"The dimensions might be invalid or unsupported. Details: {str(e)}"
                )

            # Wait for network idle if needed
            if not getattr(page, '_waited_for_network', False):
                try:
                    await page.wait_for_load_state('networkidle', timeout=self.NETWORK_IDLE_TIMEOUT_MS)
                    setattr(page, '_waited_for_network', True)
                except TimeoutError:
                    logger.warning(
                        f"Network idle timeout ({self.NETWORK_IDLE_TIMEOUT_MS}ms) reached, "
                        "continuing with capture"
                    )

            # Scroll back to top
            try:
                await page.evaluate('window.scrollTo(0, 0)')
            except PlaywrightError as e:
                raise BrowserException(
                    f"Failed to scroll back to top of page. "
                    f"The page might be unresponsive. Details: {str(e)}"
                )

            # Final pause to let the page settle
            await page.wait_for_timeout(self.SCROLL_PAUSE_MS)

        except PlaywrightError as e:
            error_msg = str(e)
            if "Target closed" in error_msg:
                raise BrowserException(
                    "Page was closed during viewport setup. "
                    "This might be due to a navigation, redirect, or page crash."
                )
            else:
                raise BrowserException(
                    f"Playwright error during viewport setup: {error_msg}"
                )
        except Exception as e:
            logger.error(f"Error setting viewport and scrolling: {str(e)}", exc_info=True)
            raise BrowserException(
                f"Failed to set viewport and scroll. "
                f"Type: {type(e).__name__}, Details: {str(e)}"
            )