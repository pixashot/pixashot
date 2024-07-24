from typing import Optional, Dict
from pydantic import BaseModel, HttpUrl, Field


class CaptureRequest(BaseModel):
    # Basic options
    url: Optional[HttpUrl] = Field(None, description="URL of the site to take a screenshot of")
    html_content: Optional[str] = Field(None, description="HTML content to render and capture")

    # Viewport and screenshot options
    window_width: Optional[int] = Field(1280, description="The width of the browser viewport (pixels)")
    window_height: Optional[int] = Field(720, description="The height of the browser viewport (pixels)")
    full_page: Optional[bool] = Field(False, description="Take a screenshot of the full page")
    selector: Optional[str] = Field(None, description="CSS-like selector of the element to take a screenshot of")

    # Format and response options
    format: Optional[str] = Field("png", description="Response format: png, jpeg, webp, pdf, html")
    response_type: Optional[str] = Field("by_format", description="Response type: by_format, empty, json")

    # Image options
    image_quality: Optional[int] = Field(80, description="Image quality (0-100)")
    pixel_density: Optional[float] = Field(2.0, description="Device scale factor (DPR)")
    omit_background: Optional[bool] = Field(False, description="Render a transparent background for the image")
    dark_mode: Optional[bool] = Field(False, description="Enable dark mode for the screenshot")

    # Wait and timeout options
    wait_for_timeout: Optional[int] = Field(5000, description="Timeout in milliseconds to wait for page load")
    wait_for_selector: Optional[str] = Field(None, description="Wait for a specific selector to appear in DOM")

    # JavaScript and extension options
    custom_js: Optional[str] = Field(None, description="Custom JavaScript to inject and execute before taking the screenshot")
    use_popup_blocker: Optional[bool] = Field(True, description="Use the popup blocker extension")
    use_cookie_blocker: Optional[bool] = Field(True, description="Use the cookie consent blocker extension")

    # Network and resource options
    ignore_https_errors: Optional[bool] = Field(True, description="Ignore HTTPS errors during navigation")
    block_media: Optional[bool] = Field(False, description="Block images, video, and audio from loading")

    # Proxy options
    proxy_server: Optional[str] = Field(None, description="Proxy server address")
    proxy_port: Optional[int] = Field(None, description="Proxy server port")
    proxy_username: Optional[str] = Field(None, description="Proxy server username")
    proxy_password: Optional[str] = Field(None, description="Proxy server password")

    # Geolocation options
    geolocation: Optional[Dict[str, float]] = Field(None, description="Geolocation to spoof (latitude, longitude, accuracy)")

    # PDF-specific options
    pdf_print_background: Optional[bool] = Field(True, description="Print background graphics in PDF")
    pdf_scale: Optional[float] = Field(1.0, description="Scale of the webpage rendering")
    pdf_page_ranges: Optional[str] = Field(None, description="Paper ranges to print, e.g., '1-5, 8, 11-13'")
    pdf_format: Optional[str] = Field(None, description="Paper format, e.g., 'A4', 'Letter'")
    pdf_width: Optional[str] = Field(None, description="Paper width, accepts values labeled with units")
    pdf_height: Optional[str] = Field(None, description="Paper height, accepts values labeled with units")