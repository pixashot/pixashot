import time
import logging
from playwright.sync_api import sync_playwright
from context_creator import ContextCreator
from browser_controller import BrowserController
from exceptions import ScreenshotServiceException, BrowserException, NetworkException, ElementNotFoundException, JavaScriptExecutionException, TimeoutException

logger = logging.getLogger(__name__)

class ScreenshotCaptureService:
    def __init__(self):
        self.context_creator = ContextCreator()
        self.browser_controller = BrowserController()

    def capture_screenshot(self, url, output_path, options):
        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries + 1):
            try:
                with sync_playwright() as p:
                    context = self.context_creator.create_context(p, options)
                    page = context.new_page()

                    start_time = time.time()
                    logger.info(f"Loading {url}...")
                    self.browser_controller.goto_with_timeout(page, url)
                    logger.info(f'Initial page load complete! Time taken: {time.time() - start_time:.2f}s')

                    self._prepare_page(page, options)

                    if options.full_page:
                        logger.info('Capturing full page screenshot...')
                        self.capture_full_page_screenshot(page, output_path, options)
                    else:
                        logger.info('Capturing viewport screenshot...')
                        self.capture_viewport_screenshot(page, output_path, options)

                    logger.info(f'Screenshot captured! Total time: {time.time() - start_time:.2f}s')
                    return
            except (BrowserException, NetworkException, ElementNotFoundException, JavaScriptExecutionException, TimeoutException) as e:
                logger.error(f'Error during screenshot capture (attempt {attempt + 1}/{max_retries + 1}): {str(e)}')
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue
                raise ScreenshotServiceException(f"Failed to capture screenshot after {max_retries} attempts: {str(e)}")
            except Exception as e:
                logger.exception("Unexpected error during screenshot capture")
                raise ScreenshotServiceException(f"Unexpected error during screenshot capture: {str(e)}")

    def _prepare_page(self, page, options):
        start_time = time.time()

        try:
            self.browser_controller.prepare_page(page, options)
            logger.info(f'Page prepared! Time taken: {time.time() - start_time:.2f}s')

            if options.custom_js:
                self.browser_controller.execute_custom_js(page, options.custom_js)
                logger.info(f'Custom JS executed. Time taken: {time.time() - start_time:.2f}s')

            if options.wait_for_selector:
                self.browser_controller.wait_for_selector(page, options.wait_for_selector, options.wait_for_timeout)
                logger.info(f'Waited for selector. Time taken: {time.time() - start_time:.2f}s')
        except (NetworkException, ElementNotFoundException, JavaScriptExecutionException, TimeoutException) as e:
            logger.error(f"Error preparing page: {str(e)}")
            raise

    def capture_full_page_screenshot(self, page, output_path, options):
        try:
            self.browser_controller.prepare_for_full_page_screenshot(page, options.window_width)
            self._take_screenshot(page, output_path, options, full_page=True)
        except Exception as e:
            logger.error(f"Error capturing full page screenshot: {str(e)}")
            raise ScreenshotServiceException(f"Failed to capture full page screenshot: {str(e)}")

    def capture_viewport_screenshot(self, page, output_path, options):
        try:
            self.browser_controller.prepare_for_viewport_screenshot(page, options.window_width, options.window_height)
            self._take_screenshot(page, output_path, options, full_page=False)
        except Exception as e:
            logger.error(f"Error capturing viewport screenshot: {str(e)}")
            raise ScreenshotServiceException(f"Failed to capture viewport screenshot: {str(e)}")

    def _take_screenshot(self, page, output_path, options, full_page):
        screenshot_options = {
            'path': output_path,
            'full_page': full_page,
            'quality': options.image_quality if options.format != 'png' else None,
            'omit_background': options.omit_background,
            'type': options.format,
        }

        try:
            if options.selector:
                element = page.query_selector(options.selector)
                if element:
                    element.screenshot(**screenshot_options)
                else:
                    raise ElementNotFoundException(f"Selector '{options.selector}' not found on the page.")
            else:
                page.screenshot(**screenshot_options)
        except ElementNotFoundException as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            raise ScreenshotServiceException(f"Failed to take screenshot: {str(e)}")