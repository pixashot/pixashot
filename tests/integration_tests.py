import pytest
from playwright.async_api import async_playwright
from quart import Quart
from src.app import create_app, AppContainer
from src.capture_request import CaptureRequest
from src.cache_manager import CacheManager


@pytest.fixture(scope='module')
async def app() -> Quart:
    """Create and configure a test app instance."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture(scope='module')
async def initialized_container(app: Quart) -> AppContainer:
    """Initialize the app container with all necessary services."""
    container = app.config['container']
    await container.initialize()
    yield container
    await container.close()


@pytest.fixture
async def test_client(app: Quart, initialized_container):
    """Create a test client with the initialized container."""
    return app.test_client()


@pytest.mark.asyncio
async def test_screenshot_endpoint_png(test_client):
    """Test capturing a PNG screenshot."""
    test_data = {
        "url": "https://example.com",
        "format": "png",
        "window_width": 1280,
        "window_height": 720,
        "full_page": True
    }

    response = await test_client.post('/capture', json=test_data)

    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'image/png'
    assert response.headers['Content-Disposition'].startswith('attachment; filename=screenshot.png')

    content = await response.get_data()
    assert len(content) > 0
    assert content.startswith(b'\x89PNG')  # PNG magic number


@pytest.mark.asyncio
async def test_screenshot_endpoint_jpeg(test_client):
    """Test capturing a JPEG screenshot."""
    test_data = {
        "url": "https://example.com",
        "format": "jpeg",
        "image_quality": 80,
        "window_width": 1280,
        "window_height": 720
    }

    response = await test_client.post('/capture', json=test_data)

    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'image/jpeg'
    assert response.headers['Content-Disposition'].startswith('attachment; filename=screenshot.jpeg')

    content = await response.get_data()
    assert len(content) > 0
    assert content.startswith(b'\xff\xd8\xff')  # JPEG magic number


@pytest.mark.asyncio
async def test_screenshot_endpoint_pdf(test_client):
    """Test capturing a PDF."""
    test_data = {
        "url": "https://example.com",
        "format": "pdf",
        "full_page": True,
        "pdf_format": "A4"
    }

    response = await test_client.post('/capture', json=test_data)

    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'
    assert response.headers['Content-Disposition'].startswith('attachment; filename=screenshot.pdf')

    content = await response.get_data()
    assert len(content) > 0
    assert content.startswith(b'%PDF')  # PDF magic number


@pytest.mark.asyncio
async def test_screenshot_with_interactions(test_client):
    """Test capturing a screenshot with user interactions."""
    test_data = {
        "url": "https://example.com",
        "format": "png",
        "interactions": [
            {
                "action": "click",
                "selector": "#accept-cookies"
            },
            {
                "action": "wait_for",
                "wait_for": {
                    "type": "network_idle",
                    "value": 1000
                }
            }
        ]
    }

    response = await test_client.post('/capture', json=test_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_screenshot_with_html_content(test_client):
    """Test capturing a screenshot from HTML content."""
    test_data = {
        "html_content": "<html><body><h1>Test Heading</h1></body></html>",
        "format": "png",
        "window_width": 800,
        "window_height": 600
    }

    response = await test_client.post('/capture', json=test_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_request(test_client):
    """Test handling of invalid request parameters."""
    test_data = {
        # Missing both url and html_content
        "format": "png"
    }

    response = await test_client.post('/capture', json=test_data)
    assert response.status_code == 400

    response_json = await response.get_json()
    assert 'error' in response_json['message'].lower()


@pytest.mark.asyncio
async def test_health_endpoint(test_client):
    """Test the health check endpoint."""
    response = await test_client.get('/health')
    assert response.status_code == 200

    response_json = await response.get_json()
    assert response_json['status'] == 'healthy'
    assert 'checks' in response_json
    assert 'memory_usage_mb' in response_json['checks']
    assert 'cpu_percent' in response_json['checks']


@pytest.mark.asyncio
async def test_liveness_endpoint(test_client):
    """Test the liveness endpoint."""
    response = await test_client.get('/health/live')
    assert response.status_code == 200

    response_json = await response.get_json()
    assert response_json['status'] == 'alive'


@pytest.mark.asyncio
async def test_dark_mode_screenshot(test_client):
    """Test capturing a screenshot with dark mode enabled."""
    test_data = {
        "url": "https://example.com",
        "format": "png",
        "dark_mode": True
    }

    response = await test_client.post('/capture', json=test_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_geolocation_screenshot(test_client):
    """Test capturing a screenshot with geolocation spoofing."""
    test_data = {
        "url": "https://example.com",
        "format": "png",
        "geolocation": {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "accuracy": 100
        }
    }

    response = await test_client.post('/capture', json=test_data)
    assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, "-v"])