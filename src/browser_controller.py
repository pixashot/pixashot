import os
import logging
from playwright.sync_api import Page, TimeoutError
from typing import TypeVar
from exceptions import BrowserException, NetworkException, ElementNotFoundException, JavaScriptExecutionException, \
    TimeoutException

T = TypeVar('T')

logger = logging.getLogger(__name__)


class BrowserController:
    MAX_VIEWPORT_HEIGHT = 16384
    NETWORK_IDLE_TIMEOUT_MS = 1000
    SCROLL_PAUSE_MS = 500

    def __init__(self):
        self.js_file_path = os.path.join(os.path.dirname(__file__), 'js/page-utils.js')
        self.dynamic_content_detector_path = os.path.join(os.path.dirname(__file__), 'js/dynamic-content-detector.js')
        self.dark_mode_js_path = os.path.join(os.path.dirname(__file__), 'js/dark-mode.js')

    def goto_with_timeout(self, page: Page, url: str, timeout: float = 5.0):
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=timeout * 1000)
        except TimeoutError:
            logger.warning(f"Navigation exceeded {timeout} seconds. Proceeding without waiting for full load.")
            raise TimeoutException(f"Navigation to {url} timed out after {timeout} seconds")

    def prepare_page(self, page: Page, options):
        try:
            self.inject_scripts(page)
            self.prevent_horizontal_overflow(page)
            if options.dark_mode:
                self.apply_dark_mode(page)
            self.wait_for_network_idle(page, options.wait_for_timeout)
            if options.custom_js:
                self.execute_custom_js(page, options.custom_js)
            if options.wait_for_selector:
                self.wait_for_selector(page, options.wait_for_selector, options.wait_for_timeout)
        except Exception as e:
            logger.error(f"Error preparing page: {str(e)}")
            raise BrowserException(f"Failed to prepare page: {str(e)}")

    def inject_scripts(self, page: Page):
        try:
            with open(self.js_file_path, 'r') as file:
                js_content = file.read()
                page.evaluate(js_content)
            page.evaluate('pageUtils.disableSmoothScrolling()')
            page.evaluate('pageUtils.waitForAllImages()')
        except Exception as e:
            logger.error(f"Error injecting scripts: {str(e)}")
            raise JavaScriptExecutionException(f"Failed to inject scripts: {str(e)}")

    def prevent_horizontal_overflow(self, page: Page):
        try:
            page.evaluate("""
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

    def wait_for_network_idle(self, page: Page, timeout: int):
        try:
            page.wait_for_load_state('networkidle', timeout=timeout)
        except TimeoutError as e:
            logger.warning(f"Timeout waiting for network idle: {timeout}ms")
            raise NetworkException(f"Timeout waiting for network idle: {timeout}ms")

    def execute_custom_js(self, page: Page, custom_js: str):
        try:
            page.evaluate(custom_js)
        except Exception as e:
            logger.error(f"Error executing custom JavaScript: {str(e)}")
            raise JavaScriptExecutionException(f"Error executing custom JavaScript: {str(e)}")

    def wait_for_selector(self, page: Page, selector: str, timeout: int):
        try:
            page.wait_for_selector(selector, timeout=timeout)
        except TimeoutError:
            logger.warning(f"Timeout waiting for selector '{selector}': {timeout}ms")
            raise ElementNotFoundException(f"Selector '{selector}' not found on the page within {timeout}ms")

    def prepare_for_full_page_screenshot(self, page: Page, window_width: int, window_height: int):
        try:
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            self.wait_for_network_idle(page, self.NETWORK_IDLE_TIMEOUT_MS)
            self._set_viewport_and_scroll(page, window_width, window_height)
        except Exception as e:
            logger.error(f"Error preparing for full page screenshot: {str(e)}")
            raise BrowserException(f"Failed to prepare for full page screenshot: {str(e)}")

    def prepare_for_viewport_screenshot(self, page: Page, window_width: int, window_height: int):
        try:
            self._set_viewport_and_scroll(page, window_width, window_height)
        except Exception as e:
            logger.error(f"Error preparing for viewport screenshot: {str(e)}")
            raise BrowserException(f"Failed to prepare for viewport screenshot: {str(e)}")

    # Utility functions

    def _set_viewport_and_scroll(self, page: Page, width: int, height: int):
        try:
            page.set_viewport_size({'width': width, 'height': height})
            self.wait_for_network_idle(page, self.NETWORK_IDLE_TIMEOUT_MS)
            page.evaluate('window.scrollTo(0, 0)')
            page.wait_for_timeout(self.SCROLL_PAUSE_MS)
        except Exception as e:
            logger.error(f"Error setting viewport and scrolling: {str(e)}")
            raise BrowserException(f"Failed to set viewport and scroll: {str(e)}")

    def wait_for_dynamic_content(self, page: Page, check_interval: int = 1000, max_unchanged_checks: int = 5):
        try:
            with open(self.dynamic_content_detector_path, 'r') as file:
                js_content = file.read()
                page.evaluate(js_content)
            page.evaluate(f'detectDynamicContentLoading({check_interval}, {max_unchanged_checks})')
        except Exception as e:
            logger.error(f"Error waiting for dynamic content: {str(e)}")
            raise JavaScriptExecutionException(f"Failed to wait for dynamic content: {str(e)}")

    def apply_dark_mode(self, page: Page):
        try:
            page.evaluate("""
                () => {
                    // Set color-scheme to dark
                    document.documentElement.style.colorScheme = 'dark';

                    // Add a meta tag for color-scheme if it doesn't exist
                    if (!document.querySelector('meta[name="color-scheme"]')) {
                        const meta = document.createElement('meta');
                        meta.name = 'color-scheme';
                        meta.content = 'dark';
                        document.head.appendChild(meta);
                    }

                    // Set prefers-color-scheme media query (for Tailwind's media strategy)
                    const darkModeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
                    Object.defineProperty(darkModeMediaQuery, 'matches', { get: () => true });
                    window.dispatchEvent(new Event('dark-mode-change'));

                    // Add 'dark' class to <html> element (for Tailwind's class strategy)
                    document.documentElement.classList.add('dark');

                    // Force update for sites using Tailwind's class strategy
                    if (window.Alpine) {
                        window.Alpine.store('darkMode').on();
                        window.Alpine.store('theme').setDarkMode();
                    }
                }
            """)
            logger.info("Dark mode preference applied successfully for Tailwind sites")
        except Exception as e:
            logger.error(f"Error applying dark mode preference: {str(e)}")
            raise JavaScriptExecutionException(f"Failed to apply dark mode preference: {str(e)}")