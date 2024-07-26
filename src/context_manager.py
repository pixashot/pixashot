import os
import time
from playwright.async_api import async_playwright, Browser, BrowserContext
from typing import Dict, Tuple, List, Optional

class ContextManager:
    def __init__(self, playwright=None, max_contexts=5, context_timeout=300):
        self.playwright = playwright
        self.max_contexts = max_contexts
        self.context_timeout = context_timeout
        self.contexts: Dict[Tuple, Tuple[BrowserContext, float]] = {}
        self.extension_dir = os.path.join(os.path.dirname(__file__), 'extensions')

    def initialize(self, playwright):
        self.playwright = playwright

    async def get_context(self, options) -> BrowserContext:
        if self.playwright is None:
            self.playwright = await async_playwright().start()

        key = self._get_context_key(options)
        current_time = time.time()

        # Check if we have a valid context for this key
        if key in self.contexts:
            context, last_used = self.contexts[key]
            if current_time - last_used < self.context_timeout:
                self.contexts[key] = (context, current_time)
                return context

        # If we don't have a valid context, create a new one
        context = await self._create_context(options)
        self.contexts[key] = (context, current_time)

        # If we've exceeded the max number of contexts, remove the oldest one
        if len(self.contexts) > self.max_contexts:
            oldest_key = min(self.contexts, key=lambda k: self.contexts[k][1])
            await self.contexts[oldest_key][0].close()
            del self.contexts[oldest_key]

        return context

    def _get_context_key(self, options) -> Tuple:
        return (
            options.use_popup_blocker,
            options.use_cookie_blocker,
        )

    async def _create_context(self, options) -> BrowserContext:
        extensions = self._get_extensions(options)
        browser_args = self._get_browser_args(extensions)

        browser = await self.playwright.chromium.launch(
            headless=True,
            args=browser_args
        )

        return await browser.new_context(ignore_https_errors=True)

    def _get_extensions(self, options) -> List[str]:
        extensions = []
        if options.use_popup_blocker:
            extensions.append(os.path.join(self.extension_dir, 'popup-off'))
        if options.use_cookie_blocker:
            extensions.append(os.path.join(self.extension_dir, 'dont-care-cookies'))
        return extensions

    def _get_browser_args(self, extensions: List[str]) -> List[str]:
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

    async def close(self):
        for context, _ in self.contexts.values():
            await context.close()
        if self.playwright:
            await self.playwright.stop()