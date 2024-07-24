from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field


class ScreenshotRequest(BaseModel):
    url: Optional[HttpUrl] = Field(None, description="URL of the site to take a screenshot of")
    html_content: Optional[str] = Field(None, description="HTML content to render and capture")
    window_width: Optional[int] = Field(1280, description="The width of the browser viewport (pixels)")
    window_height: Optional[int] = Field(720, description="The height of the browser viewport (pixels)")

    # Format options
    format: Optional[str] = Field("png", description="Response format: png, jpeg, webp")
    response_type: Optional[str] = Field("by_format", description="Response type: by_format, empty, json")

    # Selector and viewport options
    selector: Optional[str] = Field(None, description="CSS-like selector of the element to take a screenshot of")

    # Custom JavaScript injection
    custom_js: Optional[str] = Field(None,
                                     description="Custom JavaScript to inject and execute before taking the screenshot")

    # Extension options
    use_popup_blocker: Optional[bool] = Field(True, description="Use the popup blocker extension")
    use_cookie_blocker: Optional[bool] = Field(True, description="Use the cookie consent blocker extension")

    # Image options
    image_quality: Optional[int] = Field(80, description="Image quality (0-100)")
    pixel_density: Optional[float] = Field(2.0, description="Device scale factor (DPR)")

    # Wait options
    wait_for_timeout: Optional[int] = Field(5000, description="Timeout in milliseconds to wait for page load")
    wait_for_selector: Optional[str] = Field(None, description="Wait for a specific selector to appear in DOM")

    # Proxy options
    proxy_server: Optional[str] = Field(None, description="Proxy server address")
    proxy_port: Optional[int] = Field(None, description="Proxy server port")
    proxy_username: Optional[str] = Field(None, description="Proxy server username")
    proxy_password: Optional[str] = Field(None, description="Proxy server password")

    # Error options
    ignore_https_errors: Optional[bool] = Field(True, description="Ignore HTTPS errors during navigation")

    # Additional options that could be easily implemented
    full_page: Optional[bool] = Field(False, description="Take a screenshot of the full page")
    omit_background: Optional[bool] = Field(False, description="Render a transparent background for the image")
