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
    assert str(request.url) == "https://example.com/"
    assert request.window_width == 1280
    assert request.window_height == 720
    assert request.format == "png"
    assert request.full_page == True


def test_capture_request_default_values():
    request = CaptureRequest(url="https://example.com")
    assert request.window_width == 1920
    assert request.window_height == 1080
    assert request.format == "png"
    assert request.full_page == False
    assert request.image_quality == 90
    assert request.pixel_density == 1.0


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


def test_invalid_window_dimensions():
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", window_width=-1)
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", window_height=0)


def test_invalid_image_quality():
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", image_quality=101)
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", image_quality=-1)


def test_invalid_pixel_density():
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", pixel_density=0)
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", pixel_density=-1.5)


def test_invalid_wait_for_timeout():
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", wait_for_timeout=-1)


def test_invalid_proxy_port():
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", proxy_server="proxy.example.com", proxy_port=70000)


def test_invalid_geolocation():
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", geolocation={"latitude": 91, "longitude": 0, "accuracy": 100})
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", geolocation={"latitude": 0, "longitude": 181, "accuracy": 100})
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", geolocation={"latitude": 0, "longitude": 0, "accuracy": -1})


def test_invalid_pdf_scale():
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", format="pdf", pdf_scale=0)
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", format="pdf", pdf_scale=-1.5)


def test_invalid_response_type():
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", response_type="invalid_type")


def test_invalid_combination():
    with pytest.raises(ValidationError):
        CaptureRequest(html_content="<html></html>", url="https://example.com")  # Can't have both HTML content and URL


def test_missing_required_fields():
    with pytest.raises(ValidationError):
        CaptureRequest()  # Neither URL nor HTML content provided


def test_invalid_custom_js():
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", custom_js=123)  # custom_js should be a string


def test_invalid_wait_for_selector():
    with pytest.raises(ValidationError):
        CaptureRequest(url="https://example.com", wait_for_selector=123)  # wait_for_selector should be a string
