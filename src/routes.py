import os
import base64
import logging
import random
import tempfile
import time
from datetime import datetime
from io import BytesIO
from urllib.parse import parse_qs, urlparse
import psutil

from quart import (
    abort,
    current_app,
    make_response,
    request,
    send_file,
)

from cache_manager import cache_response
from capture_request import CaptureRequest


def register_routes(app):
    @app.route('/capture', methods=['POST', 'GET'])
    async def capture():
        try:
            if request.method == 'POST':
                options = CaptureRequest(**(await request.json))
            elif request.method == 'GET':
                query_params = parse_qs(urlparse(request.url).query)
                options = CaptureRequest(**{k: v[0] for k, v in query_params.items()})

            capture_service = current_app.config['container'].capture_service

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
        except Exception as e:
            current_app.logger.exception("Unexpected error occurred")
            return {'status': 'error', 'message': 'An unexpected error occurred while capturing.',
                    'errorDetails': str(e)}, 500

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