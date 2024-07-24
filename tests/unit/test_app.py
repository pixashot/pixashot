import pytest
from unittest.mock import patch, Mock
from src.app import app
from src.exceptions import ScreenshotServiceException


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_screenshot_endpoint_success(client):
    mock_capture_service = Mock()
    mock_capture_service.capture_screenshot.return_value = None

    with patch('src.app.capture_service', mock_capture_service):
        response = client.post('/capture', json={
            "url": "https://example.com",
            "format": "png"
        })

    assert response.status_code == 200
    assert response.content_type == 'image/png'


def test_screenshot_endpoint_invalid_params(client):
    response = client.post('/capture', json={
        "format": "png"
    })

    assert response.status_code == 400
    assert b"Either url or html_content must be provided" in response.data


def test_screenshot_endpoint_service_exception(client):
    mock_capture_service = Mock()
    mock_capture_service.capture_screenshot.side_effect = Screen