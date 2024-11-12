import os
import time
import logging
import asyncio
from collections import OrderedDict
from typing import Dict, Tuple, List, Optional, Set
from playwright.async_api import async_playwright, Browser, BrowserContext, Error as PlaywrightError
import psutil

logger = logging.getLogger(__name__)


class ContextManager:
    def __init__(
            self,
            max_contexts: int = 15,
            context_timeout: int = 300,
            memory_limit_mb: int = 1500,
            playwright=None,
            extension_dir: Optional[str] = None,
            cleanup_interval: int = 60,
            max_context_uses: int = 100
    ):
        self.max_contexts = max_contexts
        self.context_timeout = context_timeout
        self.memory_limit = memory_limit_mb
        self.playwright = playwright
        self.max_context_uses = max_context_uses
        self.cleanup_interval = cleanup_interval

        # Using OrderedDict for FIFO behavior
        self.contexts: OrderedDict[Tuple, Tuple[BrowserContext, float, int, Browser]] = OrderedDict()

        # Track active contexts and their states
        self.active_contexts: Set[BrowserContext] = set()
        self.context_use_counts: Dict[BrowserContext, int] = {}
        self.context_last_check: Dict[BrowserContext, float] = {}

        # Keep track of the last cleanup time
        self.last_cleanup_time = time.time()

        # Extension directory handling
        self.extension_dir = extension_dir or os.path.join(os.path.dirname(__file__), 'extensions')

        self.browser: Optional[Browser] = None
        self._cleanup_lock = asyncio.Lock()
        self._browser_lock = asyncio.Lock()

        # Validate extension directory
        if not os.path.exists(self.extension_dir):
            logger.warning(f"Extension directory not found at {self.extension_dir}")
            os.makedirs(self.extension_dir, exist_ok=True)

    async def initialize(self, playwright):
        """Initialize the playwright instance and browser with optimized settings."""
        try:
            async with self._browser_lock:
                self.playwright = playwright
                if not self.browser or not self.browser.is_connected():
                    self.browser = await self.playwright.chromium.launch(
                        headless=True,
                        args=[
                            '--no-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--disable-setuid-sandbox',
                            '--disable-software-rasterizer',
                            '--disable-dev-tools',
                            '--no-first-run',
                            '--no-zygote',
                            '--single-process',
                            '--disable-accelerated-2d-canvas',
                            '--disable-accelerated-video-decode',
                            '--disable-gpu-compositing',
                            '--disable-gpu-rasterization'
                        ]
                    )
                    logger.info("Browser instance launched successfully with optimized settings")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise

    async def is_context_valid(self, context: BrowserContext) -> bool:
        """Check if a context is still valid and usable."""
        try:
            if context not in self.active_contexts:
                return False

            # Check if the context is too old
            last_used = self.context_last_check.get(context, 0)
            if time.time() - last_used > self.context_timeout:
                return False

            # Verify context is still operational
            test_page = await context.new_page()
            await test_page.close()
            return True
        except PlaywrightError:
            return False
        except Exception as e:
            logger.warning(f"Error checking context validity: {str(e)}")
            return False

    async def get_context(self, options) -> BrowserContext:
        """Get an existing context or create a new one based on configuration."""
        try:
            await self._check_cleanup()

            if self.playwright is None:
                self.playwright = await async_playwright().start()

            key = self._get_context_key(options)
            current_time = time.time()

            # Check if we have a valid context for this key
            if key in self.contexts:
                context, last_used, use_count, browser = self.contexts[key]

                # Validate the context before using it
                if await self.is_context_valid(context):
                    # Update context metadata
                    use_count += 1
                    self.contexts[key] = (context, current_time, use_count, browser)
                    self.context_use_counts[context] = use_count
                    self.context_last_check[context] = current_time
                    self.contexts.move_to_end(key)

                    logger.debug(f"Reusing existing context (use count: {use_count})")
                    return context
                else:
                    # Context is invalid, remove it
                    logger.info("Found invalid context, removing it")
                    await self._remove_context(key)

            # Create new context if needed
            return await self._create_new_context(options, key)

        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            raise

    async def _create_new_context(self, options, key) -> BrowserContext:
        """Create a new browser context with optimized settings."""
        try:
            # Check browser connection
            async with self._browser_lock:
                if not self.browser or not self.browser.is_connected():
                    await self.initialize(self.playwright)

            # Check memory before creating new context
            if not self._check_memory_usage():
                await self._force_cleanup()

            # Remove oldest context if at capacity
            while len(self.contexts) >= self.max_contexts:
                await self._remove_oldest_context()

            # Create and configure new context
            context = await self._setup_new_context(options)

            # Store the new context
            self.contexts[key] = (context, time.time(), 1, self.browser)
            self.active_contexts.add(context)
            self.context_use_counts[context] = 1
            self.context_last_check[context] = time.time()

            logger.info(f"Created new context. Active contexts: {len(self.contexts)}")
            return context

        except Exception as e:
            logger.error(f"Error creating new context: {str(e)}")
            raise

    async def _setup_new_context(self, options) -> BrowserContext:
        """Set up a new browser context with all necessary configurations."""
        context_options = {
            'ignore_https_errors': options.ignore_https_errors,
            'viewport': {'width': options.window_width, 'height': options.window_height},
            'device_scale_factor': options.pixel_density,
            'bypass_csp': True,
        }

        if hasattr(options, 'proxy_server') and options.proxy_server:
            context_options['proxy'] = {
                'server': f"{options.proxy_server}:{options.proxy_port}"
            }
            if hasattr(options, 'proxy_username') and options.proxy_username:
                context_options['proxy']['username'] = options.proxy_username
                context_options['proxy']['password'] = options.proxy_password

        context = await self.browser.new_context(**context_options)

        # Set default timeouts
        context.set_default_timeout(90000)  # 90 seconds default timeout
        context.set_default_navigation_timeout(15000)  # 15 seconds navigation timeout

        # Apply extensions if needed
        try:
            if options.use_popup_blocker:
                await self._apply_extension(context, 'popup-off')
            if options.use_cookie_blocker:
                await self._apply_extension(context, 'dont-care-cookies')
        except Exception as e:
            logger.warning(f"Failed to apply extensions: {str(e)}")

        return context

    async def _apply_extension(self, context: BrowserContext, extension_name: str):
        """Apply a browser extension to the context with improved error handling."""
        try:
            extension_path = os.path.join(self.extension_dir, extension_name)
            if not os.path.exists(extension_path):
                logger.warning(f"Extension directory not found: {extension_path}")
                return

            # Load and validate extension code
            try:
                extension_files = os.listdir(extension_path)
                for file in extension_files:
                    if file.endswith('.js'):
                        js_path = os.path.join(extension_path, file)
                        with open(js_path, 'r', encoding='utf-8') as f:
                            extension_code = f.read()
                            if extension_code.strip():
                                await context.add_init_script(extension_code)
                                logger.debug(f"Applied extension {extension_name} from {js_path}")
            except Exception as e:
                logger.error(f"Error loading extension {extension_name}: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"Error applying extension {extension_name}: {str(e)}")
            raise

    def _get_extension_args(self, options) -> List[str]:
        """Get browser arguments for extensions."""
        extension_args = []
        if os.path.exists(self.extension_dir):
            extensions = []
            if options.use_popup_blocker:
                popup_blocker_path = os.path.join(self.extension_dir, 'popup-off')
                if os.path.exists(popup_blocker_path):
                    extensions.append(popup_blocker_path)

            if options.use_cookie_blocker:
                cookie_blocker_path = os.path.join(self.extension_dir, 'dont-care-cookies')
                if os.path.exists(cookie_blocker_path):
                    extensions.append(cookie_blocker_path)

            if extensions:
                extension_args.extend([
                    f'--disable-extensions-except={",".join(extensions)}',
                    *[f'--load-extension={ext}' for ext in extensions]
                ])

        return extension_args

    async def _remove_context(self, key: Tuple):
        """Safely remove and close a context."""
        try:
            if key in self.contexts:
                context, _, _, _ = self.contexts[key]
                if context in self.active_contexts:
                    try:
                        await context.close()
                    except PlaywrightError:
                        pass  # Context might already be closed
                    self.active_contexts.remove(context)

                self.context_use_counts.pop(context, None)
                self.context_last_check.pop(context, None)
                del self.contexts[key]

                logger.info(f"Removed context {key}")
        except Exception as e:
            logger.error(f"Error removing context {key}: {str(e)}")
            # Still remove from tracking even if close fails
            self.contexts.pop(key, None)

    async def close(self):
        """Close all contexts and the browser."""
        try:
            async with self._cleanup_lock:
                for key in list(self.contexts.keys()):
                    await self._remove_context(key)

                if self.browser:
                    try:
                        await self.browser.close()
                    except PlaywrightError:
                        pass  # Browser might already be closed

                if self.playwright:
                    await self.playwright.stop()

            logger.info("ContextManager closed successfully")
        except Exception as e:
            logger.error(f"Error closing ContextManager: {str(e)}")
            raise

    def _get_context_key(self, options) -> Tuple:
        """Generate a unique key based on context configuration."""
        return (
            bool(options.use_popup_blocker),
            bool(options.use_cookie_blocker),
            bool(options.ignore_https_errors),
            bool(options.block_media),
            options.window_width,
            options.window_height,
            options.pixel_density
        )

    async def _check_cleanup(self):
        """Check if cleanup is needed based on time interval."""
        current_time = time.time()
        if current_time - self.last_cleanup_time >= self.cleanup_interval:
            async with self._cleanup_lock:
                await self._cleanup_contexts()
                self.last_cleanup_time = current_time

    def _check_memory_usage(self) -> bool:
        """Check if memory usage is within limits."""
        try:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            logger.debug(f"Current memory usage: {memory_mb:.2f}MB")
            return memory_mb < self.memory_limit
        except Exception as e:
            logger.error(f"Error checking memory usage: {str(e)}")
            return True

    async def _cleanup_contexts(self):
        """Clean up expired or overused contexts."""
        current_time = time.time()
        keys_to_remove = []

        for key, (context, last_used, use_count, _) in self.contexts.items():
            if (
                    current_time - last_used >= self.context_timeout or
                    use_count >= self.max_context_uses or
                    not await self.is_context_valid(context)
            ):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            await self._remove_context(key)
            logger.info(f"Cleaned up context with key {key}")

    async def _force_cleanup(self):
        """Force immediate cleanup of contexts."""
        async with self._cleanup_lock:
            await self._cleanup_contexts()
            self.last_cleanup_time = time.time()

    async def _remove_oldest_context(self):
        """Remove the oldest context from the pool."""
        if self.contexts:
            oldest_key = next(iter(self.contexts))
            await self._remove_context(oldest_key)
            logger.info(f"Removed oldest context with key {oldest_key}")

    def get_stats(self) -> Dict:
        """Get current context pool statistics."""
        try:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent(interval=0.1)

            return {
                'active_contexts': len(self.active_contexts),
                'total_contexts': len(self.contexts),
                'max_contexts': self.max_contexts,
                'context_timeout': self.context_timeout,
                'memory_usage_mb': round(memory_mb, 2),
                'memory_limit_mb': self.memory_limit,
                'cpu_percent': round(cpu_percent, 2),
                'context_keys': [str(key) for key in self.contexts.keys()],
                'avg_context_uses': round(sum(self.context_use_counts.values()) / len(
                    self.context_use_counts)) if self.context_use_counts else 0
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}