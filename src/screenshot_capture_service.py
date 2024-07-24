import time
import logging
from playwright.sync_api import sync_playwright
from context_creator import ContextCreator
from browser_controller import BrowserController
from exceptions import ScreenshotServiceException, BrowserException, NetworkException, ElementNotFoundException, \
    JavaScriptExecutionException, TimeoutException
from PIL import Image
import io

logger = logging.getLogger(__name__)


class ScreenshotCaptureService:
    def __init__(self):
        self.context_creator = ContextCreator()
        self.browser_controller = BrowserController()

    def capture_screenshot(self, output_path, options):
        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries + 1):
            try:
                with sync_playwright() as p:
                    context = self.context_creator.create_context(p, options)
                    page = context.new_page()

                    start_time = time.time()
                    if options.url:
                        logger.info(f"Loading {options.url}...")
                        self.browser_controller.goto_with_timeout(page, options.url)
                    else:
                        logger.info("Loading provided HTML content...")
                        page.set_content(options.html_content)
                    logger.info(f'Initial page load complete! Time taken: {time.time() - start_time:.2f}s')

                    self._prepare_page(page, options)

                    if options.format == 'pdf':
                        logger.info('Capturing PDF...')
                        self.capture_pdf(page, output_path, options)
                    elif options.full_page:
                        logger.info('Capturing full page screenshot...')
                        self.capture_full_page_screenshot(page, output_path, options)
                    else:
                        logger.info('Capturing viewport screenshot...')
                        self.capture_viewport_screenshot(page, output_path, options)

                    logger.info(f'Capture complete! Total time: {time.time() - start_time:.2f}s')
                    return
            except (BrowserException, NetworkException, ElementNotFoundException, JavaScriptExecutionException,
                    TimeoutException) as e:
                logger.error(f'Error during capture (attempt {attempt + 1}/{max_retries + 1}): {str(e)}')
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue
                raise ScreenshotServiceException(f"Failed to capture after {max_retries} attempts: {str(e)}")
            except Exception as e:
                logger.exception("Unexpected error during capture")
                raise ScreenshotServiceException(f"Unexpected error during capture: {str(e)}")

    def _prepare_page(self, page, options):
        start_time = time.time()

        try:
            self.browser_controller.prepare_page(page, options)
            logger.info(f'Page prepared! Time taken: {time.time() - start_time:.2f}s')
        except (NetworkException, ElementNotFoundException, JavaScriptExecutionException, TimeoutException) as e:
            logger.error(f"Error preparing page: {str(e)}")
            raise

    def capture_full_page_screenshot(self, page, output_path, options):
        try:
            self.browser_controller.prepare_for_full_page_screenshot(page, options.window_width, options.window_height)
            self._take_screenshot(page, output_path, options, full_page=True)
            self._crop_screenshot_if_necessary(output_path, options.window_width, options.pixel_density)
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

    def _crop_screenshot_if_necessary(self, output_path, window_width, pixel_density):
        try:
            with Image.open(output_path) as img:
                target_width = int(window_width * pixel_density)
                if img.width > target_width:
                    logger.info(f"Cropping image from {img.width}px to {target_width}px width")
                    cropped_img = img.crop((0, 0, target_width, img.height))

                    # Save the cropped image in the same format as the original
                    cropped_img.save(output_path, format=img.format)
        except Exception as e:
            logger.error(f"Error cropping screenshot: {str(e)}")
            raise ScreenshotServiceException(f"Failed to crop screenshot: {str(e)}")

    def capture_pdf(self, page, output_path, options):
        try:
            pdf_options = {
                'path': output_path,
                'print_background': options.pdf_print_background,
                'scale': options.pdf_scale,
                'page_ranges': options.pdf_page_ranges,
                'format': options.pdf_format,
                'width': options.pdf_width,
                'height': options.pdf_height,
            }
            # Remove None values
            pdf_options = {k: v for k, v in pdf_options.items() if v is not None}
            page.pdf(**pdf_options)
        except Exception as e:
            logger.error(f"Error capturing PDF: {str(e)}")
            raise ScreenshotServiceException(f"Failed to capture PDF: {str(e)}")