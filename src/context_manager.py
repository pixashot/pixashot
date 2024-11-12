import os
import time
import logging
import asyncio
from collections import OrderedDict
from typing import Dict, Tuple, List, Optional, Set
from playwright.async_api import async_playwright, Browser, BrowserContext
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

        # Keep track of the last cleanup time
        self.last_cleanup_time = time.time()

        # Extension directory handling
        if extension_dir:
            self.extension_dir = extension_dir
        else:
            self.extension_dir = os.path.join(os.path.dirname(__file__), 'extensions')

        self.browser: Optional[Browser] = None
        self._cleanup_lock = asyncio.Lock()

        # Validate extension directory
        if not os.path.exists(self.extension_dir):
            logger.warning(f"Extension directory not found at {self.extension_dir}")
            os.makedirs(self.extension_dir, exist_ok=True)

        logger.info(f"Initialized ContextManager with max_contexts={self.max_contexts}, "
                    f"context_timeout={self.context_timeout}s, "
                    f"memory_limit={self.memory_limit}MB, "
                    f"extension_dir={self.extension_dir}, "
                    f"max_context_uses={self.max_context_uses}")

    async def initialize(self, playwright):
        """Initialize the playwright instance and launch the browser with optimized settings."""
        try:
            self.playwright = playwright
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

    async def get_context(self, options) -> BrowserContext:
        """Get an existing context or create a new one based on configuration."""
        try:
            # Check if cleanup is needed
            await self._check_cleanup()

            if self.playwright is None:
                self.playwright = await async_playwright().start()

            key = self._get_context_key(options)
            current_time = time.time()

            # Check if we have a valid context for this key
            if key in self.contexts:
                context, last_used, use_count, browser = self.contexts[key]
                if (current_time - last_used < self.context_timeout and
                        use_count < self.max_context_uses and
                        context in self.active_contexts):
                    # Update context metadata
                    use_count += 1
                    self.contexts[key] = (context, current_time, use_count, browser)
                    self.contexts.move_to_end(key)

                    logger.debug(f"Reusing existing context with key {key} (use count: {use_count})")
                    return context

            # If we need a new context, first check memory usage
            if not self._check_memory_usage():
                logger.warning("Memory usage too high, performing cleanup")
                await self._force_cleanup()

            # Create new context
            context = await self._create_context(options)

            # If we've exceeded the max number of contexts, remove the oldest one(s)
            while len(self.contexts) >= self.max_contexts:
                await self._remove_oldest_context()

            # Add the new context
            self.contexts[key] = (context, current_time, 1, self.browser)
            self.active_contexts.add(context)
            self.context_use_counts[context] = 1
            self.contexts.move_to_end(key)

            logger.info(f"Created new context with key {key}. Active contexts: {len(self.contexts)}")
            return context

        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            raise

    async def _create_context(self, options) -> BrowserContext:
        """Create a new browser context with optimized settings."""
        try:
            context = await self.browser.new_context(
                ignore_https_errors=options.ignore_https_errors,
                viewport={'width': options.window_width, 'height': options.window_height},
                device_scale_factor=options.pixel_density,
                hardware_acceleration="disable",  # Disable hardware acceleration for better stability
                java_script_enabled=True,  # Explicitly enable JavaScript
                bypass_csp=True,  # Bypass Content Security Policy for better compatibility
                proxy=self._get_proxy_config(options)
            )

            # Set default timeout to reduce hanging
            context.set_default_timeout(10000)  # 10 seconds default timeout
            context.set_default_navigation_timeout(15000)  # 15 seconds navigation timeout

            # Apply resource blocking if needed
            if options.block_media:
                await context.route(
                    "**/*.{png,jpg,jpeg,gif,svg,ico,mp4,webm,ogg,mp3,wav,webp,pdf}",
                    lambda route: route.abort()
                )

            # Apply extensions if needed and available
            if os.path.exists(self.extension_dir):
                if options.use_popup_blocker:
                    await self._apply_extension(context, 'popup-off')
                if options.use_cookie_blocker:
                    await self._apply_extension(context, 'dont-care-cookies')

            return context
        except Exception as e:
            logger.error(f"Error creating context: {str(e)}")
            raise

    def _get_proxy_config(self, options) -> Optional[Dict]:
        """Get proxy configuration if specified in options."""
        if options.proxy_server and options.proxy_port:
            proxy_config = {
                'server': f"{options.proxy_server}:{options.proxy_port}"
            }
            if options.proxy_username and options.proxy_password:
                proxy_config.update({
                    'username': options.proxy_username,
                    'password': options.proxy_password
                })
            return proxy_config
        return None

    async def _check_cleanup(self):
        """Check if cleanup is needed based on time interval."""
        current_time = time.time()
        if current_time - self.last_cleanup_time >= self.cleanup_interval:
            async with self._cleanup_lock:
                await self._cleanup_contexts()
                self.last_cleanup_time = current_time

    async def _force_cleanup(self):
        """Force immediate cleanup of contexts."""
        async with self._cleanup_lock:
            await self._cleanup_contexts()
            self.last_cleanup_time = time.time()

    async def _cleanup_contexts(self):
        """Clean up expired or overused contexts."""
        current_time = time.time()
        keys_to_remove = []

        for key, (context, last_used, use_count, _) in self.contexts.items():
            if (current_time - last_used >= self.context_timeout or
                    use_count >= self.max_context_uses or
                    context not in self.active_contexts):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            await self._close_context(key)
            logger.info(f"Cleaned up context with key {key}")

    def _check_memory_usage(self) -> bool:
        """Check if memory usage is within limits."""
        try:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            logger.debug(f"Current memory usage: {memory_mb:.2f}MB")
            return memory_mb < self.memory_limit
        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")
            return True

    async def _remove_oldest_context(self):
        """Remove the oldest context from the pool."""
        if self.contexts:
            oldest_key = next(iter(self.contexts))
            await self._close_context(oldest_key)
            logger.info(f"Removed oldest context with key {oldest_key}")

    async def _close_context(self, key: Tuple):
        """Close and remove a specific context."""
        try:
            if key in self.contexts:
                context, _, _, _ = self.contexts[key]
                if context in self.active_contexts:
                    await context.close()
                    self.active_contexts.remove(context)
                self.context_use_counts.pop(context, None)
                del self.contexts[key]
        except Exception as e:
            logger.error(f"Error closing context {key}: {str(e)}")
            # Still try to remove from contexts even if close fails
            self.contexts.pop(key, None)

    async def close(self):
        """Close all contexts and the browser."""
        try:
            async with self._cleanup_lock:
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