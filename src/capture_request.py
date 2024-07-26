from typing import Optional, Literal, Dict, Union, List
from pydantic import BaseModel, HttpUrl, Field, PositiveInt, PositiveFloat, conint, confloat, model_validator


class Geolocation(BaseModel):
    latitude: confloat(ge=-90, le=90)
    longitude: confloat(ge=-180, le=180)
    accuracy: PositiveFloat

    def __eq__(self, other):
        if isinstance(other, dict):
            return (self.latitude == other['latitude'] and
                    self.longitude == other['longitude'] and
                    self.accuracy == other['accuracy'])
        return super().__eq__(other)


class WaitForOption(BaseModel):
    type: Literal["network_idle", "network_mostly_idle", "selector", "timeout"]
    value: Union[str, int] = Field(..., description="Selector string for 'selector', milliseconds for others")


class InteractionStep(BaseModel):
    action: Literal["click", "type", "hover", "scroll", "wait_for"]
    selector: Optional[str] = None
    text: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    wait_for: Optional[WaitForOption] = Field(None, description="Specifies what to wait for")


def validate_url_or_html_content(v):
    if not v.get('url') and not v.get('html_content'):
        raise ValueError('Either url or html_content must be provided')
    if v.get('url') and v.get('html_content'):
        raise ValueError('Cannot provide both url and html_content')
    return v


class CaptureRequest(BaseModel):
    # Basic options
    url: Optional[HttpUrl] = Field(None, description="URL of the site to take a screenshot of")
    html_content: Optional[str] = Field(None, description="HTML content to render and capture")

    # Viewport and screenshot options
    window_width: PositiveInt = Field(1920, description="The width of the browser viewport (pixels)")
    window_height: PositiveInt = Field(1080, description="The height of the browser viewport (pixels)")
    full_page: Optional[bool] = Field(False, description="Take a screenshot of the full page (scrolled to the bottom)")
    selector: Optional[str] = Field(None, description="CSS-like selector of the element to take a screenshot of")

    # Format and response options
    format: Optional[Literal["png", "jpeg", "webp", "pdf", "html"]] = Field("png",
                                                                            description="Response format: png, jpeg, webp, pdf, html")
    response_type: Optional[Literal["by_format", "empty", "json"]] = Field("by_format",
                                                                           description="Response type: by_format, empty, json")

    # Interactions
    interactions: Optional[List[InteractionStep]] = Field(None,
                                                          description="List of interaction steps to perform before capturing")
    wait_for_animation: Optional[bool] = Field(False, description="Wait for animations to complete before capturing")

    # Image options
    image_quality: Optional[conint(ge=0, le=100)] = Field(90, description="Image quality (0-100)")
    pixel_density: Optional[PositiveFloat] = Field(1.0, description="Device scale factor (DPR)")
    omit_background: Optional[bool] = Field(False, description="Render a transparent background for the image")
    dark_mode: Optional[bool] = Field(False, description="Enable dark mode for the screenshot")

    # Wait and timeout options
    wait_for_timeout: Optional[PositiveInt] = Field(30000, description="Timeout in milliseconds to wait for page load")
    wait_for_selector: Optional[str] = Field(None, description="Wait for a specific selector to appear in DOM")
    delay_capture: Optional[PositiveInt] = Field(0, description="Delay in milliseconds before taking the screenshot")
    wait_for_network: Literal["idle", "mostly_idle"] = Field(
        "idle",
        description="Specify whether to wait for the network to be mostly idle or completely idle"
    )

    # JavaScript and extension options
    custom_js: Optional[str] = Field(None,
                                     description="Custom JavaScript to inject and execute before taking the screenshot")
    use_popup_blocker: Optional[bool] = Field(True, description="Use the popup blocker extension")
    use_cookie_blocker: Optional[bool] = Field(True, description="Use the cookie consent blocker extension")

    # Network and resource options
    ignore_https_errors: Optional[bool] = Field(True, description="Ignore HTTPS errors during navigation")
    block_media: Optional[bool] = Field(False, description="Block images, video, and audio from loading")
    custom_headers: Optional[Dict[str, str]] = Field(None, description="Custom headers to be sent with the request")

    # Proxy options
    proxy_server: Optional[str] = Field(None, description="Proxy server address")
    proxy_port: Optional[conint(ge=1, le=65535)] = Field(None, description="Proxy server port")
    proxy_username: Optional[str] = Field(None, description="Proxy server username")
    proxy_password: Optional[str] = Field(None, description="Proxy server password")

    # Geolocation options
    geolocation: Optional[Geolocation] = Field(None, description="Geolocation to spoof (latitude, longitude, accuracy)")

    # PDF-specific options
    pdf_print_background: Optional[bool] = Field(True, description="Print background graphics in PDF")
    pdf_scale: Optional[PositiveFloat] = Field(1.0, description="Scale of the webpage rendering")
    pdf_page_ranges: Optional[str] = Field(None, description="Paper ranges to print, e.g., '1-5, 8, 11-13'")
    pdf_format: Optional[Literal["A4", "Letter", "Legal"]] = Field("A4",
                                                                   description="Paper format, e.g., 'A4', 'Letter'")
    pdf_width: Optional[str] = Field(None, description="Paper width, accepts values labeled with units")
    pdf_height: Optional[str] = Field(None, description="Paper height, accepts values labeled with units")

    @model_validator(mode='before')
    def validate_url_or_html_content(cls, values):
        return validate_url_or_html_content(values)

    @model_validator(mode='after')
    def check_pdf_options(self) -> 'CaptureRequest':
        if self.format != 'pdf':
            pdf_fields = ['pdf_print_background', 'pdf_scale', 'pdf_page_ranges', 'pdf_format', 'pdf_width',
                          'pdf_height']
            for field in pdf_fields:
                if getattr(self, field) is not None:
                    setattr(self, field, None)
        return self

    @model_validator(mode='after')
    def validate_custom_headers(self) -> 'CaptureRequest':
        if self.custom_headers:
            # Validate that header names are strings and don't contain invalid characters
            for header_name in self.custom_headers.keys():
                if not isinstance(header_name, str) or ':' in header_name:
                    raise ValueError(f"Invalid header name: {header_name}")
        return self

    @model_validator(mode='after')
    def validate_interaction_steps(self) -> 'CaptureRequest':
        if self.interactions:
            for step in self.interactions:
                if step.action == "wait_for":
                    if not step.wait_for:
                        raise ValueError("wait_for action requires a wait_for option")
                    if step.wait_for.type in ["network_idle", "network_mostly_idle", "timeout"]:
                        if not isinstance(step.wait_for.value, int):
                            raise ValueError(f"{step.wait_for.type} requires an integer value for milliseconds")
                    elif step.wait_for.type == "selector":
                        if not isinstance(step.wait_for.value, str):
                            raise ValueError("selector wait_for type requires a string value")
        return self

    model_config = {
        'arbitrary_types_allowed': True
    }
