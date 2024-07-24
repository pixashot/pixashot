import pytest
from pydantic import ValidationError
from src.capture_request import CaptureRequest

def test_capture_request_valid():
    data = {
        "url": "https://example.com",
        "window_width": 1280,
        "window_height": 720,
        "format": "png",
        "full_page": True
    }
    request = CaptureRequest(**data)
    assert request.url == "https://example.com"
    assert request.window_width == 1280
    assert request.window_height == 720
    assert request.format == "png"
    assert request.full_page == True

def test_capture_request_default_values():
    request = CaptureRequest(url="https://example.com")
    assert request.window_width == 1280
    assert request.window_height == 720
    assert request.format == "png"
    assert request.full_page == False
    assert request.image_quality == 80
    assert request.pixel_density == 2.0

def test_capture_request_invalid_url():
    with pytest.raises(ValidationError):
        CaptureRequest(url="not_a_valid_url")

def test_capture_request_invalid_format():
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", format="invalid_format")

def test_capture_request_html_content():
    html = "<html><body><h1>Test</h1></body></html>"
    request = CaptureRequest(html_content=html)
    assert request.html_content == html
    assert request.url is None

def test_capture_request_geolocation():
    geo = {"latitude": 37.7749, "longitude": -122.4194, "accuracy": 100}
    request = CaptureRequest(url="https://example.com", geolocation=geo)
    assert request.geolocation == geo

def test_capture_request_pdf_options():
    request = CaptureRequest(
        url="https://example.com",
        format="pdf",
        pdf_print_background=False,
        pdf_scale=1.5,
        pdf_page_ranges="1-3",
        pdf_format="A4"
    )
    assert request.format == "pdf"
    assert request.pdf_print_background == False
    assert request.pdf_scale == 1.5
    assert request.pdf_page_ranges == "1-3"
    assert request.pdf_format == "A4"