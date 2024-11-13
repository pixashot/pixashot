import asyncio
import os
import logging
from typing import Dict, Optional
from playwright.async_api import Page
from exceptions import BrowserException, JavaScriptExecutionException
from controllers.interaction_controller import InteractionController
from controllers.screenshot_controller import ScreenshotController

logger = logging.getLogger(__name__)


class MainBrowserController:
    def __init__(self):
        self.interaction_controller = InteractionController()
        self.screenshot_controller = ScreenshotController()

        # Initialize paths for JS files (moved from ContentController)
        self.dynamic_content_detector_path = os.path.join(os.path.dirname(__file__),
                                                          '../js/dynamic-content-detector.js')
        self.dark_mode_js_path = os.path.join(os.path.dirname(__file__), '../js/dark-mode.js')

    async def prepare_page(self, page: Page, options):
        """Prepare page with improved error handling and more resilient network waiting."""
        try:
            await self.prevent_horizontal_overflow(page)

            # Combine network waits into a single operation with better error handling
            if options.wait_for_network in ('idle', 'mostly_idle'):
                try:
                    # Use shorter timeout for network wait
                    timeout = min(options.wait_for_timeout, 5000)
                    if options.wait_for_network == 'idle':
                        try:
                            await self.interaction_controller.wait_for_network_idle(page, timeout)
                        except Exception as e:
                            logger.warning(f"Network idle wait failed, continuing: {str(e)}")
                    else:
                        try:
                            await self.interaction_controller.wait_for_network_mostly_idle(page, timeout)
                        except Exception as e:
                            logger.warning(f"Network mostly idle wait failed, continuing: {str(e)}")
                    setattr(page, '_waited_for_network', True)
                except Exception as e:
                    logger.warning(f"Network wait failed, continuing with page preparation: {str(e)}")

            # Execute independent operations in parallel with error handling
            tasks = []
            if options.dark_mode:
                tasks.append(self.apply_dark_mode(page))
            if options.geolocation:
                tasks.append(self.set_geolocation(page, options.geolocation))

            if tasks:
                try:
                    await asyncio.gather(*tasks, return_exceptions=True)
                except Exception as e:
                    logger.warning(f"Some page preparation tasks failed: {str(e)}")

            if options.wait_for_animation:
                try:
                    await self.interaction_controller.wait_for_animations(page, timeout=2000)
                except Exception as e:
                    logger.warning(f"Animation wait failed, continuing: {str(e)}")

            if options.custom_js:
                try:
                    await self.execute_custom_js(page, options.custom_js)
                except Exception as e:
                    logger.warning(f"Custom JS execution failed: {str(e)}")

            if options.wait_for_selector:
                try:
                    await self.interaction_controller.wait_for_selector(
                        page,
                        options.wait_for_selector,
                        min(options.wait_for_timeout, 5000)
                    )
                except Exception as e:
                    logger.warning(f"Selector wait failed: {str(e)}")

            logger.info('Page prepared successfully')
        except Exception as e:
            logger.error(f"Error preparing page: {str(e)}")
            error_message = f"Failed to prepare page: {str(e)}"
            raise BrowserException(error_message) from e

    # Content management methods (moved from ContentController)
    async def execute_custom_js(self, page: Page, custom_js: str):
        """Execute custom JavaScript on the page."""
        try:
            await page.evaluate(custom_js)
        except Exception as e:
            logger.error(f"Error executing custom JavaScript: {str(e)}")
            raise JavaScriptExecutionException(f"Error executing custom JavaScript: {str(e)}")

    async def wait_for_dynamic_content(self, page: Page, check_interval: int = 1000, max_unchanged_checks: int = 5):
        """Wait for dynamic content to finish loading."""
        try:
            with open(self.dynamic_content_detector_path, 'r') as file:
                js_content = file.read()
                await page.evaluate(js_content)
            await page.evaluate(f'detectDynamicContentLoading({check_interval}, {max_unchanged_checks})')
        except Exception as e:
            logger.error(f"Error waiting for dynamic content: {str(e)}")
            raise JavaScriptExecutionException(f"Failed to wait for dynamic content: {str(e)}")

    async def apply_dark_mode(self, page: Page):
        """Apply dark mode to the page."""
        try:
            with open(self.dark_mode_js_path, 'r') as file:
                dark_mode_js = file.read()
            await page.evaluate(dark_mode_js)
            logger.info("Dark mode applied successfully")
        except Exception as e:
            logger.error(f"Error applying dark mode: {str(e)}")
            raise JavaScriptExecutionException(f"Failed to apply dark mode: {str(e)}")

    async def prevent_horizontal_overflow(self, page: Page):
        """Prevent horizontal overflow on the page."""
        try:
            await page.evaluate("""
                () => {
                    const style = document.createElement('style');
                    style.textContent = `
                        body, html {
                            max-width: 100vw !important;
                            overflow-x: hidden !important;
                        }
                    `;
                    document.head.appendChild(style);
                }
            """)
        except Exception as e:
            logger.error(f"Error preventing horizontal overflow: {str(e)}")
            raise JavaScriptExecutionException(f"Failed to prevent horizontal overflow: {str(e)}")

    # Geolocation methods (moved from GeolocationController)
    async def set_geolocation(self, page: Page, location: Optional[Dict[str, float]]):
        """Set the geolocation for the page."""
        if location is None:
            logger.info("No geolocation set, skipping geolocation configuration")
            return

        try:
            context = page.context
            await context.grant_permissions(['geolocation'])
            await context.set_geolocation(location)

            # Handle both dictionary and mock object
            latitude = location['latitude'] if isinstance(location, dict) else location.latitude
            longitude = location['longitude'] if isinstance(location, dict) else location.longitude
            accuracy = location['accuracy'] if isinstance(location, dict) else location.accuracy

            await page.add_init_script(f"""
                const mockGeolocation = {{
                    getCurrentPosition: (success) => {{
                        success({{
                            coords: {{
                                latitude: {latitude},
                                longitude: {longitude},
                                accuracy: {accuracy},
                                altitude: null,
                                altitudeAccuracy: null,
                                heading: null,
                                speed: null
                            }},
                            timestamp: Date.now()
                        }});
                    }},
                    watchPosition: (success) => {{
                        success({{
                            coords: {{
                                latitude: {latitude},
                                longitude: {longitude},
                                accuracy: {accuracy},
                                altitude: null,
                                altitudeAccuracy: null,
                                heading: null,
                                speed: null
                            }},
                            timestamp: Date.now()
                        }});
                        return 0;
                    }},
                }};
                Object.defineProperty(navigator, 'geolocation', {{
                    value: mockGeolocation,
                    configurable: true,
                }});
            """)

            logger.info(f"Geolocation set to: {location}")
        except Exception as e:
            logger.error(f"Error setting geolocation: {str(e)}")
            raise BrowserException(f"Failed to set geolocation: {str(e)}")

    # Screenshot preparation methods (delegated to ScreenshotController)
    async def prepare_for_full_page_screenshot(self, page: Page, window_width: int):
        """Prepare for taking a full page screenshot."""
        return await self.screenshot_controller.prepare_for_full_page_screenshot(page, window_width)

    async def prepare_for_viewport_screenshot(self, page: Page, window_width: int, window_height: int):
        """Prepare for taking a viewport screenshot."""
        return await self.screenshot_controller.prepare_for_viewport_screenshot(page, window_width, window_height)

    # Interaction methods (delegated to InteractionController)
    async def goto_with_timeout(self, page: Page, url: str, timeout: float = 5.0):
        """Navigate to a URL with timeout."""
        return await self.interaction_controller.goto_with_timeout(page, url, timeout)

    async def perform_interactions(self, page: Page, interactions: list):
        """Perform a series of interactions on the page."""
        return await self.interaction_controller.perform_interactions(page, interactions)