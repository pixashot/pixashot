import os
import asyncio
import logging
from playwright.async_api import Page
from typing import Awaitable, TypeVar
from exceptions import BrowserException, NetworkException, ElementNotFoundException, JavaScriptExecutionException, TimeoutException

T = TypeVar('T')

logger = logging.getLogger(__name__)

class BrowserController:
    MAX_VIEWPORT_HEIGHT = 16384
    NETWORK_IDLE_TIMEOUT_MS = 1000
    SCROLL_PAUSE_MS = 500

    def __init__(self):
        self.js_file_path = os.path.join(os.path.dirname(__file__), 'js/page-utils.js')
        self.dynamic_content_detector_path = os.path.join(os.path.dirname(__file__), 'js/dynamic-content-detector.js')

    async def goto_with_timeout(self, page: Page, url: str, timeout: float = 5.0):
        try:
            await asyncio.wait_for(page.goto(url, wait_until='domcontentloaded'), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Navigation exceeded {timeout} seconds. Proceeding without waiting for full load.")
            raise TimeoutException(f"Navigation to {url} timed out after {timeout} seconds")

    async def prepare_page(self, page: Page, options):
        try:
            await asyncio.gather(
                self.inject_scripts(page),
                self.wait_for_network_idle(page, options.wait_for_timeout),
                self.execute_custom_js(page, options.custom_js) if options.custom_js else asyncio.sleep(0),
                self.wait_for_selector(page, options.wait_for_selector,
                                       options.wait_for_timeout) if options.wait_for_selector else asyncio.sleep(0)
            )
        except Exception as e:
            logger.error(f"Error preparing page: {str(e)}")
            raise BrowserException(f"Failed to prepare page: {str(e)}")

    async def inject_scripts(self, page: Page):
        try:
            with open(self.js_file_path, 'r') as file:
                js_content = file.read()
                await page.evaluate(js_content)
            await page.evaluate('pageUtils.disableSmoothScrolling()')
            await page.evaluate('pageUtils.waitForAllImages()')
        except Exception as e:
            logger.error(f"Error injecting scripts: {str(e)}")
            raise JavaScriptExecutionException(f"Failed to inject scripts: {str(e)}")

    async def wait_for_network_idle(self, page: Page, timeout: int):
        try:
            await self._safe_wait(page.wait_for_load_state('networkidle'), timeout, "Timeout waiting for network idle")
        except TimeoutException as e:
            logger.warning(str(e))
            raise NetworkException(str(e))

    async def execute_custom_js(self, page: Page, custom_js: str):
        try:
            await page.evaluate(custom_js)
        except Exception as e:
            logger.error(f"Error executing custom JavaScript: {str(e)}")
            raise JavaScriptExecutionException(f"Error executing custom JavaScript: {str(e)}")

    async def wait_for_selector(self, page: Page, selector: str, timeout: int):
        try:
            await self._safe_wait(page.wait_for_selector(selector), timeout, f"Timeout waiting for selector '{selector}'")
        except TimeoutException as e:
            logger.warning(str(e))
            raise ElementNotFoundException(f"Selector '{selector}' not found on the page within {timeout}ms")

    async def prepare_for_full_page_screenshot(self, page: Page, window_width: int):
        try:
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await self.wait_for_network_idle(page, self.NETWORK_IDLE_TIMEOUT_MS)

            full_height = await page.evaluate('Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)')
            full_height = min(full_height, self.MAX_VIEWPORT_HEIGHT)

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

    # Utility functions

    async def _safe_wait(self, wait_function: Awaitable[T], timeout: int, error_message: str) -> T:
        try:
            return await asyncio.wait_for(wait_function, timeout=timeout / 1000)  # Convert ms to seconds
        except asyncio.TimeoutError:
            logger.warning(f"{error_message}: {timeout}ms")
            raise TimeoutException(f"{error_message}: {timeout}ms")

    async def _set_viewport_and_scroll(self, page: Page, width: int, height: int):
        try:
            await page.set_viewport_size({'width': width, 'height': height})
            await self.wait_for_network_idle(page, self.NETWORK_IDLE_TIMEOUT_MS)
            await page.evaluate('window.scrollTo(0, 0)')
            await page.wait_for_timeout(self.SCROLL_PAUSE_MS)
        except Exception as e:
            logger.error(f"Error setting viewport and scrolling: {str(e)}")
            raise BrowserException(f"Failed to set viewport and scroll: {str(e)}")

    async def wait_for_dynamic_content(self, page: Page, check_interval: int = 1000, max_unchanged_checks: int = 5):
        try:
            with open(self.dynamic_content_detector_path, 'r') as file:
                js_content = file.read()
                await page.evaluate(js_content)
            await page.evaluate(f'detectDynamicContentLoading({check_interval}, {max_unchanged_checks})')
        except Exception as e:
            logger.error(f"Error waiting for dynamic content: {str(e)}")
            raise JavaScriptExecutionException(f"Failed to wait for dynamic content: {str(e)}")