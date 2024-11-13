import os
import logging
from typing import List, Dict
from playwright.async_api import Browser, BrowserContext
from ua_generator import generate as generate_ua

logger = logging.getLogger(__name__)


class ContextManager:
    def __init__(self):
        self.context = None
        self.browser = None
        self.extension_dir = os.path.join(os.path.dirname(__file__), 'extensions')

        # Read extension configuration from environment
        self.use_popup_blocker = os.getenv('USE_POPUP_BLOCKER', 'true').lower() == 'true'
        self.use_cookie_blocker = os.getenv('USE_COOKIE_BLOCKER', 'true').lower() == 'true'

    def _get_extension_args(self) -> List[str]:
        """Get browser arguments for enabled extensions."""
        extensions = []
        if os.path.exists(self.extension_dir):
            extension_configs = [
                ('popup-off', self.use_popup_blocker),
                ('dont-care-cookies', self.use_cookie_blocker)
            ]

            for ext_name, is_enabled in extension_configs:
                if is_enabled:
                    ext_path = os.path.join(self.extension_dir, ext_name)
                    if os.path.exists(ext_path):
                        extensions.append(ext_path)

        if not extensions:
            return []

        return [
            f'--disable-extensions-except={",".join(extensions)}',
            *[f'--load-extension={ext}' for ext in extensions]
        ]

    def _generate_headers(self, options) -> Dict[str, str]:
        """Generate headers including user agent based on options."""
        ua_options = {}

        if hasattr(options, 'user_agent_device'):
            ua_options['device'] = options.user_agent_device
        if hasattr(options, 'user_agent_platform'):
            ua_options['platform'] = options.user_agent_platform
        if hasattr(options, 'user_agent_browser'):
            ua_options['browser'] = options.user_agent_browser

        # Generate a user agent with specified or default options
        ua = generate_ua(**ua_options)

        # Get all relevant headers from ua-generator
        headers = ua.headers.copy()
        headers.update({
            'Sec-CH-UA': ua.ch.brands,
            'Sec-CH-UA-Mobile': ua.ch.mobile,
            'Sec-CH-UA-Platform': f'"{ua.ch.platform}"'
        })

        # Add any custom headers from options
        if hasattr(options, 'custom_headers') and options.custom_headers:
            headers.update(options.custom_headers)

        return headers

    async def initialize(self, playwright) -> BrowserContext:
        """Initialize and return a configured browser context."""
        try:
            # Base browser arguments
            browser_args = [
                '--disable-features=site-per-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
            ]

            # Add extension arguments if any are enabled
            extension_args = self._get_extension_args()
            if extension_args:
                browser_args.extend(extension_args)
                logger.info(f"Launching browser with extensions: {extension_args}")

            # Launch browser with combined arguments
            self.browser = await playwright.chromium.launch(args=browser_args)

            # Create context with minimal settings (will be configured per capture)
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                device_scale_factor=1.0
            )

            logger.info("Browser context initialized successfully with configured extensions")
            return self.context

        except Exception as e:
            logger.error(f"Failed to initialize browser context: {str(e)}")
            raise

    async def close(self):
        """Clean up resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()