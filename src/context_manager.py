import os
import logging
from typing import List, Dict, Optional
from playwright.async_api import Browser, BrowserContext
from ua_generator import generate as generate_ua
from config import config
from exceptions import BrowserException

logger = logging.getLogger(__name__)


class ContextManager:
    def __init__(self):
        self.context = None
        self.browser = None
        self.extension_dir = os.path.join(os.path.dirname(__file__), 'extensions')

        # Read extension configuration from environment
        self.use_popup_blocker = os.getenv('USE_POPUP_BLOCKER', 'true').lower() == 'true'
        self.use_cookie_blocker = os.getenv('USE_COOKIE_BLOCKER', 'true').lower() == 'true'

        # Initialize proxy configuration from environment
        self.default_proxy_config = self._get_proxy_config()

    def _get_proxy_config(self) -> Optional[Dict[str, str]]:
        """Get proxy configuration from environment variables."""
        if config.PROXY_SERVER and config.PROXY_PORT:
            proxy_config = {
                'server': f'{config.PROXY_SERVER}:{config.PROXY_PORT}'
            }

            # Add authentication if provided
            if config.PROXY_USERNAME and config.PROXY_PASSWORD:
                proxy_config.update({
                    'username': config.PROXY_USERNAME,
                    'password': config.PROXY_PASSWORD
                })

            logger.info(f"Using proxy configuration: {config.PROXY_SERVER}:{config.PROXY_PORT}")
            return proxy_config
        return None

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

            # Create initial context with default proxy if configured
            context_options = {
                'viewport': {'width': 1920, 'height': 1080},
                'device_scale_factor': 1.0
            }

            if self.default_proxy_config:
                context_options['proxy'] = self.default_proxy_config

            self.context = await self.browser.new_context(**context_options)

            # Log successful initialization
            proxy_info = "with proxy" if self.default_proxy_config else "without proxy"
            logger.info(f"Browser context initialized successfully {proxy_info}")

            return self.context

        except Exception as e:
            logger.error(f"Failed to initialize browser context: {str(e)}")
            raise BrowserException(f"Browser context initialization failed: {str(e)}")

    async def close(self):
        """Clean up resources."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.error(f"Error during context cleanup: {str(e)}")
            # Don't re-raise as this is cleanup code