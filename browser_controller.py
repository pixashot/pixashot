import os
import tempfile
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

class BrowserController:
    def __init__(self):
        self.js_file_path = os.path.join(os.path.dirname(__file__), 'js/page-utils.js')
        self.dynamic_content_detector_path = os.path.join(os.path.dirname(__file__), 'js/dynamic-content-detector.js')

    def create_context(self, playwright, options):
        temp_dir = tempfile.gettempdir()
        user_data_dir = os.path.join(temp_dir, 'chrome-user-data')

        extensions = [
            os.path.join(os.path.dirname(__file__), 'extensions/popup-off'),
            os.path.join(os.path.dirname(__file__), 'extensions/dont-care-cookies'),
        ]

        disable_extensions_arg = f"--disable-extensions-except={','.join(extensions)}"
        load_extension_args = [f"--load-extension={ext}" for ext in extensions]

        context_options = {
            "user_data_dir": user_data_dir,
            "headless": options.get('headless', False),
            "ignore_https_errors": options.get('ignore_https_errors', True),
            "device_scale_factor": options.get('pixel_density', 2.0),
            "viewport": {
                "width": options.get('windowWidth', 1280),
                "height": options.get('windowHeight', 720)
            },
            "args": [
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
        }

        if options.get('proxy_server') and options.get('proxy_port'):
            context_options["proxy"] = {
                "server": f"{options['proxy_server']}:{options['proxy_port']}",
                "username": options.get('proxy_username'),
                "password": options.get('proxy_password')
            }

        return playwright.chromium.launch_persistent_context(**context_options)

    def goto_with_timeout(self, page, url):
        try:
            page.goto(url, wait_until='networkidle', timeout=5000)
        except TimeoutError:
            print("Navigation exceeded 20 seconds. Proceeding without waiting for network idle.")

    def get_scroll_height(self, page):
        return page.evaluate("() => document.documentElement.scrollHeight")

    def scroll_to(self, page, target_position):
        page.evaluate(f"window.scrollTo(0, {target_position})")
        page.wait_for_timeout(100)  # Short pause after each scroll

    def wait_for_page_load(self, page, timeout=5000):
        try:
            # Wait for the initial page load
            page.wait_for_load_state('networkidle', timeout=timeout)

            # Load and execute our custom JavaScript
            with open(self.dynamic_content_detector_path, 'r') as file:
                js_content = file.read()
                page.evaluate(js_content)

            # Call our custom function and wait for it to resolve
            page.evaluate('detectDynamicContentLoading(1000, 5)')

            print("Dynamic content finished loading")
        except Exception as e:
            print(f"Timeout or error waiting for dynamic content: {e}")

    def scroll_to_bottom(self, page, max_scrolls=10, scroll_timeout=30):
        previous_height = 0
        scroll_count = 0
        start_time = time.time()

        while scroll_count < max_scrolls and (time.time() - start_time) < scroll_timeout:
            current_height = page.evaluate('() => document.body.scrollHeight')
            if current_height == previous_height:
                print("Reached the bottom of the page or no new content loaded.")
                break

            # Scroll in smaller increments
            for i in range(0, current_height - previous_height, 200):
                self.scroll_to(page, previous_height + i)
                page.wait_for_timeout(100)  # Short pause between scrolls

            page.wait_for_timeout(2000)  # Wait for 2 seconds to allow content to load

            scroll_count += 1
            previous_height = current_height

            print(f"Scroll {scroll_count}/{max_scrolls} completed. Current height: {current_height}")

        if scroll_count == max_scrolls:
            print(f"Reached maximum number of scrolls ({max_scrolls}).")
        elif (time.time() - start_time) >= scroll_timeout:
            print(f"Scroll operation timed out after {scroll_timeout} seconds.")