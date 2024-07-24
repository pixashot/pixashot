import base64
import os
import random
import tempfile
import time
import traceback
from urllib.parse import urlparse

from flask import Flask, abort, after_this_request, request, send_file

from screenshot_capture_service import ScreenshotCaptureService
from screenshot_request import ScreenshotRequest
import logging
from logging.config import dictConfig
from exceptions import ScreenshotServiceException

# Configure logging
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)

# Create a single instance of ScreenshotCaptureService
capture_service = ScreenshotCaptureService()


@app.before_request
def auth_token_middleware():
    if os.environ.get('AUTH_TOKEN'):
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1] if auth_header else None

        if not token:
            abort(401, description="Authorization token is missing.")

        if token != os.environ.get('AUTH_TOKEN'):
            abort(403, description="Invalid authorization token.")


@app.route('/screenshot', methods=['POST'])
def screenshot():
    try:
        options = ScreenshotRequest(**request.json)
    except ValueError as e:
        app.logger.error(f"Invalid request parameters: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 400

    try:
        hostname = urlparse(str(options.url)).hostname.replace('.', '-')
        screenshot_path = f"{tempfile.gettempdir()}/{hostname}_{int(time.time())}_{int(random.random() * 10000)}.{options.format}"

        capture_service.capture_screenshot(str(options.url), screenshot_path, options)

        @after_this_request
        def remove_file(response):
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            return response

        if options.response_type == 'empty':
            return '', 204
        elif options.response_type == 'json':
            with open(screenshot_path, 'rb') as f:
                image_data = f.read()
            return {'image': base64.b64encode(image_data).decode('utf-8')}, 200
        else:  # by_format
            return send_file(screenshot_path, mimetype=f'image/{options.format}')

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
            'message': 'An unexpected error occurred while capturing the screenshot.',
            'errorDetails': str(e),
            'stackTrace': traceback.format_exc()
        }, 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
