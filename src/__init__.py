import os
from dotenv import load_dotenv
from .logging_config import get_logging_config

# Load .env file if it exists
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


class Config:
    def __init__(self):
        # Required settings with defaults
        self.PORT = int(os.getenv('PORT', 8080))
        self.RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'False').lower() == 'true'
        self.RATE_LIMIT_CAPTURE = os.getenv('RATE_LIMIT_CAPTURE', '1 per second')
        self.RATE_LIMIT_SIGNED = os.getenv('RATE_LIMIT_SIGNED', '5 per second')
        self.CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', 0))

        # Optional settings - explicitly set to None if not provided
        self.AUTH_TOKEN = os.getenv('AUTH_TOKEN', None)
        self.URL_SIGNING_SECRET = os.getenv('URL_SIGNING_SECRET', None)
        self.PROXY_SERVER = os.getenv('PROXY_SERVER', None)
        self.PROXY_PORT = os.getenv('PROXY_PORT', None)
        self.PROXY_USERNAME = os.getenv('PROXY_USERNAME', None)
        self.PROXY_PASSWORD = os.getenv('PROXY_PASSWORD', None)


config = Config()

__all__ = ['config', 'get_logging_config']