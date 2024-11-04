# Standard library imports
import os
import base64
import logging
import random
import tempfile
import time
from datetime import datetime
from io import BytesIO
from urllib.parse import parse_qs, urlparse

# Third-party imports
from quart import (
    abort,
    current_app,
    make_response,
    request,
    send_file,
)
from quart_rate_limiter import rate_limit

# Local application imports
from cache_manager import cache_response
from config import config
from capture_request import CaptureRequest
from exceptions import (
    AuthenticationError,
    ScreenshotServiceException,
    SignatureExpiredError,
    InvalidSignatureError,
)
from request_auth import (
    generate_signed_url,
    is_authenticated,
    verify_signed_url,
)


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


@current_app.route('/health')
@current_app.route('/health/ready')
async def health_check():
    """
    Health check endpoint that verifies:
    1. Service is up
    2. Can create a browser context
    3. Memory usage is within bounds
    4. Service has been running for a known duration
    """
    try:
        # Try to get a browser context with minimal options
        context = await current_app.container.capture_service.context_manager.get_context(
            CaptureRequest(url="about:blank")
        )

        # Get process metrics
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_percent = process.cpu_percent()

        # Get context manager metrics
        active_contexts = len(current_app.container.capture_service.context_manager.contexts)

        # Calculate uptime if start_time exists
        uptime = time.time() - current_app.start_time if hasattr(current_app, 'start_time') else 0

        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'browser_context': 'ok',
                'memory_usage_mb': round(memory_usage, 2),
                'cpu_percent': round(cpu_percent, 2),
                'active_contexts': active_contexts,
                'uptime_seconds': round(uptime, 2)
            },
            'version': os.getenv('VERSION', '1.0.0')
        }, 200

    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }, 503


@current_app.route('/health/live')
async def liveness():
    """
    Simple liveness check that just confirms the service is running
    and can respond to HTTP requests.
    """
    return {'status': 'alive'}, 200