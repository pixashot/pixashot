import os
import base64
import logging
import random
import tempfile
import time
import traceback
from logging.config import dictConfig
from io import BytesIO
from urllib.parse import parse_qs, urlparse

from quart import Quart, abort, request, send_file, make_response
from quart_rate_limiter import RateLimiter, rate_limit

from config import get_logging_config
from capture_request import CaptureRequest
from capture_service import CaptureService
from exceptions import ScreenshotServiceException, AuthenticationError
from playwright.async_api import async_playwright
from request_auth import is_authenticated, verify_signed_url, generate_signed_url, SignatureExpiredError, InvalidSignatureError

# Configure logging
dictConfig(get_logging_config())

app = Quart(__name__)
capture_service = CaptureService()

# Read configuration from environment variables
RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'False').lower() == 'true'
RATE_LIMIT_CAPTURE = os.environ.get('RATE_LIMIT_CAPTURE', '1 per second')
RATE_LIMIT_SIGNED = os.environ.get('RATE_LIMIT_SIGNED', '5 per second')
PROXY_SERVER = os.environ.get('PROXY_SERVER')
PROXY_PORT = os.environ.get('PROXY_PORT')
PROXY_USERNAME = os.environ.get('PROXY_USERNAME')
PROXY_PASSWORD = os.environ.get('PROXY_PASSWORD')
URL_SIGNING_SECRET = os.environ.get('URL_SIGNING_SECRET')

# Initialize rate limiter
limiter = RateLimiter(app)

@app.before_serving
async def startup():
    global capture_service
    playwright = await async_playwright().start()
    capture_service = CaptureService()
    await capture_service.initialize(playwright)


@app.after_serving
async def shutdown():

@app.before_request
async def auth_middleware():
    try:
        if request.path == '/capture' and request.method == 'GET':
            query_params = parse_qs(urlparse(request.url).query)
            verify_signed_url(query_params, URL_SIGNING_SECRET)
        elif not is_authenticated(request):
            raise AuthenticationError("Authentication failed")
    except (SignatureExpiredError, InvalidSignatureError, AuthenticationError) as e:
        abort(401, description=str(e))

def apply_rate_limit(f):
    if RATE_LIMIT_ENABLED:
        def rate_limit_func():
            if request.path == '/capture' and request.method == 'GET':
                return rate_limit(RATE_LIMIT_SIGNED)
            return rate_limit(RATE_LIMIT_CAPTURE)
        return rate_limit_func()(f)
    return f

@app.route('/capture', methods=['POST', 'GET'])
@apply_rate_limit
async def capture():
    try:
        if request.method == 'POST':
            options = CaptureRequest(**(await request.json))
        elif request.method == 'GET':
            query_params = parse_qs(urlparse(request.url).query)
            options = CaptureRequest(**{k: v[0] for k, v in query_params.items() if k not in ['signature', 'expires']})

        # Apply proxy settings from environment variables
        options.apply_proxy_settings(PROXY_SERVER, PROXY_PORT, PROXY_USERNAME, PROXY_PASSWORD)

        # ... [rest of the capture function remains the same] ...

    except ValueError as e:
        app.logger.error(f"Invalid request parameters: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 400
    except ScreenshotServiceException as e:
        app.logger.error(f"Screenshot service error: {str(e)}")
        return {'status': 'error', 'message': str(e), 'errorType': e.__class__.__name__}, 500
    except Exception as e:
        app.logger.exception("Unexpected error occurred")
        return {'status': 'error', 'message': 'An unexpected error occurred while capturing.', 'errorDetails': str(e)}, 500

@app.route('/sign_url', methods=['POST'])
@apply_rate_limit
async def generate_signed_url_route():
    try:
        data = await request.json
        capture_options = data.get('options', {})
        expiration = data.get('expiration', 3600)  # Default to 1 hour
        base_url = request.host_url + 'capture'
        signed_url = generate_signed_url(base_url, capture_options, URL_SIGNING_SECRET, expires_in=expiration)
        return {'signed_url': signed_url}
    except Exception as e:
        app.logger.exception("Error generating signed URL")
        return {'status': 'error', 'message': 'An error occurred while generating the signed URL.', 'errorDetails': str(e)}, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)