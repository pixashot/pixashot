import base64
import logging
import os
import random
import tempfile
import time
import traceback
from logging.config import dictConfig
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from io import BytesIO

from quart import Quart, abort, request, send_file, make_response
from quart_rate_limiter import RateLimiter, rate_limit

from config import get_logging_config
from capture_request import CaptureRequest
from capture_service import CaptureService
from exceptions import ScreenshotServiceException
from playwright.async_api import async_playwright

# Configure logging
dictConfig(get_logging_config())

app = Quart(__name__)
capture_service = CaptureService()

# Read rate limiting configuration from environment variables
RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'False').lower() == 'true'
RATE_LIMIT_CAPTURE = os.environ.get('RATE_LIMIT_CAPTURE', '1 per second')

# Initialize rate limiter
limiter = RateLimiter(app)


@app.before_serving
async def startup():
    playwright = await async_playwright().start()
    await capture_service.initialize(playwright)


@app.after_serving
async def shutdown():
    await capture_service.close()


@app.before_request
async def auth_token_middleware():
    if os.environ.get('AUTH_TOKEN'):
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1] if auth_header else None

        if not token:
            abort(401, description="Authorization token is missing.")

        if token != os.environ.get('AUTH_TOKEN'):
            abort(403, description="Invalid authorization token.")


@app.route('/capture', methods=['POST'])
@rate_limit(RATE_LIMIT_CAPTURE) if RATE_LIMIT_ENABLED else lambda x: x
async def capture():
    try:
        options = CaptureRequest(**(await request.json))
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
