import pytest
from playwright.async_api import async_playwright
from src.app import app
from src.capture_service import CaptureService

@pytest.fixture(scope='module')
async def initialized_app():
    async with async_playwright() as playwright:
        app.capture_service = CaptureService(playwright)
        yield app
        await app.capture_service.close()

@pytest.fixture
async def test_client(initialized_app):
    return initialized_app.test_client()

@pytest.mark.asyncio
async def test_screenshot_endpoint(test_client):
    # Test data
    test_data = {
        "url": "https://example.com",
        "format": "png",
        "window_width": 1280,
        "window_height": 720,
        "full_page": True
    }

    # Make a POST request to the /capture endpoint
    response = await test_client.post('/capture', json=test_data)

    # Check if the request was successful
    assert response.status_code == 200

    # Check if the response is a PNG image
    assert response.headers['Content-Type'] == 'image/png'

    # Check if the response has content
    assert len(await response.get_data()) > 0

if __name__ == '__main__':
    pytest.main([__file__, "-v"])