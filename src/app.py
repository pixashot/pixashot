import os
from dotenv import load_dotenv
from logging.config import dictConfig

from quart import Quart
from quart_rate_limiter import RateLimiter

from playwright.async_api import async_playwright

from cache_manager import CacheManager
from config import config, get_logging_config
from capture_service import CaptureService

# Configure logging
dictConfig(get_logging_config())

app = Quart(__name__)
capture_service = CaptureService()

# Initialize rate limiter
limiter = RateLimiter(app)

# Configure caching
app.config['CACHING_ENABLED'] = config.CACHE_MAX_SIZE > 0
app.cache_manager = CacheManager(max_size=config.CACHE_MAX_SIZE if app.config['CACHING_ENABLED'] else None)

# Log caching status
if app.config['CACHING_ENABLED']:
    app.logger.info(f"Caching enabled with max size: {config.CACHE_MAX_SIZE}")
else:
    app.logger.info("Caching disabled")


@app.before_serving
async def startup():
    global capture_service
    playwright = await async_playwright().start()
    capture_service = CaptureService()
    await capture_service.initialize(playwright)


@app.after_serving
async def shutdown():
    await capture_service.close()


# Import routes
from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.PORT, debug=True)
