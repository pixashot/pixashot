import asyncio
import logging
from playwright.async_api import Page
from context_manager import ContextManager
from controllers.main_controller import MainBrowserController
from exceptions import ScreenshotServiceException

logger = logging.getLogger(__name__)

class CaptureService:
    def __init__(self, playwright=None):
        self.context_manager = ContextManager(playwright)
        self.browser_controller = MainBrowserController()

    async def initialize(self, playwright):
        self.context_manager = ContextManager(playwright)
        await self.context_manager.initialize(playwright)

    async def capture_screenshot(self, output_path, options):
        max_retries = 2
        retry_delay = 1

        for attempt in range(max_retries + 1):
            try:
                context = await self.context_manager.get_context(options)
                page = await context.new_page()

                await self._configure_page(page, options)
                await self._load_content(page, options)
                await self._prepare_page(page, options)
                await self._perform_interactions(page, options)
                await self._perform_capture(page, output_path, options)

                return
            except Exception as e:
                logger.error(f'Error during capture (attempt {attempt + 1}/{max_retries + 1}): {str(e)}')
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    continue
                raise ScreenshotServiceException(f"Failed to capture after {max_retries} attempts: {str(e)}")

    async def _configure_page(self, page: Page, options):
        await page.set_viewport_size({"width": options.window_width, "height": options.window_height})

        if options.proxy_server and options.proxy_port:
            await page.route("**/*", lambda route: route.continue_({
                "proxy": {
                    "server": f"{options.proxy_server}:{options.proxy_port}",
                    "username": options.proxy_username,
                    "password": options.proxy_password
                }
            }))

        if options.custom_headers:
            await page.set_extra_http_headers(options.custom_headers)

        if options.block_media:
            await page.route("**/*.{png,jpg,jpeg,gif,svg,ico,mp4,webm,ogg,mp3,wav}", lambda route: route.abort())

    async def _load_content(self, page: Page, options):
        if options.url:
            logger.info(f"Loading {options.url}...")
            await self.browser_controller.goto_with_timeout(page, options.url, options.wait_for_timeout / 1000)
        elif options.html_content:
            logger.info("Loading provided HTML content...")
            await page.set_content(options.html_content, wait_until='domcontentloaded')

    async def _prepare_page(self, page: Page, options):
        await self.browser_controller.prepare_page(page, options)

    async def _perform_capture(self, page: Page, output_path, options):
        if options.format == 'pdf':
            await self._capture_pdf(page, output_path, options)
        elif options.full_page:
            await self._capture_full_page_screenshot(page, output_path, options)
        else:
            await self._capture_viewport_screenshot(page, output_path, options)

    async def _perform_interactions(self, page: Page, options):
        if options.interactions:
            await self.browser_controller.perform_interactions(page, options.interactions)

    async def _capture_pdf(self, page: Page, output_path, options):
        pdf_options = {k: v for k, v in options.dict().items() if k.startswith('pdf_') and v is not None}
        await page.pdf(path=output_path, **pdf_options)

    async def _capture_full_page_screenshot(self, page: Page, output_path, options):
        await self.browser_controller.prepare_for_full_page_screenshot(page, options.window_width)
        await self._take_screenshot(page, output_path, options, full_page=True)

    async def _capture_viewport_screenshot(self, page: Page, output_path, options):
        await self._take_screenshot(page, output_path, options, full_page=False)

    async def _take_screenshot(self, page: Page, output_path, options, full_page: bool):
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

    async def close(self):
        await self.context_manager.close()