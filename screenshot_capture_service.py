from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from browser_controller import BrowserController


class ScreenshotCaptureService:
    MAX_VIEWPORT_HEIGHT = 16384

    def __init__(self):
        self.browser_controller = BrowserController()

    def capture_screenshot(self, url, output_path, options):
        with sync_playwright() as p:
            context = self.browser_controller.create_context(p, options)
            page = context.new_page()

            try:
                print(f"Loading {url}...")
                self.browser_controller.goto_with_timeout(page, url)
                print('Initial page load complete!')

                self.browser_controller.wait_for_page_load(page, options.get('wait_for_timeout', 5000))
                print('Page loaded!')

                with open(self.browser_controller.js_file_path, 'r') as file:
                    js_content = file.read()
                    page.evaluate(js_content)

                page.evaluate('pageUtils.disableSmoothScrolling()')
                page.evaluate('pageUtils.waitForAllImages()')

                print('All images loaded')

                if options.get('scroll_to_bottom', True):
                    print('Scrolling to bottom of page...')
                    self.browser_controller.scroll_to_bottom(page, options.get('max_scrolls', 10), options.get('scroll_timeout', 30))

                full_height = page.evaluate('pageUtils.getFullHeight()')
                full_height = min(full_height, self.MAX_VIEWPORT_HEIGHT)

                page.set_viewport_size({'width': options.get('windowWidth', 1280), 'height': full_height})

                self.browser_controller.scroll_to(page, 0)
                page.wait_for_timeout(2000)

                print('Capturing screenshot...')
                page.screenshot(path=output_path, full_page=options.get('full_page', True))

                print('Screenshot captured!')
            except PlaywrightTimeoutError:
                print('Timeout occurred, but continuing with screenshot capture')
                page.screenshot(path=output_path, full_page=options.get('full_page', True))
            except Exception as error:
                print('Error during screenshot capture:', error)
                raise
            finally:
                print('Closing context.')
                context.close()