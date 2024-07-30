# routes.py

import os
import base64
import logging
import random
import tempfile
import time
from io import BytesIO
from urllib.parse import parse_qs, urlparse

from quart import abort, request, send_file, make_response, current_app
from quart_rate_limiter import rate_limit

from cache_manager import cache_response
from config import config
from capture_request import CaptureRequest
from exceptions import ScreenshotServiceException, AuthenticationError
from request_auth import is_authenticated, verify_signed_url, generate_signed_url, SignatureExpiredError, \
    InvalidSignatureError


@current_app.before_request
async def auth_middleware():
    try:
        if request.path == '/capture' and request.method == 'GET':
            query_params = parse_qs(urlparse(request.url).query)
            verify_signed_url(query_params, config.URL_SIGNING_SECRET)
        elif not is_authenticated(request):
            raise AuthenticationError("Authentication failed")
    except (SignatureExpiredError, InvalidSignatureError, AuthenticationError) as e:
        abort(401, description=str(e))


def apply_rate_limit(f):
    if config.RATE_LIMIT_ENABLED:
        def rate_limit_func():
            if request.path == '/capture' and request.method == 'GET':
                return rate_limit(config.RATE_LIMIT_SIGNED)
            return rate_limit(config.RATE_LIMIT_CAPTURE)

        return current_app.container.rate_limiter.limit(rate_limit_func())(f)
    return f


@current_app.route('/capture', methods=['POST', 'GET'])
@apply_rate_limit
@cache_response
async def capture():
    try:
        if request.method == 'POST':
            options = CaptureRequest(**(await request.json))
        elif request.method == 'GET':
            query_params = parse_qs(urlparse(request.url).query)
            options = CaptureRequest(**{k: v[0] for k, v in query_params.items() if k not in ['signature', 'expires']})

        # Apply proxy settings from environment variables if not provided in the request
        if not options.proxy_server and config.PROXY_SERVER:
            options.proxy_server = config.PROXY_SERVER
        if not options.proxy_port and config.PROXY_PORT:
            options.proxy_port = int(config.PROXY_PORT)
        if not options.proxy_username and config.PROXY_USERNAME:
            options.proxy_username = config.PROXY_USERNAME
        if not options.proxy_password and config.PROXY_PASSWORD:
            options.proxy_password = config.PROXY_PASSWORD

        capture_service = current_app.container.capture_service

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
        current_app.logger.error(f"Invalid request parameters: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 400
    except ScreenshotServiceException as e:
        current_app.logger.error(f"Screenshot service error: {str(e)}")
        return {'status': 'error', 'message': str(e), 'errorType': e.__class__.__name__}, 500
    except Exception as e:
        current_app.logger.exception("Unexpected error occurred")
        return {'status': 'error', 'message': 'An unexpected error occurred while capturing.',
                'errorDetails': str(e)}, 500


@current_app.route('/sign_url', methods=['POST'])
@apply_rate_limit
async def generate_signed_url_route():
    try:
        data = await request.json
        capture_options = data.get('options', {})
        expiration = data.get('expiration', 3600)  # Default to 1 hour
        base_url = request.host_url + 'capture'
        signed_url = generate_signed_url(base_url, capture_options, config.URL_SIGNING_SECRET, expires_in=expiration)
        return {'signed_url': signed_url}
    except Exception as e:
        current_app.logger.exception("Error generating signed URL")
        return {'status': 'error', 'message': 'An error occurred while generating the signed URL.',
                'errorDetails': str(e)}, 500