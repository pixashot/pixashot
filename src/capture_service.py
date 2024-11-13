import logging
from playwright.async_api import Page
from exceptions import ScreenshotServiceException
from context_manager import ContextManager

logger = logging.getLogger(__name__)


class CaptureService:
    def __init__(self):
        self.context_manager = None

    async def initialize(self, playwright):
        self.context_manager = ContextManager(playwright)
        await self.context_manager.initialize(playwright)

    async def capture_screenshot(self, output_path, options):
        try:
            context = await self.context_manager.get_context(options)
            page = await context.new_page()

            try:
                # Basic setup
                await page.set_viewport_size({
                    "width": options.window_width,
                    "height": options.window_height
                })

                # Single navigation with timeout handling
                if options.url:
                    try:
                        await page.goto(str(options.url),
                                        wait_until='domcontentloaded',  # Less strict wait condition
                                        timeout=options.wait_for_timeout)
                    except Exception as nav_error:
                        logger.warning(f"Navigation timeout or error: {str(nav_error)}. Continuing with capture...")

                        # Give a small additional wait to allow more content to load
                        try:
                            await page.wait_for_timeout(1000)  # Wait an extra second
                        except:
                            pass

                else:
                    await page.set_content(options.html_content)

                # Optional wait for network idle with shorter timeout
                try:
                    await page.wait_for_load_state('networkidle', timeout=2000)
                except Exception as wait_error:
                    logger.warning(f"Network idle timeout: {str(wait_error)}. Proceeding with capture...")

                # Take screenshot of whatever we have
                await page.screenshot(
                    path=output_path,
                    full_page=options.full_page,
                    type=options.format,
                    quality=options.image_quality if options.format != 'png' else None
                )

            finally:
                await page.close()

        except Exception as e:
            logger.error(f"Screenshot capture error: {str(e)}")
            raise ScreenshotServiceException(str(e))

    async def close(self):
        if self.context_manager:
            await self.context_manager.close()