import os
import logging
from typing import Dict, List
from playwright.async_api import async_playwright, Browser, BrowserContext

logger = logging.getLogger(__name__)


class ContextManager:
    def __init__(self, playwright=None):
        self.playwright = playwright
        self.browser = None
        self.context = None
        self.extension_dir = os.path.join(os.path.dirname(__file__), 'extensions')

        # Read extension configuration from environment
        self.use_popup_blocker = os.getenv('USE_POPUP_BLOCKER', 'true').lower() == 'true'
        self.use_cookie_blocker = os.getenv('USE_COOKIE_BLOCKER', 'true').lower() == 'true'
        self.use_ad_blocker = os.getenv('USE_AD_BLOCKER', 'true').lower() == 'true'

    def _get_extension_args(self) -> List[str]:
        """Get browser arguments for enabled extensions."""
        extensions = []

        if os.path.exists(self.extension_dir):
            if self.use_popup_blocker:
                popup_path = os.path.join(self.extension_dir, 'popup-off')
                if os.path.exists(popup_path):
                    extensions.append(popup_path)

            if self.use_cookie_blocker:
                cookie_path = os.path.join(self.extension_dir, 'dont-care-cookies')
                if os.path.exists(cookie_path):
                    extensions.append(cookie_path)

            if self.use_ad_blocker:
                ad_block_path = os.path.join(self.extension_dir, 'ublock-origin')
                if os.path.exists(ad_block_path):
                    extensions.append(ad_block_path)

        if not extensions:
            return []

        return [
            f'--disable-extensions-except={",".join(extensions)}',
            *[f'--load-extension={ext}' for ext in extensions]
        ]

    async def initialize(self, playwright):
        """Initialize browser with configured extensions."""
        try:
            self.playwright = playwright

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
            self.browser = await self.playwright.chromium.launch(args=browser_args)

            # Create the shared context with standard settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            # Apply any extension-specific JavaScript
            if self.use_popup_blocker or self.use_cookie_blocker or self.use_ad_blocker:
                await self._setup_extension_scripts()

            logger.info("Browser and context initialized successfully with configured extensions")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise

    async def _setup_extension_scripts(self):
        """Setup any additional scripts needed for extensions."""
        if self.use_cookie_blocker:
            await self.context.add_init_script("""
                window.addEventListener('DOMContentLoaded', () => {
                    // Basic cookie consent handler
                    const commonSelectors = [
                        '[aria-label*="cookie banner"]',
                        '[class*="cookie-banner"]',
                        '[id*="cookie-banner"]',
                        '[class*="cookie-consent"]',
                        '[id*="cookie-consent"]'
                    ];

                    commonSelectors.forEach(selector => {
                        const element = document.querySelector(selector);
                        if (element) element.remove();
                    });
                });
            """)

        if self.use_popup_blocker:
            await self.context.add_init_script("""
                // Basic popup blocker
                window.open = function() { return null; };
                window.addEventListener('load', () => {
                    document.querySelectorAll('a[target="_blank"]')
                        .forEach(a => a.setAttribute('target', '_self'));
                });
            """)

    async def get_context(self, options) -> BrowserContext:
        """Return the shared context."""
        if not self.context:
            await self.initialize(self.playwright)
        return self.context

    async def close(self):
        """Clean up resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()