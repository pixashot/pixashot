import asyncio
from playwright.async_api import Page, TimeoutError
from exceptions import TimeoutException
from controllers.base_controller import BaseBrowserController
import logging

logger = logging.getLogger(__name__)


class NavigationController(BaseBrowserController):
    async def goto_with_timeout(self, page: Page, url: str, timeout: float = 5.0):
        try:
            await page.goto(str(url), wait_until='domcontentloaded', timeout=timeout * 1000)
        except TimeoutError:
            logger.warning(f"Navigation exceeded {timeout} seconds. Proceeding without waiting for full load.")
            raise TimeoutException(f"Navigation to {url} timed out after {timeout} seconds")

    async def wait_for_network_idle(self, page: Page, timeout: int):
        try:
            await page.wait_for_load_state('networkidle', timeout=timeout)
        except TimeoutError:
            logger.warning(f"Timeout waiting for network idle: {timeout}ms")
            logger.warning("Proceeding with capture despite network not being completely idle")

    async def wait_for_network_mostly_idle(self, page: Page, timeout: float = 5.0, idle_threshold: int = 2, min_wait: float = 0.5):
        async def get_network_activity():
            return await page.evaluate('''() => {
                const resources = performance.getEntriesByType('resource');
                const recentResources = resources.filter(r => r.responseEnd > performance.now() - 1000);
                const pendingRequests = window.performance.getEntriesByType('resource').filter(r => !r.responseEnd).length;
                return {
                    recentRequests: recentResources.length,
                    pendingRequests: pendingRequests
                };
            }''')

        start_time = asyncio.get_event_loop().time()
        previous_activity = await get_network_activity()
        check_interval = 0.1

        while asyncio.get_event_loop().time() - start_time < timeout:
            await asyncio.sleep(check_interval)
            current_activity = await get_network_activity()

            activity_delta = (
                abs(current_activity['recentRequests'] - previous_activity['recentRequests']) +
                abs(current_activity['pendingRequests'] - previous_activity['pendingRequests'])
            )

            if activity_delta <= idle_threshold and asyncio.get_event_loop().time() - start_time >= min_wait:
                logger.info("Network considered mostly idle")
                return True  # Network is considered mostly idle

            previous_activity = current_activity
            check_interval = min(check_interval * 1.5, 0.5)  # Exponential backoff, max 0.5 second

        logger.warning(f"Network did not become mostly idle within {timeout} seconds")
        return False

    async def wait_for_selector(self, page: Page, selector: str, timeout: int):
        try:
            await page.wait_for_selector(selector, timeout=timeout)
        except TimeoutError:
            logger.warning(f"Timeout waiting for selector '{selector}': {timeout}ms")
            raise TimeoutException(f"Selector '{selector}' not found on the page within {timeout}ms")