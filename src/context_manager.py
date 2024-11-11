import os
import time
import logging
from collections import OrderedDict
from typing import Dict, Tuple, List, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext

logger = logging.getLogger(__name__)


class ContextManager:
    def __init__(
            self,
            max_contexts: int = 15,
            context_timeout: int = 300,
            memory_limit_mb: int = 1500,
            playwright=None,
            extension_dir: Optional[str] = None
    ):
        self.max_contexts = max_contexts
        self.context_timeout = context_timeout
        self.memory_limit = memory_limit_mb
        self.playwright = playwright

        # Using OrderedDict for FIFO behavior
        self.contexts: OrderedDict[Tuple, Tuple[BrowserContext, float, Browser]] = OrderedDict()

        # Extension directory handling
        if extension_dir:
            self.extension_dir = extension_dir
        else:
            # Default to a subdirectory of the current file's location
            self.extension_dir = os.path.join(os.path.dirname(__file__), 'extensions')

        self.browser: Optional[Browser] = None

        # Validate extension directory
        if not os.path.exists(self.extension_dir):
            logger.warning(f"Extension directory not found at {self.extension_dir}")
            os.makedirs(self.extension_dir, exist_ok=True)

        logger.info(f"Initialized ContextManager with max_contexts={self.max_contexts}, "
                    f"context_timeout={self.context_timeout}s, "
                    f"memory_limit={self.memory_limit}MB, "
                    f"extension_dir={self.extension_dir}")

    async def initialize(self, playwright):
        """Initialize the playwright instance and launch the browser."""
        try:
            self.playwright = playwright
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox']
            )
            logger.info("Browser instance launched successfully")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise

    def _get_context_key(self, options) -> Tuple:
        """Generate a unique key based on context configuration."""
        return (
            bool(options.use_popup_blocker),
            bool(options.use_cookie_blocker),
            bool(options.ignore_https_errors),
            bool(options.block_media)
        )

    async def get_context(self, options) -> BrowserContext:
        """Get an existing context or create a new one based on configuration."""
        try:
            if self.playwright is None:
                self.playwright = await async_playwright().start()

            # Check memory usage before proceeding
            if not self._check_memory_usage():
                logger.warning("Memory usage too high, clearing all contexts")
                await self._clear_all_contexts()

            key = self._get_context_key(options)
            current_time = time.time()

            # Clean expired contexts
            await self._clean_expired_contexts()

            # Check if we have a valid context for this key
            if key in self.contexts:
                context, last_used, _ = self.contexts[key]
                if current_time - last_used < self.context_timeout:
                    # Move this context to the end of the OrderedDict (most recently used)
                    self.contexts.move_to_end(key)
                    # Update last used time
                    self.contexts[key] = (context, current_time, self.browser)
                    logger.debug(f"Reusing existing context with key {key}")
                    return context

            # If we don't have a valid context, create a new one
            context = await self._create_context(options)

            # If we've exceeded the max number of contexts, remove the oldest one(s)
            while len(self.contexts) >= self.max_contexts:
                oldest_key = next(iter(self.contexts))
                await self._close_context(oldest_key)
                logger.info(f"Removed oldest context with key {oldest_key}")

            # Add the new context
            self.contexts[key] = (context, current_time, self.browser)
            self.contexts.move_to_end(key)
            logger.info(f"Created new context with key {key}. Active contexts: {len(self.contexts)}")

            return context
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            raise

    async def _create_context(self, options) -> BrowserContext:
        """Create a new browser context with the specified options."""
        try:
            # Create context with specific configuration
            context = await self.browser.new_context(
                ignore_https_errors=options.ignore_https_errors,
                viewport={'width': options.window_width, 'height': options.window_height},
                device_scale_factor=options.pixel_density,
            )

            # Apply additional configurations
            if options.block_media:
                await context.route("**/*.{png,jpg,jpeg,gif,svg,ico,mp4,webm,ogg,mp3,wav}",
                                 lambda route: route.abort())

            # Only attempt to use extensions if the directory exists and contains the extensions
            if os.path.exists(self.extension_dir):
                if options.use_popup_blocker:
                    await self._apply_extension(context, 'popup-off')
                if options.use_cookie_blocker:
                    await self._apply_extension(context, 'dont-care-cookies')

            return context
        except Exception as e:
            logger.error(f"Error creating context: {str(e)}")
            raise

    async def _apply_extension(self, context: BrowserContext, extension_name: str):
        """Safely apply an extension to a context if it exists."""
        extension_path = os.path.join(self.extension_dir, extension_name)
        content_js_path = os.path.join(extension_path, 'content.js')

        if os.path.exists(content_js_path):
            try:
                with open(content_js_path, 'r') as f:
                    script_content = f.read()
                await context.add_init_script(script=script_content)
                logger.debug(f"Applied extension {extension_name}")
            except Exception as e:
                logger.warning(f"Failed to apply extension {extension_name}: {str(e)}")
        else:
            logger.warning(f"Extension {extension_name} not found at {extension_path}")

    def _get_extensions(self, options) -> List[str]:
        """Get list of available extension paths based on options."""
        extensions = []
        if not os.path.exists(self.extension_dir):
            return extensions

        if options.use_popup_blocker:
            popup_path = os.path.join(self.extension_dir, 'popup-off')
            if os.path.exists(popup_path):
                extensions.append(popup_path)
            else:
                logger.warning(f"Popup blocker extension not found at {popup_path}")

        if options.use_cookie_blocker:
            cookie_path = os.path.join(self.extension_dir, 'dont-care-cookies')
            if os.path.exists(cookie_path):
                extensions.append(cookie_path)
            else:
                logger.warning(f"Cookie blocker extension not found at {cookie_path}")

        return extensions

    def _get_browser_args(self, extensions: List[str]) -> List[str]:
        """Get browser arguments including extension configuration."""
        args = [
            '--autoplay-policy=no-user-gesture-required',
            '--disable-gpu',
            '--disable-accelerated-2d-canvas',
            '--disable-accelerated-video-decode',
            '--disable-gpu-compositing',
            '--disable-gpu-rasterization',
            '--no-sandbox'
        ]

        if extensions:
            disable_extensions_arg = f"--disable-extensions-except={','.join(extensions)}"
            load_extension_args = [f"--load-extension={ext}" for ext in extensions]
            args.extend([disable_extensions_arg, *load_extension_args])

        return args

    def _check_memory_usage(self) -> bool:
        """Check if memory usage is within limits."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            logger.debug(f"Current memory usage: {memory_mb:.2f}MB")
            return memory_mb < self.memory_limit
        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")
            return True  # Continue if we can't check memory

    async def _clean_expired_contexts(self):
        """Remove expired contexts."""
        try:
            current_time = time.time()
            expired_keys = [
                key for key, (_, last_used, _) in self.contexts.items()
                if current_time - last_used >= self.context_timeout
            ]
            for key in expired_keys:
                await self._close_context(key)
                logger.info(f"Removed expired context with key {key}")
        except Exception as e:
            logger.error(f"Error cleaning expired contexts: {str(e)}")

    async def _clear_all_contexts(self):
        """Clear all contexts when memory usage is too high."""
        try:
            for key in list(self.contexts.keys()):
                await self._close_context(key)
            logger.info("All contexts cleared")
        except Exception as e:
            logger.error(f"Error clearing all contexts: {str(e)}")

    async def _close_context(self, key: Tuple):
        """Close and remove a specific context."""
        try:
            if key in self.contexts:
                context, _, _ = self.contexts[key]
                await context.close()
                del self.contexts[key]
        except Exception as e:
            logger.error(f"Error closing context {key}: {str(e)}")
            # Still try to remove from contexts even if close fails
            self.contexts.pop(key, None)

    async def close(self):
        """Close all contexts and the browser."""
        try:
            for key in list(self.contexts.keys()):
                await self._close_context(key)
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("ContextManager closed successfully")
        except Exception as e:
            logger.error(f"Error closing ContextManager: {str(e)}")
            raise

    def get_stats(self) -> Dict:
        """Get current context pool statistics."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
        except Exception as e:
            logger.error(f"Error getting memory stats: {str(e)}")
            memory_mb = 0

        return {
            'active_contexts': len(self.contexts),
            'max_contexts': self.max_contexts,
            'context_timeout': self.context_timeout,
            'memory_usage_mb': round(memory_mb, 2),
            'memory_limit_mb': self.memory_limit,
            'context_keys': [str(key) for key in self.contexts.keys()]
        }