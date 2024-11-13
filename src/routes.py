import os
import base64
import logging
import random
import tempfile
import time
from datetime import datetime
from urllib.parse import parse_qs, urlparse
import psutil

from quart import (
    abort,
    current_app,
    make_response,
    request,
    send_file, jsonify,
)

from cache_manager import cache_response
from capture_request import CaptureRequest
from exceptions import ScreenshotServiceException

logger = logging.getLogger(__name__)


def register_routes(app):
    def is_development():
        """Check if we're running in development mode"""
        return app.debug or os.environ.get('FLASK_ENV') == 'development'

    @app.route('/capture', methods=['POST', 'GET'])
    async def capture():
        """
        Handle screenshot capture requests with development-aware error handling.
        """
        try:
            # Parse request parameters
            if request.method == 'POST':
                request_json = await request.get_json()
                options = CaptureRequest(**request_json)
            elif request.method == 'GET':
                query_params = parse_qs(urlparse(request.url).query)
                options = CaptureRequest(**{k: v[0] for k, v in query_params.items()})
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Only POST and GET methods are supported'
                }), 400

            capture_service = current_app.config['container'].capture_service

            # Handle HTML format separately
            if options.format == 'html':
                html_content = await capture_service.capture_screenshot(None, options)
                if options.response_type == 'json':
                    return jsonify({
                        'file': base64.b64encode(html_content.encode()).decode('utf-8'),
                        'format': 'html'
                    }), 200
                else:
                    response = await make_response(html_content)
                    response.headers['Content-Type'] = 'text/html'
                    return response

            # Generate unique output filename
            if options.url:
                hostname = urlparse(str(options.url)).hostname.replace('.', '-')
            else:
                hostname = 'html-content'

            timestamp = int(time.time())
            random_suffix = int(random.random() * 10000)
            output_path = f"{tempfile.gettempdir()}/{hostname}_{timestamp}_{random_suffix}.{options.format}"

            # Capture the screenshot
            try:
                await capture_service.capture_screenshot(output_path, options)
            except Exception as capture_error:
                if os.path.exists(output_path):
                    os.remove(output_path)
                raise capture_error

            # Handle different response types
            try:
                if options.response_type == 'empty':
                    os.remove(output_path)
                    return '', 204

                elif options.response_type == 'json':
                    with open(output_path, 'rb') as f:
                        file_data = f.read()
                    os.remove(output_path)
                    return jsonify({
                        'file': base64.b64encode(file_data).decode('utf-8'),
                        'format': options.format
                    }), 200

                else:  # by_format
                    mime_type = 'application/pdf' if options.format == 'pdf' else f'image/{options.format}'
                    with open(output_path, 'rb') as f:
                        file_data = f.read()
                    os.remove(output_path)

                    response = await make_response(file_data)
                    response.headers['Content-Type'] = mime_type
                    response.headers['Content-Disposition'] = f'attachment; filename=screenshot.{options.format}'
                    return response

            except Exception as e:
                if os.path.exists(output_path):
                    os.remove(output_path)
                raise e

        except ValueError as e:
            if is_development():
                raise  # Re-raise the exception in development mode
            logger.error(f"Invalid request parameters: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'error_type': 'ValidationError'
            }), 400

        except Exception as e:
            if is_development():
                raise  # Re-raise the exception in development mode

            logger.exception("Error during capture")

            error_response = {
                'status': 'error',
                'message': 'An unexpected error occurred while capturing.',
                'timestamp': datetime.utcnow().isoformat()
            }

            if isinstance(e, ScreenshotServiceException) and isinstance(e.args[0], dict):
                error_details = e.args[0]
                error_response.update({
                    'error_type': error_details.get('type', 'Unknown'),
                    'error_details': error_details.get('message', str(e)),
                    'retry_attempts': [
                        {
                            'attempt': attempt.get('attempt'),
                            'error': attempt.get('error'),
                            'error_type': attempt.get('error_type'),
                            'timestamp': attempt.get('timestamp')
                        }
                        for attempt in error_details.get('retry_attempts', [])
                    ],
                    'call_stack': error_details.get('call_stack')
                })
            else:
                error_response.update({
                    'error_type': e.__class__.__name__,
                    'error_details': str(e),
                    'call_stack': getattr(e, 'message', str(e))
                })

            return jsonify(error_response), 500

    @app.route('/health')
    @app.route('/health/ready')
    async def health_check():
        """Health check endpoint"""
        try:
            process = psutil.Process(os.getpid())
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            cpu_percent = process.cpu_percent()

            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'checks': {
                    'memory_usage_mb': round(memory_usage, 2),
                    'cpu_percent': round(cpu_percent, 2)
                },
                'version': os.getenv('VERSION', '1.0.0')
            }, 200

        except Exception as e:
            if is_development():
                raise  # Re-raise the exception in development mode
            current_app.logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }, 503

    @app.route('/health/live')
    async def liveness():
        """Simple liveness check"""
        return {'status': 'alive'}, 200