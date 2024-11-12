import asyncio
import logging
import time
import os
from playwright.async_api import Page, TimeoutError, Error as PlaywrightError
from context_manager import ContextManager
from controllers.main_controller import MainBrowserController
from exceptions import ScreenshotServiceException, TimeoutException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from tenacity.after import after_log
import ua_generator
from retry_tracker import before_retry

logger = logging.getLogger(__name__)


class CaptureService:
    def __init__(self):
        self.context_manager = None
        self.browser_controller = MainBrowserController()
        self._lock = asyncio.Lock()

    async def initialize(self, playwright):
        """Initialize the capture service with a Playwright instance."""
        try:
            self.context_manager = ContextManager(playwright=playwright)
            await self.context_manager.initialize(playwright)
            logger.info("Capture service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize capture service: {str(e)}")
            raise

    async def _get_valid_context(self, options):
        """Get a valid browser context, recreating if necessary."""
        async with self._lock:
            try:
                context = await self.context_manager.get_context(options)
                # Verify context is still valid
                try:
                    test_page = await context.new_page()
                    await test_page.close()
                    return context
                except PlaywrightError:
                    logger.warning("Detected invalid context, recreating...")
                    # Context is invalid, force cleanup and recreation
                    await self.context_manager._force_cleanup()
                    return await self.context_manager.get_context(options)
            except Exception as e:
                logger.error(f"Error getting valid context: {str(e)}")
                # Attempt recovery by reinitializing
                try:
                    await self.context_manager._force_cleanup()
                    return await self.context_manager.get_context(options)
                except Exception as reinit_error:
                    logger.error(f"Failed to recover context: {str(reinit_error)}")
                    raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((TimeoutError, TimeoutException, PlaywrightError)),
        after=after_log(logger, logging.ERROR),
        before=before_retry,
        reraise=True
    )
    async def capture_screenshot(self, output_path, options):
        """Main capture method with improved error handling and context validation."""
        try:
            if not self.context_manager:
                raise ScreenshotServiceException("Capture service not initialized")

            context = await self._get_valid_context(options)
            page = None

            try:
                page = await context.new_page()
                await self._configure_page(page, options)
                await self._load_content(page, options)
                await self._prepare_page(page, options)
                await self._perform_interactions(page, options)
                await self._perform_capture(page, output_path, options)
            except Exception as e:
                if isinstance(e, TimeoutError):
                    logger.warning(f"Timeout during capture: {str(e)}. Attempting to save partial result...")
                    if page:
                        await self._perform_capture(page, output_path, options)
                elif isinstance(e, PlaywrightError) and "Target page, context or browser has been closed" in str(e):
                    logger.warning("Browser context was closed, retrying with new context...")
                    raise  # This will trigger the retry mechanism
                else:
                    raise
            finally:
                if page:
                    try:
                        await page.close()
                    except PlaywrightError:
                        logger.warning("Failed to close page, it may already be closed")

        except Exception as e:
            retry_state = getattr(self.capture_screenshot, 'retry_state', None)
            attempts = []
            if retry_state and hasattr(retry_state, 'retry_tracker'):
                attempts = retry_state.retry_tracker.get_attempts()

            error_details = {
                "message": str(e),
                "type": e.__class__.__name__,
                "retry_attempts": attempts,
                "call_stack": getattr(e, 'message', str(e))
            }

            if isinstance(e, TimeoutError):
                if output_path and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return  # Successfully saved a partial screenshot

            raise ScreenshotServiceException(error_details)

    async def _configure_page(self, page: Page, options):
        """Configure page settings based on capture options."""
        try:
            await page.set_viewport_size({"width": options.window_width, "height": options.window_height})

            headers = {}
            if options.use_random_user_agent:
                ua = ua_generator.generate(
                    device=options.user_agent_device,
                    platform=options.user_agent_platform,
                    browser=options.user_agent_browser
                )
                headers = ua.headers.get()

            if options.custom_headers:
                headers.update(options.custom_headers)

            if headers:
                await page.set_extra_http_headers(headers)

            if options.proxy_server and options.proxy_port:
                await page.route("**/*", lambda route: route.continue_({
                    "proxy": {
                        "server": f"{options.proxy_server}:{options.proxy_port}",
                        "username": options.proxy_username,
                        "password": options.proxy_password
                    }
                }))

            if options.block_media:
                await page.route(
                    "**/*.{png,jpg,jpeg,gif,svg,ico,mp4,webm,ogg,mp3,wav,webp}",
                    lambda route: route.abort()
                )
        except PlaywrightError as e:
            logger.error(f"Error configuring page: {str(e)}")
            raise

    async def _load_content(self, page: Page, options):
        """Load the content to be captured."""
        try:
            if options.url:
                logger.info(f"Loading {options.url}...")
                await self.browser_controller.goto_with_timeout(page, options.url, options.wait_for_timeout / 1000)
            elif options.html_content:
                logger.info("Loading provided HTML content...")
                await page.set_content(options.html_content, wait_until='domcontentloaded')
        except Exception as e:
            logger.error(f"Error loading content: {str(e)}")
            raise

    async def _prepare_page(self, page: Page, options):
        """Prepare the page for capture."""
        try:
            await self.browser_controller.prepare_page(page, options)
        except Exception as e:
            logger.error(f"Error preparing page: {str(e)}")
            raise

    async def _perform_capture(self, page: Page, output_path, options):
        """Perform the actual capture with improved error handling."""
        try:
            if options.format == 'pdf':
                await self._capture_pdf(page, output_path, options)
            else:
                screenshot_data = None
                try:
                    if options.full_page:
                        await self.browser_controller.prepare_for_full_page_screenshot(page, options.window_width)
                    screenshot_data = await page.screenshot(
                        path=None,  # Don't save directly to file yet
                        full_page=options.full_page,
                        type=options.format,
                        quality=options.image_quality if options.format != 'png' else None,
                        omit_background=options.omit_background,
                        timeout=30000  # 30 second timeout
                    )
                except TimeoutError as e:
                    logger.warning(f"Screenshot timeout occurred: {str(e)}. Attempting fallback capture...")
                    screenshot_data = await page.screenshot(
                        path=None,
                        full_page=options.full_page,
                        type=options.format,
                        quality=options.image_quality if options.format != 'png' else None,
                        omit_background=options.omit_background,
                        timeout=0  # No timeout for fallback attempt
                    )

                if screenshot_data:
                    with open(output_path, 'wb') as f:
                        f.write(screenshot_data)
                else:
                    raise ScreenshotServiceException("Failed to capture screenshot")

        except Exception as e:
            logger.error(f"Error during capture: {str(e)}")
            raise ScreenshotServiceException(str(e))

    async def _perform_interactions(self, page: Page, options):
        """Perform any specified interactions before capture."""
        try:
            if options.interactions:
                await self.browser_controller.perform_interactions(page, options.interactions)
        except Exception as e:
            logger.error(f"Error performing interactions: {str(e)}")
            raise

    async def _capture_pdf(self, page: Page, output_path, options):
        """Capture PDF output."""
        try:
            pdf_options = {k: v for k, v in options.dict().items() if k.startswith('pdf_') and v is not None}
            await page.pdf(path=output_path, **pdf_options)
        except Exception as e:
            logger.error(f"Error capturing PDF: {str(e)}")
            raise

    async def _take_screenshot(self, page: Page, output_path, options, full_page: bool):
        """Take a screenshot with the specified options."""
        try:
            screenshot_options = {
                'path': output_path,
                'full_page': full_page,
                'type': options.format,
                'quality': options.image_quality if options.format != 'png' else None,
                'omit_background': options.omit_background,
            }

            if options.selector:
                element = await page.query_selector(options.selector)
                if element:
                    await element.screenshot(**screenshot_options)
                else:
                    raise ScreenshotServiceException(f"Selector '{options.selector}' not found on the page.")
            else:
                await page.screenshot(**screenshot_options)
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            raise

    async def close(self):
        """Clean up resources."""
        try:
            if self.context_manager:
                await self.context_manager.close()
        except Exception as e:
            logger.error(f"Error closing capture service: {str(e)}")
            raise