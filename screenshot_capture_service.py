import os
import tempfile
import time

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


class ScreenshotCaptureService:
    def __init__(self):
        self.proxy_config = None
        self.js_file_path = os.path.join(os.path.dirname(__file__), 'page-utils.js')

    def setup_proxy(self, proxy_server, proxy_port, proxy_username=None, proxy_password=None):
        self.proxy_config = {
            'server': f"{proxy_server}:{proxy_port}",
        }
        if proxy_username and proxy_password:
            self.proxy_config['username'] = proxy_username
            self.proxy_config['password'] = proxy_password

    def init(self):
        temp_dir = tempfile.gettempdir()
        user_data_dir = os.path.join(temp_dir, 'chrome-user-data')

        extensions = [
            os.path.join(os.path.dirname(__file__), 'extensions/popup-off'),
            os.path.join(os.path.dirname(__file__), 'extensions/dont-care-cookies'),
        ]

        disable_extensions_arg = f"--disable-extensions-except={','.join(extensions)}"
        load_extension_args = [f"--load-extension={ext}" for ext in extensions]

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir,
                headless=False,
                ignore_https_errors=True,
                device_scale_factor=2.0,
                args=[
                    disable_extensions_arg,
                    *load_extension_args,
                    '--autoplay-policy=no-user-gesture-required',
                    '--disable-gpu',
                    '--disable-accelerated-2d-canvas',
                    '--disable-accelerated-video-decode',
                    '--disable-gpu-compositing',
                    '--disable-gpu-rasterization',
                    '--no-sandbox'
                ],
                proxy=self.proxy_config
            )
            return browser

    def goto_with_timeout(self, page, url):
        try:
            page.goto(url, wait_until='networkidle', timeout=20000)
        except TimeoutError:
            print("Navigation exceeded 20 seconds. Proceeding without waiting for network idle.")

    def get_scroll_height(self, page):
        return page.evaluate("() => document.documentElement.scrollHeight")

    def scroll_to(self, page, target_position):
        page.evaluate(f"window.scrollTo(0, {target_position})")

    def capture_screenshot(self, url, output_path, width=1280, height=1280, pixel_density=2.0):
        with self.init() as browser:
            page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=pixel_density)

            try:
                print(f"Loading {url}...")
                self.goto_with_timeout(page, url)
                print('Finished loading!')

                page.wait_for_load_state('networkidle', timeout=30000)
                print('Page loaded!')

                # Load and execute the JavaScript file
                with open(self.js_file_path, 'r') as file:
                    js_content = file.read()
                    page.evaluate(js_content)

                # Use the loaded JavaScript functions
                page.evaluate('pageUtils.disableSmoothScrolling()')
                page.evaluate('pageUtils.waitForAllImages()')

                print('All images loaded')

                # Scroll to bottom of the page
                print('Scrolling to bottom of page...')
                self.scroll_to_bottom(page, max_scrolls=5, scroll_timeout=10)

                # Get the full height of the page after scrolling
                full_height = page.evaluate('pageUtils.getFullHeight()')

                # Set the viewport to the full height of the page
                page.set_viewport_size({'width': width, 'height': full_height})

                # Scroll back to top
                self.scroll_to(page, 0)
                page.wait_for_timeout(2000)

                print('Capturing screenshot...')
                page.screenshot(path=output_path, full_page=True)

                print('Screenshot captured!')
            except PlaywrightTimeoutError:
                print('Timeout occurred, but continuing with screenshot capture')
                page.screenshot(path=output_path, full_page=True)
            except Exception as error:
                print('Error during screenshot capture:', error)
                raise
            finally:
                print('Closing browser.')
                page.close()

    def scroll_to_bottom(self, page, max_scrolls=10, scroll_timeout=30):
        previous_height = 0
        scroll_count = 0
        start_time = time.time()

        while scroll_count < max_scrolls and (time.time() - start_time) < scroll_timeout:
            current_height = page.evaluate('() => document.body.scrollHeight')
            if current_height == previous_height:
                print("Reached the bottom of the page or no new content loaded.")
                break

            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(2000)  # Wait for 2 seconds to allow content to load

            scroll_count += 1
            previous_height = current_height

            print(f"Scroll {scroll_count}/{max_scrolls} completed. Current height: {current_height}")

        if scroll_count == max_scrolls:
            print(f"Reached maximum number of scrolls ({max_scrolls}).")
        elif (time.time() - start_time) >= scroll_timeout:
            print(f"Scroll operation timed out after {scroll_timeout} seconds.")