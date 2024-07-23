import random
import traceback

from flask import Flask, request, send_file, after_this_request
import os
from urllib.parse import urlparse
import tempfile
import time
from screenshot_capture_service import ScreenshotCaptureService

app = Flask(__name__)


def auth_token_middleware():
    if os.environ.get('AUTH_TOKEN'):
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1] if auth_header else None

        if not token:
            return 'Authorization token is missing.', 401

        if token != os.environ.get('AUTH_TOKEN'):
            return 'Invalid authorization token.', 403


@app.route('/screenshot', methods=['POST'])
def screenshot():
    auth_result = auth_token_middleware()
    if auth_result:
        return auth_result

    data = request.json
    target_url = data.get('url')
    window_width = data.get('windowWidth', 1280)
    window_height = data.get('windowHeight', 720)
    use_proxy = data.get('useProxy', True)

    if not target_url:
        return {'status': 'error', 'message': 'Missing required parameter: url'}, 400

    try:
        capture_service = ScreenshotCaptureService(
            os.environ.get('PROXY_SERVER'),
            os.environ.get('PROXY_PORT'),
            os.environ.get('PROXY_USERNAME'),
            os.environ.get('PROXY_PASSWORD'),
            use_proxy
        )

        hostname = urlparse(target_url).hostname.replace('.', '-')
        screenshot_path = f"{tempfile.gettempdir()}/{hostname}_{int(time.time())}_{int(random.random() * 10000)}.png"

        capture_service.capture_screenshot(target_url, screenshot_path, window_width, window_height, 2.0)

        print(f"Returning screenshot from {screenshot_path}")

        @after_this_request
        def remove_file(response):
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            return response

        return send_file(screenshot_path, mimetype='image/png')

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
