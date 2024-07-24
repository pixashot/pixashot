from playwright.sync_api import sync_playwright
from context_creator import ContextCreator
from browser_controller import BrowserController


class ScreenshotCaptureService:
    def __init__(self):
        self.context_creator = ContextCreator()
        self.browser_controller = BrowserController()

    def capture_screenshot(self, url, output_path, options):
        with sync_playwright() as p:
            context = self.context_creator.create_context(p, options)
            page = context.new_page()

            try:
                print(f"Loading {url}...")
                self.browser_controller.goto_with_timeout(page, url)
                print('Initial page load complete!')

                self.browser_controller.wait_for_page_load(page, options.wait_for_timeout)
                print('Page loaded!')

                self.browser_controller.inject_and_execute_scripts(page)
                print('All images loaded')

                if options.custom_js:
                    page.evaluate(options.custom_js)

                if options.wait_for_selector:
                    page.wait_for_selector(options.wait_for_selector, timeout=options.wait_for_timeout)

                if options.full_page:
                    print('Capturing full page screenshot...')
                    self.capture_full_page_screenshot(page, output_path, options)
                else:
                    print('Capturing viewport screenshot...')
                    self.capture_viewport_screenshot(page, output_path, options)

                print('Screenshot captured!')
            except Exception as error:
                print('Error during screenshot capture:', error)
                raise
            finally:
                print('Closing context.')
                context.close()

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
