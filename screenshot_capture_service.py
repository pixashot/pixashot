import os
import tempfile
from playwright.sync_api import sync_playwright


class ScreenshotCaptureService:
    def __init__(self):
        self.proxy_config = None

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

                # Disable smooth scrolling
                page.evaluate("""
                    () => {
                        const style = document.createElement('style');
                        style.innerHTML = `* { scroll-behavior: auto !important; }`;
                        document.head.appendChild(style);
                    }
                """)

                # Set all images to eager loading and wait for them to load
                page.evaluate("""
                    () => {
                        const images = document.querySelectorAll('img');
                        images.forEach(img => {
                            img.loading = 'eager';
                            if (img.complete) return;
                            img.src = img.src;
                        });

                        return Promise.all(Array.from(images)
                            .filter(img => !img.complete)
                            .map(img => new Promise((resolve) => {
                                img.onload = img.onerror = resolve;
                            }))
                        );
                    }
                """)

                print('All images set to eager loading and loaded')

                # Scroll through the page
                last_scroll_height = 0
                while True:
                    scroll_height = self.get_scroll_height(page)
                    if scroll_height == last_scroll_height:
                        break

                    for position in range(0, scroll_height, height):
                        self.scroll_to(page, position)
                        page.wait_for_timeout(500)

                    last_scroll_height = scroll_height
                    page.wait_for_timeout(1000)

                # Scroll back to top
                self.scroll_to(page, 0)
                page.wait_for_timeout(2000)

                print('Capturing screenshot...')
                page.screenshot(path=output_path, full_page=True)

                print('Screenshot captured!')
            except Exception as error:
                print('Error during screenshot capture:', error)
                raise
            finally:
                print('Closing browser.')
                page.close()