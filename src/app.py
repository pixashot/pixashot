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

class AppContainer:
    def __init__(self):
        self.playwright = None
        self.capture_service = None
        self.cache_manager = None
        self.rate_limiter = None
        self.context_manager = None

    async def initialize(self):
        try:
            # Start playwright
            self.playwright = await async_playwright().start()

            # Initialize context manager
            context_manager_config = {
                'max_contexts': int(os.getenv('BROWSER_MAX_CONTEXTS', '15')),
                'context_timeout': int(os.getenv('BROWSER_CONTEXT_TIMEOUT', '300')),
                'memory_limit_mb': int(os.getenv('BROWSER_MEMORY_LIMIT_MB', '1500')),
                'playwright': self.playwright
            }
            self.context_manager = ContextManager(**context_manager_config)
            await self.context_manager.initialize(self.playwright)

            # Initialize capture service
            self.capture_service = CaptureService()
            self.capture_service.context_manager = self.context_manager
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
        if self.context_manager:
            await self.context_manager.close()
        if self.playwright:
            await self.playwright.stop()


def create_app():
    # Configure logging
    dictConfig(get_logging_config())

    app = Quart(__name__)

    # Get configuration from environment with defaults
    context_manager_config = {
        'max_contexts': int(os.getenv('BROWSER_MAX_CONTEXTS', '15')),
        'context_timeout': int(os.getenv('BROWSER_CONTEXT_TIMEOUT', '300')),
        'memory_limit_mb': int(os.getenv('BROWSER_MEMORY_LIMIT_MB', '1500'))
    }

    # Store container in app config instead of directly on app
    container = AppContainer()

    # Initialize context manager with configuration
    container.context_manager = ContextManager(**context_manager_config)
    app.config['container'] = container

    # Initialize rate limiter
    container.rate_limiter = RateLimiter(app)

    # Configure caching
    app.config['CACHING_ENABLED'] = config.CACHE_MAX_SIZE > 0

    # Log caching status
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