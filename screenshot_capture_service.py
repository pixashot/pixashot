from playwright.sync_api import sync_playwright
from context_creator import ContextCreator
from browser_controller import BrowserController


class ScreenshotCaptureService:
    MAX_VIEWPORT_HEIGHT = 16384

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

                with open(self.browser_controller.js_file_path, 'r') as file:
                    js_content = file.read()
                    page.evaluate(js_content)

                page.evaluate('pageUtils.disableSmoothScrolling()')
                page.evaluate('pageUtils.waitForAllImages()')

                print('All images loaded')

                if options.scroll_to_bottom:
                    print('Scrolling to bottom of page...')
                    self.browser_controller.scroll_to_bottom(page, options.max_scrolls, options.scroll_timeout)

                if options.wait_for_selector:
                    page.wait_for_selector(options.wait_for_selector, timeout=options.wait_for_timeout)

                if options.custom_js:
                    page.evaluate(options.custom_js)

                if options.full_page:
                    full_height = page.evaluate('pageUtils.getFullHeight()')
                    full_height = min(full_height, self.MAX_VIEWPORT_HEIGHT)
                    page.set_viewport_size({'width': options.windowWidth, 'height': full_height})
                else:
                    page.set_viewport_size({'width': options.windowWidth, 'height': options.windowHeight})

                self.browser_controller.scroll_to(page, 0)
                page.wait_for_timeout(2000)

                print('Capturing screenshot...')
                screenshot_options = {
                    'path': output_path,
                    'full_page': options.full_page,
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

                print('Screenshot captured!')
            except Exception as error:
                print('Error during screenshot capture:', error)
                raise
            finally:
                print('Closing context.')
                context.close()