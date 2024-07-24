import os
import random
import tempfile
import time
import traceback
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
        data = ScreenshotRequest(**request.json)
    except ValueError as e:
        return {'status': 'error', 'message': str(e)}, 400

    try:
        hostname = urlparse(str(data.url)).hostname.replace('.', '-')
        screenshot_path = f"{tempfile.gettempdir()}/{hostname}_{int(time.time())}_{int(random.random() * 10000)}.png"

        options = {
            'windowWidth': data.windowWidth,
            'windowHeight': data.windowHeight,
            'pixel_density': data.pixel_density,
            'proxy_server': data.proxy_server,
            'proxy_port': data.proxy_port,
            'proxy_username': data.proxy_username,
            'proxy_password': data.proxy_password,
            'ignore_https_errors': data.ignore_https_errors,
            'full_page': data.full_page,
            'scroll_to_bottom': data.scroll_to_bottom,
            'max_scrolls': data.max_scrolls,
            'scroll_timeout': data.scroll_timeout,
            'wait_for_timeout': data.wait_for_timeout,
            'headless': data.headless,
            'format': data.format,
        }

        capture_service.capture_screenshot(str(data.url), screenshot_path, options)

        print(f"Returning screenshot from {screenshot_path}")

        @after_this_request
        def remove_file(response):
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            return response

        return send_file(screenshot_path, mimetype=f'image/{data.format}')

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
