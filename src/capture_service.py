import asyncio
import logging
from playwright.async_api import Page
from context_manager import ContextManager
from controllers.main_controller import MainBrowserController
from exceptions import ScreenshotServiceException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from tenacity.after import after_log
import ua_generator

logger = logging.getLogger(__name__)


class CaptureService:
    def __init__(self):
        self.context_manager = None
        self.browser_controller = MainBrowserController()

    async def initialize(self, playwright):
        """Initialize the capture service with a Playwright instance."""
        try:
            self.context_manager = ContextManager(playwright=playwright)
            await self.context_manager.initialize(playwright)
            logger.info("Capture service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize capture service: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        after=after_log(logger, logging.ERROR)
    )
    async def capture_screenshot(self, output_path, options):
        if not self.context_manager:
            raise ScreenshotServiceException("Capture service not initialized")

        context = await self.context_manager.get_context(options)
        page = await context.new_page()

        await self._configure_page(page, options)
        await self._load_content(page, options)
        await self._prepare_page(page, options)
        await self._perform_interactions(page, options)
        await self._perform_capture(page, output_path, options)

    async def _configure_page(self, page: Page, options):
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
