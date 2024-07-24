from playwright.sync_api import sync_playwright
from context_creator import ContextCreator
from browser_controller import BrowserController
import time


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
                    print(f"Loading {url}...")
                    self.browser_controller.goto_with_timeout(page, url)
                    print(f'Initial page load complete! Time taken: {time.time() - start_time:.2f}s')

                    self._prepare_page(page, options)

                    if options.full_page:
                        print('Capturing full page screenshot...')
                        self.capture_full_page_screenshot(page, output_path, options)
                    else:
                        print('Capturing viewport screenshot...')
                        self.capture_viewport_screenshot(page, output_path, options)

                    print(f'Screenshot captured! Total time: {time.time() - start_time:.2f}s')
                    return
            except Exception as error:
                print(f'Error during screenshot capture (attempt {attempt + 1}/{max_retries + 1}): {error}')
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue
                raise

    def _prepare_page(self, page, options):
        start_time = time.time()

        self.browser_controller.wait_for_page_load(page, options.wait_for_timeout)
        print(f'Page loaded! Time taken: {time.time() - start_time:.2f}s')

        self.browser_controller.inject_and_execute_scripts(page)
        print(f'Scripts injected and executed. Time taken: {time.time() - start_time:.2f}s')

        if options.custom_js:
            page.evaluate(options.custom_js)
            print(f'Custom JS executed. Time taken: {time.time() - start_time:.2f}s')

        if options.wait_for_selector:
            page.wait_for_selector(options.wait_for_selector, timeout=options.wait_for_timeout)
            print(f'Waited for selector. Time taken: {time.time() - start_time:.2f}s')

    def capture_full_page_screenshot(self, page, output_path, options):
        self.browser_controller.prepare_for_full_page_screenshot(page, options.windowWidth)
        self._take_screenshot(page, output_path, options, full_page=True)

    def capture_viewport_screenshot(self, page, output_path, options):
        self.browser_controller.prepare_for_viewport_screenshot(page, options.windowWidth, options.windowHeight)
        self._take_screenshot(page, output_path, options, full_page=False)

    def _take_screenshot(self, page, output_path, options, full_page):
        screenshot_options = {
            'path': output_path,
            'full_page': full_page,
            'quality': options.image_quality if options.format != 'png' else None,
            'omit_background': options.omit_background,
            'type': options.format,
        }

        if options.selector:
            element = page.query_selector(options.selector)
            if element:
                element.screenshot(**screenshot_options)
            else:
                raise ValueError(f"Selector '{options.selector}' not found on the page.")
        else:
            page.screenshot(**screenshot_options)