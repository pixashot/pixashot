import os
from dotenv import load_dotenv

# Load .env file if it exists
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


class Config:
    PORT = int(os.getenv('PORT', 8080))
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'False').lower() == 'true'
    RATE_LIMIT_CAPTURE = os.getenv('RATE_LIMIT_CAPTURE', '1 per second')
    RATE_LIMIT_SIGNED = os.getenv('RATE_LIMIT_SIGNED', '5 per second')
    PROXY_SERVER = os.getenv('PROXY_SERVER')
    PROXY_PORT = os.getenv('PROXY_PORT')
    PROXY_USERNAME = os.getenv('PROXY_USERNAME')
    PROXY_PASSWORD = os.getenv('PROXY_PASSWORD')
    URL_SIGNING_SECRET = os.getenv('URL_SIGNING_SECRET')
    CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', 0))


config = Config()
