import os
from dotenv import load_dotenv

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

from cache_manager import CacheManager, cache_response
from config import get_logging_config
from capture_request import CaptureRequest
from capture_service import CaptureService
from exceptions import ScreenshotServiceException, AuthenticationError
from playwright.async_api import async_playwright
from request_auth import is_authenticated, verify_signed_url, generate_signed_url, SignatureExpiredError, \
    InvalidSignatureError

# Load .env file if it exists
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

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
CACHE_MAX_SIZE = int(os.environ.get('CACHE_MAX_SIZE', 0))

# Initialize rate limiter
limiter = RateLimiter(app)


# Configure caching
app.config['CACHING_ENABLED'] = CACHE_MAX_SIZE > 0
app.cache_manager = CacheManager(max_size=CACHE_MAX_SIZE if app.config['CACHING_ENABLED'] else None)

# Log caching status
if app.config['CACHING_ENABLED']:
    app.logger.info(f"Caching enabled with max size: {CACHE_MAX_SIZE}")
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
@cache_response
async def capture():
    try:
        if request.method == 'POST':
            options = CaptureRequest(**(await request.json))
        elif request.method == 'GET':
            query_params = parse_qs(urlparse(request.url).query)
            options = CaptureRequest(**{k: v[0] for k, v in query_params.items() if k not in ['signature', 'expires']})

        # Apply proxy settings from environment variables
        options.apply_proxy_settings(PROXY_SERVER, PROXY_PORT, PROXY_USERNAME, PROXY_PASSWORD)

        # Apply proxy settings from environment variables if not provided in the request
        if not options.proxy_server and PROXY_SERVER:
            options.proxy_server = PROXY_SERVER
        if not options.proxy_port and PROXY_PORT:
            options.proxy_port = int(PROXY_PORT)
        if not options.proxy_username and PROXY_USERNAME:
            options.proxy_username = PROXY_USERNAME
        if not options.proxy_password and PROXY_PASSWORD:
            options.proxy_password = PROXY_PASSWORD

        if options.format == 'html':
            html_content = await capture_service.capture_screenshot(None, options)
            if options.response_type == 'json':
                return {'html': base64.b64encode(html_content.encode()).decode('utf-8')}, 200
            else:
                response = await make_response(html_content)
                response.headers['Content-Type'] = 'text/html'
                return response
        else:
            if options.url:
                hostname = urlparse(str(options.url)).hostname.replace('.', '-')
            else:
                hostname = 'html-content'

            output_path = f"{tempfile.gettempdir()}/{hostname}_{int(time.time())}_{int(random.random() * 10000)}.{options.format}"

            await capture_service.capture_screenshot(output_path, options)

            if options.response_type == 'empty':
                os.remove(output_path)
                return '', 204
            elif options.response_type == 'json':
                with open(output_path, 'rb') as f:
                    file_data = f.read()
                os.remove(output_path)
                return {'file': base64.b64encode(file_data).decode('utf-8')}, 200
            else:  # by_format
                mime_type = 'application/pdf' if options.format == 'pdf' else f'image/{options.format}'
                with open(output_path, 'rb') as f:
                    file_data = f.read()
                os.remove(output_path)
                return await send_file(
                    BytesIO(file_data),
                    mimetype=mime_type,
                    as_attachment=True,
                    attachment_filename=f"screenshot.{options.format}"
                )

    except ValueError as e:
        app.logger.error(f"Invalid request parameters: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 400
    except ScreenshotServiceException as e:
        app.logger.error(f"Screenshot service error: {str(e)}")
        return {'status': 'error', 'message': str(e), 'errorType': e.__class__.__name__}, 500
    except Exception as e:
        app.logger.exception("Unexpected error occurred")
        return {'status': 'error', 'message': 'An unexpected error occurred while capturing.',
                'errorDetails': str(e)}, 500


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
        return {'status': 'error', 'message': 'An error occurred while generating the signed URL.',
                'errorDetails': str(e)}, 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
