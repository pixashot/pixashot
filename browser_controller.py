import os
import asyncio
from playwright.async_api import async_playwright


class BrowserController:
    MAX_VIEWPORT_HEIGHT = 16384
    NETWORK_IDLE_TIMEOUT_MS = 1000
    SCROLL_PAUSE_MS = 500

    def __init__(self):
        self.js_file_path = os.path.join(os.path.dirname(__file__), 'js/page-utils.js')
        self.dynamic_content_detector_path = os.path.join(os.path.dirname(__file__), 'js/dynamic-content-detector.js')

    async def goto_with_timeout(self, page, url):
        try:
            await asyncio.wait_for(page.goto(url, wait_until='domcontentloaded'), timeout=5.0)
        except asyncio.TimeoutError:
            print("Navigation exceeded 5 seconds. Proceeding without waiting for full load.")

    async def prepare_page(self, page, options):
        await asyncio.gather(
            self.inject_scripts(page),
            self.wait_for_network_idle(page, options.wait_for_timeout),
            self.execute_custom_js(page, options.custom_js) if options.custom_js else asyncio.sleep(0),
            self.wait_for_selector(page, options.wait_for_selector,
                                   options.wait_for_timeout) if options.wait_for_selector else asyncio.sleep(0)
        )

    async def inject_scripts(self, page):
        with open(self.js_file_path, 'r') as file:
            js_content = file.read()
            await page.evaluate(js_content)
        await page.evaluate('pageUtils.disableSmoothScrolling()')
        await page.evaluate('pageUtils.waitForAllImages()')

    async def wait_for_network_idle(self, page, timeout):
        try:
            await page.wait_for_load_state('networkidle', timeout=timeout)
        except Exception as e:
            print(f"Timeout waiting for network idle: {e}")

    async def execute_custom_js(self, page, custom_js):
        await page.evaluate(custom_js)

    async def wait_for_selector(self, page, selector, timeout):
        try:
            await page.wait_for_selector(selector, timeout=timeout)
        except Exception as e:
            print(f"Timeout waiting for selector '{selector}': {e}")

    async def prepare_for_full_page_screenshot(self, page, window_width):
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await page.wait_for_load_state('networkidle', timeout=self.NETWORK_IDLE_TIMEOUT_MS)

        full_height = await page.evaluate('Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)')
        full_height = min(full_height, self.MAX_VIEWPORT_HEIGHT)

        await page.set_viewport_size({'width': window_width, 'height': full_height})
        await page.wait_for_load_state('networkidle', timeout=self.NETWORK_IDLE_TIMEOUT_MS)
        await page.evaluate('window.scrollTo(0, 0)')
        await page.wait_for_timeout(self.SCROLL_PAUSE_MS)

    async def prepare_for_viewport_screenshot(self, page, window_width, window_height):
        await page.set_viewport_size({'width': window_width, 'height': window_height})
        await page.wait_for_load_state('networkidle', timeout=self.NETWORK_IDLE_TIMEOUT_MS)
