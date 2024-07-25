import os
import logging
from playwright.sync_api import Page
from exceptions import JavaScriptExecutionException
from controllers.base_controller import BaseBrowserController

logger = logging.getLogger(__name__)


class ContentController(BaseBrowserController):
    def __init__(self):
        super().__init__()
        self.js_file_path = os.path.join(os.path.dirname(__file__), '../js/page-utils.js')
        self.dynamic_content_detector_path = os.path.join(os.path.dirname(__file__),
                                                          '../js/dynamic-content-detector.js')
        self.dark_mode_js_path = os.path.join(os.path.dirname(__file__), '../js/dark-mode.js')

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
            with open(self.dark_mode_js_path, 'r') as file:
                dark_mode_js = file.read()
            page.evaluate(dark_mode_js)
            logger.info("Dark mode applied successfully")
        except Exception as e:
            logger.error(f"Error applying dark mode: {str(e)}")
            raise JavaScriptExecutionException(f"Failed to apply dark mode: {str(e)}")

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