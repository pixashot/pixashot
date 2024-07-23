import os
import random
import tempfile
import time
import traceback
from urllib.parse import urlparse

from flask import Flask, abort, after_this_request, request, send_file

from screenshot_capture_service import ScreenshotCaptureService

app = Flask(__name__)

# Create a single instance of ScreenshotCaptureService
capture_service = ScreenshotCaptureService()

# Set up proxy if environment variables are present
proxy_server = os.environ.get('PROXY_SERVER')
proxy_port = os.environ.get('PROXY_PORT')
proxy_username = os.environ.get('PROXY_USERNAME')
proxy_password = os.environ.get('PROXY_PASSWORD')

if proxy_server and proxy_port:
    capture_service.setup_proxy(
        proxy_server,
        proxy_port,
        proxy_username,
        proxy_password
    )
    print("Proxy configured for screenshot capture.")
else:
    print("PROXY_SERVER or PROXY_PORT not set. Proceeding without proxy.")


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
    data = request.json
    target_url = data.get('url')
    window_width = data.get('windowWidth', 1280)
    window_height = data.get('windowHeight', 720)

    if not target_url:
        return {'status': 'error', 'message': 'Missing required parameter: url'}, 400

    try:
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