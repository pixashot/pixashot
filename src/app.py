# app.py

import os
from dotenv import load_dotenv
from logging.config import dictConfig

from quart import Quart
from quart_rate_limiter import RateLimiter
from playwright.async_api import async_playwright

from cache_manager import CacheManager
from config import config, get_logging_config
from capture_service import CaptureService


class AppContainer:
    def __init__(self):
        self.playwright = None
        self.capture_service = None
        self.cache_manager = None
        self.rate_limiter = None

    async def initialize(self):
        self.playwright = await async_playwright().start()
        self.capture_service = CaptureService()
        await self.capture_service.initialize(self.playwright)

        self.cache_manager = CacheManager(
            max_size=config.CACHE_MAX_SIZE if config.CACHE_MAX_SIZE > 0 else None
        )

    async def close(self):
        if self.capture_service:
            await self.capture_service.close()
        if self.playwright:
            await self.playwright.stop()


# Configure logging
dictConfig(get_logging_config())

app = Quart(__name__)
app.container = AppContainer()

# Initialize rate limiter
app.container.rate_limiter = RateLimiter(app)

# Configure caching
app.config['CACHING_ENABLED'] = config.CACHE_MAX_SIZE > 0

# Log caching status
if app.config['CACHING_ENABLED']:
    app.logger.info(f"Caching enabled with max size: {config.CACHE_MAX_SIZE}")
else:
    app.logger.info("Caching disabled")


@app.before_serving
async def startup():
    await app.container.initialize()


@app.after_serving
async def shutdown():
    await app.container.close()


# Import routes
from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.PORT, debug=True)
