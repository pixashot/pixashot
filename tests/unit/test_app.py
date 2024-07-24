import os
import tempfile

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

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
        temp_file.write(b'fake image data')
        temp_file_path = temp_file.name

    # Mock the capture_screenshot method to use the temp file
    def mock_capture_screenshot(output_path, options):
        with open(output_path, 'wb') as f:
            f.write(b'fake image data')

    mock_capture_service.capture_screenshot.side_effect = mock_capture_screenshot

    try:
        with patch('src.app.capture_service', mock_capture_service):
            response = client.post('/capture', json={
                "url": "https://example.com",
                "format": "png"
            })

        assert response.status_code == 200
        assert response.content_type == 'image/png'
        assert response.data == b'fake image data'
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)


def test_screenshot_endpoint_invalid_params(client):
    response = client.post('/capture', json={
        "format": "png"
    })

    assert response.status_code == 400
    assert b"Either url or html_content must be provided" in response.data


def test_screenshot_endpoint_service_exception(client):
    mock_capture_service = Mock()
    mock_capture_service.capture_screenshot.side_effect = ScreenshotServiceException("An unexpected error occurred while capturing.")

    with patch('src.app.capture_service', mock_capture_service):
        response = client.post('/capture', json={
            "url": "https://example.com",
            "format": "png"
        })

    assert response.status_code == 500
    assert response.json['status'] == 'error'
    assert 'An unexpected error occurred while capturing.' in response.json['message']