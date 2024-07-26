import logging
from playwright.async_api import Page
from exceptions import JavaScriptExecutionException

logger = logging.getLogger(__name__)


class BaseBrowserController:
    def __init__(self):
        pass

    async def execute_custom_js(self, page: Page, custom_js: str):
        try:
            await page.evaluate(custom_js)
        except Exception as e:
            logger.error(f"Error executing custom JavaScript: {str(e)}")
            raise JavaScriptExecutionException(f"Error executing custom JavaScript: {str(e)}")