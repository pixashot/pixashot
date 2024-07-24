import os
import time

class BrowserController:
    MAX_VIEWPORT_HEIGHT = 16384

    def __init__(self):
        self.js_file_path = os.path.join(os.path.dirname(__file__), 'js/page-utils.js')
        self.dynamic_content_detector_path = os.path.join(os.path.dirname(__file__), 'js/dynamic-content-detector.js')

    def goto_with_timeout(self, page, url):
        try:
            page.goto(url, wait_until='networkidle', timeout=5000)
        except TimeoutError:
            print("Navigation exceeded 5 seconds. Proceeding without waiting for network idle.")

    def get_scroll_height(self, page):
        return page.evaluate("() => document.documentElement.scrollHeight")

    def scroll_to(self, page, target_position):
        page.evaluate(f"window.scrollTo(0, {target_position})")
        page.wait_for_timeout(100)  # Short pause after each scroll

    def wait_for_page_load(self, page, timeout=5000):
        try:
            page.wait_for_load_state('networkidle', timeout=timeout)
            with open(self.dynamic_content_detector_path, 'r') as file:
                js_content = file.read()
                page.evaluate(js_content)
            page.evaluate('detectDynamicContentLoading(1000, 5)')
            print("Dynamic content finished loading")
        except Exception as e:
            print(f"Timeout or error waiting for dynamic content: {e}")

    def prepare_for_full_page_screenshot(self, page, window_width):
        # Scroll to the bottom of the page
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(1000)  # Wait for any dynamic content to load

        # Get the full height of the page
        full_height = page.evaluate('Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)')
        full_height = min(full_height, self.MAX_VIEWPORT_HEIGHT)

        # Set the viewport to the full height
        page.set_viewport_size({'width': window_width, 'height': full_height})

        # Wait for network idle
        page.wait_for_load_state('networkidle')

        # Scroll back to the top
        page.evaluate('window.scrollTo(0, 0)')
        page.wait_for_timeout(500)  # Short pause after scrolling

    def prepare_for_viewport_screenshot(self, page, window_width, window_height):
        # Set the viewport to the specified size
        page.set_viewport_size({'width': window_width, 'height': window_height})

        # Wait for network idle
        page.wait_for_load_state('networkidle')

    def inject_and_execute_scripts(self, page):
        with open(self.js_file_path, 'r') as file:
            js_content = file.read()
            page.evaluate(js_content)
        page.evaluate('pageUtils.disableSmoothScrolling()')
        page.evaluate('pageUtils.waitForAllImages()')