from playwright.sync_api import Page, TimeoutError
from exceptions import TimeoutException
from controllers.base_controller import BaseBrowserController
import logging

logger = logging.getLogger(__name__)


class NavigationController(BaseBrowserController):
    def goto_with_timeout(self, page: Page, url: str, timeout: float = 5.0):
        try:
            page.goto(str(url), wait_until='domcontentloaded', timeout=timeout * 1000)
        except TimeoutError:
            logger.warning(f"Navigation exceeded {timeout} seconds. Proceeding without waiting for full load.")
            raise TimeoutException(f"Navigation to {url} timed out after {timeout} seconds")

    def wait_for_network_idle(self, page: Page, timeout: int):
        try:
            page.wait_for_load_state('networkidle', timeout=timeout)
        except TimeoutError:
            logger.warning(f"Timeout waiting for network idle: {timeout}ms")
            logger.warning("Proceeding with capture despite network not being completely idle")

    def wait_for_selector(self, page: Page, selector: str, timeout: int):
        try:
            page.wait_for_selector(selector, timeout=timeout)
        except TimeoutError:
            logger.warning(f"Timeout waiting for selector '{selector}': {timeout}ms")
            raise TimeoutException(f"Selector '{selector}' not found on the page within {timeout}ms")
