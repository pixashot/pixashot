import os
import base64
import logging
import random
import tempfile
import time
import traceback
from logging.config import dictConfig
from io import BytesIO

from quart import Quart, abort, request, send_file, make_response
from quart_rate_limiter import RateLimiter, rate_limit

from config import get_logging_config
from capture_request import CaptureRequest
from capture_service import CaptureService
from exceptions import ScreenshotServiceException
from playwright.async_api import async_playwright
from request_auth import is_authenticated

# Configure logging
dictConfig(get_logging_config())

app = Quart(__name__)
capture_service = CaptureService()

# Read rate limiting configuration from environment variables
RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'False').lower() == 'true'
RATE_LIMIT_CAPTURE = os.environ.get('RATE_LIMIT_CAPTURE', '1 per second')

# Read proxy settings from environment variables
PROXY_SERVER = os.environ.get('PROXY_SERVER')
PROXY_PORT = os.environ.get('PROXY_PORT')
PROXY_USERNAME = os.environ.get('PROXY_USERNAME')
PROXY_PASSWORD = os.environ.get('PROXY_PASSWORD')

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
    await capture_service.close()


@app.before_request
async def auth_middleware():
    if not is_authenticated(request):
        abort(401, description="Authentication failed. Provide a valid auth token or use a signed URL.")


def apply_rate_limit(f):
    if RATE_LIMIT_ENABLED:
        return rate_limit(RATE_LIMIT_CAPTURE)(f)
    return f


@app.route('/capture', methods=['POST'])
@apply_rate_limit
async def capture():
    try:
        options = CaptureRequest(**(await request.json))

        # Apply proxy settings from environment variables if not provided in the request
        if not options.proxy_server and PROXY_SERVER:
            options.proxy_server = PROXY_SERVER
        if not options.proxy_port and PROXY_PORT:
            options.proxy_port = int(PROXY_PORT)
        if not options.proxy_username and PROXY_USERNAME:
            options.proxy_username = PROXY_USERNAME
        if not options.proxy_password and PROXY_PASSWORD:
            options.proxy_password = PROXY_PASSWORD

    except ValueError as e:
        app.logger.error(f"Invalid request parameters: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 400

    try:
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

    except ScreenshotServiceException as e:
        app.logger.error(f"Screenshot service error: {str(e)}")
        return {
            'status': 'error',
            'message': str(e),
            'errorType': e.__class__.__name__
        }, 500
    except Exception as e:
        app.logger.exception("Unexpected error occurred")
        return {
            'status': 'error',
            'message': 'An unexpected error occurred while capturing.',
            'errorDetails': str(e),
            'stackTrace': traceback.format_exc()
        }, 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)