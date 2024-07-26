import logging
import time
from playwright.sync_api import Page, TimeoutError
from exceptions import InteractionException, TimeoutException
from controllers.base_controller import BaseBrowserController

logger = logging.getLogger(__name__)


class InteractionController(BaseBrowserController):
    def perform_interactions(self, page: Page, interactions: list):
        for step in interactions:
            try:
                if step.action == "click":
                    self._click(page, step.selector)
                elif step.action == "type":
                    self._type(page, step.selector, step.text)
                elif step.action == "hover":
                    self._hover(page, step.selector)
                elif step.action == "scroll":
                    self._scroll(page, step.x, step.y)
                elif step.action == "wait_for":
                    self._handle_wait_for(page, step.wait_for)
            except Exception as e:
                logger.error(f"Error performing interaction {step.action}: {str(e)}")
                raise InteractionException(f"Failed to perform {step.action}: {str(e)}")

    def _click(self, page: Page, selector: str):
        page.click(selector)

    def _type(self, page: Page, selector: str, text: str):
        page.fill(selector, text)

    def _hover(self, page: Page, selector: str):
        page.hover(selector)

    def _scroll(self, page: Page, x: int, y: int):
        page.evaluate(f"window.scrollTo({x}, {y})")

    def _handle_wait_for(self, page: Page, wait_for_option):
        try:
            if wait_for_option.type == "network_idle":
                self.wait_for_network_idle(page, wait_for_option.value)
            elif wait_for_option.type == "network_mostly_idle":
                self.wait_for_network_mostly_idle(page, wait_for_option.value)
            elif wait_for_option.type == "selector":
                self.wait_for_selector(page, wait_for_option.value, timeout=30000)  # Default 30s timeout
            elif wait_for_option.type == "timeout":
                page.wait_for_timeout(wait_for_option.value)
        except TimeoutException as e:
            logger.warning(f"Timeout during wait_for action: {str(e)}")
            raise

    def wait_for_network_idle(self, page: Page, timeout: int):
        try:
            page.wait_for_load_state('networkidle', timeout=timeout)
        except TimeoutError:
            logger.warning(f"Timeout waiting for network idle: {timeout}ms")
            raise TimeoutException(f"Network did not become idle within {timeout}ms")

    def wait_for_network_mostly_idle(self, page: Page, timeout: int, idle_threshold: int = 2, check_interval: int = 100):
        def get_network_activity():
            return page.evaluate('''() => {
                const resources = performance.getEntriesByType('resource');
                const recentResources = resources.filter(r => r.responseEnd > performance.now() - 1000);
                const pendingRequests = window.performance.getEntriesByType('resource').filter(r => !r.responseEnd).length;
                return {
                    recentRequests: recentResources.length,
                    pendingRequests: pendingRequests
                };
            }''')

        start_time = page.evaluate('() => performance.now()')
        previous_activity = get_network_activity()

        while page.evaluate('() => performance.now()') - start_time < timeout:
            page.wait_for_timeout(check_interval)
            current_activity = get_network_activity()

            activity_delta = (
                abs(current_activity['recentRequests'] - previous_activity['recentRequests']) +
                abs(current_activity['pendingRequests'] - previous_activity['pendingRequests'])
            )

            if activity_delta <= idle_threshold:
                logger.info("Network considered mostly idle")
                return

            previous_activity = current_activity

        logger.warning(f"Network did not become mostly idle within {timeout}ms")
        raise TimeoutException(f"Network did not become mostly idle within {timeout}ms")

    def wait_for_selector(self, page: Page, selector: str, timeout: int):
        try:
            page.wait_for_selector(selector, timeout=timeout)
        except TimeoutError:
            logger.warning(f"Timeout waiting for selector '{selector}': {timeout}ms")
            raise TimeoutException(f"Selector '{selector}' not found on the page within {timeout}ms")

    def goto_with_timeout(self, page: Page, url: str, timeout: float = 5.0):
        try:
            page.goto(str(url), wait_until='domcontentloaded', timeout=timeout * 1000)
        except TimeoutError:
            logger.warning(f"Navigation exceeded {timeout} seconds. Proceeding without waiting for full load.")
            raise TimeoutException(f"Navigation to {url} timed out after {timeout} seconds")

    def wait_for_animations(self, page: Page, timeout: int = 5000):
        try:
            page.evaluate(f"""
                () => new Promise((resolve) => {{
                    const checkAnimations = () => {{
                        const animating = document.querySelector(':scope *:not(:where(:hover, :active))');
                        if (!animating) {{
                            resolve();
                        }} else {{
                            requestAnimationFrame(checkAnimations);
                        }}
                    }};
                    checkAnimations();
                    setTimeout(resolve, {timeout});
                }})
            """)
        except Exception as e:
            logger.warning(f"Error waiting for animations: {str(e)}")