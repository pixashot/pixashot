import base64
import logging
import os
import random
import tempfile
import time
import traceback
from logging.config import dictConfig
from urllib.parse import urlparse

from flask import Flask, abort, after_this_request, request, send_file

from config import get_logging_config
from screenshot_request import ScreenshotRequest
from screenshot_capture_service import ScreenshotCaptureService
from exceptions import ScreenshotServiceException

# Configure logging
dictConfig(get_logging_config())

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

    if not options.url and not options.html_content:
        return {'status': 'error', 'message': 'Either url or html_content must be provided'}, 400

    try:
        if options.url:
            hostname = urlparse(str(options.url)).hostname.replace('.', '-')
        else:
            hostname = 'html-content'

        # Simplified file extension handling
        output_path = f"{tempfile.gettempdir()}/{hostname}_{int(time.time())}_{int(random.random() * 10000)}.{options.format}"

        capture_service.capture_screenshot(output_path, options)

        @after_this_request
        def remove_file(response):
            if os.path.exists(output_path):
                os.remove(output_path)
            return response

        if options.response_type == 'empty':
            return '', 204
        elif options.response_type == 'json':
            with open(output_path, 'rb') as f:
                file_data = f.read()
            return {'file': base64.b64encode(file_data).decode('utf-8')}, 200
        else:  # by_format
            mime_type = 'application/pdf' if options.format == 'pdf' else f'image/{options.format}'
            return send_file(output_path, mimetype=mime_type)

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
