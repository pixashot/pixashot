import logging
from playwright.async_api import Page
from exceptions import ScreenshotServiceException
from controllers.main_controller import MainBrowserController
from controllers.screenshot_controller import ScreenshotController
from context_manager import ContextManager

logger = logging.getLogger(__name__)

class CaptureService:
    def __init__(self):
        self.main_controller = None
        self.screenshot_controller = None
        self.context_manager = None
        self.context = None
        self.playwright = None

    async def initialize(self, playwright):
        """Initialize the service with required controllers and context."""
        self.playwright = playwright
        self.main_controller = MainBrowserController()
        self.screenshot_controller = ScreenshotController()
        self.context_manager = ContextManager()
        self.context = await self.context_manager.initialize(playwright)

    async def _configure_page(self, page: Page, options) -> None:
        """Configure page with user agent and other settings."""
        if getattr(options, 'use_random_user_agent', True):
            headers = self.context_manager._generate_headers(options)
            await page.set_extra_http_headers(headers)
            logger.info(f"Using generated user agent: {headers.get('User-Agent')}")

    async def _resilient_navigation(self, page: Page, url: str, timeout: int):
        """Attempt navigation with fallback handling for timeouts."""
        try:
            await page.goto(
                str(url),
                wait_until='domcontentloaded',  # Less strict wait condition
                timeout=timeout
            )
        except Exception as nav_error:
            logger.warning(f"Navigation timeout or error: {str(nav_error)}. Continuing with capture...")

            # Give a small additional wait to allow more content to load
            try:
                await page.wait_for_timeout(1000)  # Wait an extra second
            except Exception as wait_error:
                logger.warning(f"Additional wait failed: {str(wait_error)}")

    async def capture_screenshot(self, output_path, options):
        """Capture screenshot using the configured controllers."""
        try:
            page = await self.context.new_page()

            try:
                # Configure page with user agent
                await self._configure_page(page, options)

                # Use MainController for page preparation
                await self.main_controller.prepare_page(page, options)

                # Handle URL navigation or HTML content with resilient navigation
                if options.url:
                    await self._resilient_navigation(page, str(options.url), options.wait_for_timeout)
                else:
                    await page.set_content(options.html_content)

                # Handle interactions if specified
                if options.interactions:
                    await self.main_controller.perform_interactions(page, options.interactions)

                # Prepare for screenshot based on options
                if options.full_page:
                    await self.main_controller.prepare_for_full_page_screenshot(page, options.window_width)
                else:
                    await self.main_controller.prepare_for_viewport_screenshot(
                        page,
                        options.window_width,
                        options.window_height
                    )

                # Take the actual screenshot using ScreenshotController
                await self.screenshot_controller.take_screenshot(page, {
                    'path': output_path,
                    'full_page': options.full_page,
                    'format': options.format,
                    'quality': options.image_quality if options.format != 'png' else None,
                    'omit_background': options.omit_background
                })

            finally:
                await page.close()

        except Exception as e:
            logger.error(f"Screenshot capture error: {str(e)}")
            raise ScreenshotServiceException(str(e))

    async def close(self):
        """Clean up resources."""
        if self.context_manager:
            await self.context_manager.close()