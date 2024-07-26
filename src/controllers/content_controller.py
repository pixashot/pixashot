import os
import logging
from playwright.async_api import Page
from exceptions import JavaScriptExecutionException
from controllers.base_controller import BaseBrowserController

logger = logging.getLogger(__name__)


class ContentController(BaseBrowserController):
    def __init__(self):
        super().__init__()
        self.dynamic_content_detector_path = os.path.join(os.path.dirname(__file__),
                                                          '../js/dynamic-content-detector.js')
        self.dark_mode_js_path = os.path.join(os.path.dirname(__file__), '../js/dark-mode.js')

    async def wait_for_dynamic_content(self, page: Page, check_interval: int = 1000, max_unchanged_checks: int = 5):
        try:
            with open(self.dynamic_content_detector_path, 'r') as file:
                js_content = file.read()
                await page.evaluate(js_content)
            await page.evaluate(f'detectDynamicContentLoading({check_interval}, {max_unchanged_checks})')
        except Exception as e:
            logger.error(f"Error waiting for dynamic content: {str(e)}")
            raise JavaScriptExecutionException(f"Failed to wait for dynamic content: {str(e)}")

    async def apply_dark_mode(self, page: Page):
        try:
            with open(self.dark_mode_js_path, 'r') as file:
                dark_mode_js = file.read()
            await page.evaluate(dark_mode_js)
            logger.info("Dark mode applied successfully")
        except Exception as e:
            logger.error(f"Error applying dark mode: {str(e)}")
            raise JavaScriptExecutionException(f"Failed to apply dark mode: {str(e)}")

    async def prevent_horizontal_overflow(self, page: Page):
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