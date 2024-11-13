import logging
import time
from playwright.async_api import Page
from playwright._impl._errors import Error as PlaywrightError
from exceptions import InteractionException, TimeoutException

logger = logging.getLogger(__name__)


class InteractionController:
    async def perform_interactions(self, page: Page, interactions: list):
        for step in interactions:
            try:
                if step.action == "click":
                    await self._click(page, step.selector)
                elif step.action == "type":
                    await self._type(page, step.selector, step.text)
                elif step.action == "hover":
                    await self._hover(page, step.selector)
                elif step.action == "scroll":
                    await self._scroll(page, step.x, step.y)
                elif step.action == "wait_for":
                    await self._handle_wait_for(page, step.wait_for)
            except Exception as e:
                logger.error(f"Error performing interaction {step.action}: {str(e)}")
                raise InteractionException(f"Failed to perform {step.action}: {str(e)}")

    async def _click(self, page: Page, selector: str):
        await page.click(selector)

    async def _type(self, page: Page, selector: str, text: str):
        await page.fill(selector, text)

    async def _hover(self, page: Page, selector: str):
        await page.hover(selector)

    async def _scroll(self, page: Page, x: int, y: int):
        await page.evaluate(f"window.scrollTo({x}, {y})")

    async def _handle_wait_for(self, page: Page, wait_for_option):
        try:
            if wait_for_option.type == "network_idle":
                await self.wait_for_network_idle(page, wait_for_option.value)
            elif wait_for_option.type == "network_mostly_idle":
                await self.wait_for_network_mostly_idle(page, wait_for_option.value)
            elif wait_for_option.type == "selector":
                await self.wait_for_selector(page, wait_for_option.value, timeout=30000)  # Default 30s timeout
            elif wait_for_option.type == "timeout":
                await page.wait_for_timeout(wait_for_option.value)
        except TimeoutException as e:
            logger.warning(f"Timeout during wait_for action: {str(e)}")
            raise

    async def wait_for_network_idle(self, page: Page, timeout: int):
        try:
            await page.wait_for_load_state('networkidle', timeout=timeout)
        except TimeoutError:
            logger.warning(f"Timeout waiting for network idle: {timeout}ms")
            raise TimeoutException(f"Network did not become idle within {timeout}ms")

    async def wait_for_network_mostly_idle(self, page: Page, timeout: int, idle_threshold: int = 2,
                                           check_interval: int = 100):
        """Wait for network activity to become mostly idle with improved error handling."""
        try:
            async def check_network_activity():
                try:
                    return await page.evaluate('''() => {
                        return {
                            pendingRequests: window.performance.getEntriesByType('resource')
                                .filter(r => !r.responseEnd).length,
                            recentRequests: window.performance.getEntriesByType('resource')
                                .filter(r => r.responseEnd > performance.now() - 1000).length
                        };
                    }''')
                except Exception:
                    return {'pendingRequests': 0, 'recentRequests': 0}

            start_time = time.time()
            previous_activity = await check_network_activity()

            while time.time() - start_time < timeout / 1000:  # Convert timeout to seconds
                try:
                    # Use shorter wait intervals
                    await page.wait_for_timeout(min(check_interval, 50))

                    current_activity = await check_network_activity()

                    activity_delta = (
                            abs(current_activity['recentRequests'] - previous_activity['recentRequests']) +
                            abs(current_activity['pendingRequests'] - previous_activity['pendingRequests'])
                    )

                    if activity_delta <= idle_threshold:
                        logger.debug("Network considered mostly idle")
                        return

                    previous_activity = current_activity

                except PlaywrightError as e:
                    # Handle specific Playwright errors
                    if "Target closed" in str(e) or "Target page, context or browser has been closed" in str(e):
                        logger.warning("Page closed during network wait, considering as idle")
                        return
                    raise
                except Exception as e:
                    logger.warning(f"Error during network activity check: {str(e)}")
                    # Continue checking despite errors

            logger.warning(f"Network did not become mostly idle within {timeout}ms")
            # Don't raise an exception, just return

        except Exception as e:
            logger.error(f"Error in wait_for_network_mostly_idle: {str(e)}")
            # Don't raise an exception, just return

    async def wait_for_selector(self, page: Page, selector: str, timeout: int):
        try:
            await page.wait_for_selector(selector, timeout=timeout)
        except TimeoutError:
            logger.warning(f"Timeout waiting for selector '{selector}': {timeout}ms")
            raise TimeoutException(f"Selector '{selector}' not found on the page within {timeout}ms")

    async def goto_with_timeout(self, page: Page, url: str, timeout: float = 5.0):
        try:
            await page.goto(str(url), wait_until='domcontentloaded', timeout=timeout * 1000)
        except TimeoutError:
            logger.warning(f"Navigation exceeded {timeout} seconds. Proceeding without waiting for full load.")
            raise TimeoutException(f"Navigation to {url} timed out after {timeout} seconds")

    async def wait_for_animations(self, page: Page, timeout: int = 5000):
        try:
            await page.evaluate(f"""
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