import os
import random
import tempfile
import time
from urllib.parse import urlparse

from flask import Flask, abort, after_this_request, request, send_file

from screenshot_capture_service import ScreenshotCaptureService
from screenshot_request import ScreenshotRequest

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
        return {'status': 'error', 'message': str(e)}, 400

    try:
        hostname = urlparse(str(options.url)).hostname.replace('.', '-')
        screenshot_path = f"{tempfile.gettempdir()}/{hostname}_{int(time.time())}_{int(random.random() * 10000)}.png"

        capture_service.capture_screenshot(str(options.url), screenshot_path, options)

        @after_this_request
        def remove_file(response):
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            return response

        return send_file(screenshot_path, mimetype=f'image/{options.format}')

    except Exception as err:
        return {
            'status': 'error',
            'message': 'An unexpected error occurred while capturing the screenshot.',
            'errorDetails': str(err),
            'stackTrace': traceback.format_exc()
        }, 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
