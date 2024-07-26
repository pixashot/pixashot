import pytest
from quart import Quart
from unittest.mock import patch, Mock
from src.app import app, capture_service
from src.exceptions import ScreenshotServiceException


@pytest.fixture
def test_app():
    app.config['TESTING'] = True
    return app


@pytest.mark.asyncio
async def test_screenshot_endpoint_success(test_app):
    client = test_app.test_client()

    mock_capture_service = Mock()
    mock_capture_service.capture_screenshot.return_value = b'fake image data'

    with patch('src.app.capture_service', mock_capture_service):
        response = await client.post('/capture', json={
            "url": "https://example.com",
            "format": "png"
        })

    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'image/png'
    assert await response.get_data() == b'fake image data'


@pytest.mark.asyncio
async def test_screenshot_endpoint_invalid_params(test_app):
    client = test_app.test_client()

    response = await client.post('/capture', json={
        "format": "png"
    })

    assert response.status_code == 400
    response_data = await response.get_json()
    assert "Either url or html_content must be provided" in response_data['message']


@pytest.mark.asyncio
async def test_screenshot_endpoint_service_exception(test_app):
    client = test_app.test_client()

    mock_capture_service = Mock()
    mock_capture_service.capture_screenshot.side_effect = ScreenshotServiceException(
        "An unexpected error occurred while capturing.")

    with patch('src.app.capture_service', mock_capture_service):
        response = await client.post('/capture', json={
            "url": "https://example.com",
            "format": "png"
        })

    assert response.status_code == 500
    response_data = await response.get_json()
    assert response_data['status'] == 'error'
    assert 'An unexpected error occurred while capturing.' in response_data['message']


@pytest.mark.asyncio
async def test_auth_token_middleware(test_app):
    client = test_app.test_client()

    with patch.dict('os.environ', {'AUTH_TOKEN': 'test_token'}):
        # Test with correct token
        response = await client.post('/capture',
                                     json={"url": "https://example.com", "format": "png"},
                                     headers={"Authorization": "Bearer test_token"})
        assert response.status_code != 401

        # Test with incorrect token
        response = await client.post('/capture',
                                     json={"url": "https://example.com", "format": "png"},
                                     headers={"Authorization": "Bearer wrong_token"})
        assert response.status_code == 403

        # Test without token
        response = await client.post('/capture',
                                     json={"url": "https://example.com", "format": "png"})
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_rate_limiting(test_app):
    client = test_app.test_client()

    with patch.dict('os.environ', {'RATE_LIMIT_ENABLED': 'true', 'RATE_LIMIT_CAPTURE': '1 per minute'}):
        # First request should succeed
        response = await client.post('/capture', json={"url": "https://example.com", "format": "png"})
        assert response.status_code != 429

        # Second request within the minute should fail
        response = await client.post('/capture', json={"url": "https://example.com", "format": "png"})
        assert response.status_code == 429