import os
from dotenv import load_dotenv
from logging.config import dictConfig
from datetime import datetime
import time
import psutil
import logging

from quart import Quart
from quart_rate_limiter import RateLimiter
from playwright.async_api import async_playwright

from cache_manager import CacheManager
from config import config, get_logging_config
from capture_service import CaptureService
from routes import register_routes
from context_manager import ContextManager

logger = logging.getLogger(__name__)

# src/app.py (relevant section)

class AppContainer:
    def __init__(self):
        self.playwright = None
        self.capture_service = None
        self.cache_manager = None
        self.rate_limiter = None

    async def initialize(self):
        try:
            # Start playwright
            self.playwright = await async_playwright().start()

            # Initialize capture service
            self.capture_service = CaptureService()
            await self.capture_service.initialize(self.playwright)

            # Initialize cache manager
            self.cache_manager = CacheManager(
                max_size=config.CACHE_MAX_SIZE if config.CACHE_MAX_SIZE > 0 else None
            )
        except Exception as e:
            logger.error(f"Failed to initialize AppContainer: {str(e)}")
            raise

    async def close(self):
        if self.capture_service:
            await self.capture_service.close()
        if self.playwright:
            await self.playwright.stop()


def create_app():
    dictConfig(get_logging_config())
    app = Quart(__name__)

    # Create container with just the essentials
    container = AppContainer()
    app.config['container'] = container

    # Initialize rate limiter
    container.rate_limiter = RateLimiter(app)

    # Configure caching
    app.config['CACHING_ENABLED'] = config.CACHE_MAX_SIZE > 0
    if app.config['CACHING_ENABLED']:
        app.logger.info(f"Caching enabled with max size: {config.CACHE_MAX_SIZE}")
    else:
        app.logger.info("Caching disabled")

    # Register startup and shutdown handlers
    @app.before_serving
    async def startup():
        app.config['start_time'] = time.time()
        await container.initialize()

    @app.after_serving
    async def shutdown():
        await container.close()

    # Register routes
    register_routes(app)

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.PORT, debug=True)