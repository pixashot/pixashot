import base64
import logging
import os
import random
import tempfile
import time
import traceback
from logging.config import dictConfig
from urllib.parse import urlparse

from flask import Flask, abort, after_this_request, request, send_file, make_response

from config import get_logging_config
from capture_request import CaptureRequest
from capture_service import CaptureService
from exceptions import ScreenshotServiceException

# Configure logging
dictConfig(get_logging_config())

app = Flask(__name__)

# Create a single instance of CaptureService
capture_service = CaptureService()


@app.before_request
def auth_token_middleware():
    if os.environ.get('AUTH_TOKEN'):
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1] if auth_header else None

        if not token:
            abort(401, description="Authorization token is missing.")

        if token != os.environ.get('AUTH_TOKEN'):
            abort(403, description="Invalid authorization token.")


@app.route('/capture', methods=['POST'])
def capture():
    try:
        options = CaptureRequest(**request.json)
    except ValueError as e:
        app.logger.error(f"Invalid request parameters: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 400

    try:
        if options.format == 'html':
            html_content = capture_service.capture_screenshot(None, options)
            if options.response_type == 'json':
                return {'html': base64.b64encode(html_content.encode()).decode('utf-8')}, 200
            else:
                response = make_response(html_content)
                response.headers['Content-Type'] = 'text/html'
                return response
        else:
            if options.url:
                hostname = urlparse(str(options.url)).hostname.replace('.', '-')
            else:
                hostname = 'html-content'

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
