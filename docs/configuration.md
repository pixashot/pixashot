# Configuration Options

Pixashot provides a comprehensive set of configuration options to customize the screenshot capture process. These options are defined in the `CaptureRequest` class located in `src/capture_request.py`.

## Basic Options

- `url` (HttpUrl, optional): URL of the site to capture.
- `html_content` (str, optional): HTML content to render and capture instead of a URL.

## Viewport and Screenshot Options

- `window_width` (int, default: 1280): Width of the browser viewport in pixels.
- `window_height` (int, default: 720): Height of the browser viewport in pixels.
- `full_page` (bool, default: False): Capture the full scrollable page instead of just the viewport.
- `selector` (str, optional): CSS selector of a specific element to capture.

## Format and Response Options

- `format` (str, default: "png"): Output format. Options: "png", "jpeg", "webp", "pdf", "html".
- `response_type` (str, default: "by_format"): Type of response to return. Options: "by_format" (image file), "empty" (no content), "json" (base64 encoded image).

## Image Quality Options

- `image_quality` (int, default: 80): Image quality for JPEG and WebP formats. Range: 0-100.
- `pixel_density` (float, default: 2.0): Device scale factor (DPR) for the screenshot.
- `omit_background` (bool, default: False): Make the screenshot transparent where possible.
- `dark_mode` (bool, default: False): Enable dark mode for the screenshot.

## Wait and Delay Options

- `wait_for_timeout` (int, default: 5000): Time in milliseconds to wait after initial page load.
- `wait_for_selector` (str, optional): Wait for a specific CSS selector to appear in the DOM before capturing.
- `delay_capture` (int, default: 0): Delay in milliseconds before taking the screenshot after page preparation.

## JavaScript and Extension Options

- `custom_js` (str, optional): Custom JavaScript to inject and execute before taking the screenshot.
- `use_popup_blocker` (bool, default: True): Use the built-in popup blocker extension.
- `use_cookie_blocker` (bool, default: True): Use the built-in cookie consent blocker extension.

## Network and Resource Options

- `ignore_https_errors` (bool, default: True): Ignore HTTPS errors during navigation.
- `block_media` (bool, default: False): Block images, video, and audio from loading.

## Proxy Configuration

Proxy settings can be configured in two ways:

1. **Per-request configuration:**
   - `proxy_server` (str, optional): Proxy server address.
   - `proxy_port` (int, optional): Proxy server port.
   - `proxy_username` (str, optional): Username for proxy authentication.
   - `proxy_password` (str, optional): Password for proxy authentication.

2. **Environment variables:**
   You can set default proxy settings using the following environment variables:
   - `PROXY_SERVER`: Default proxy server address.
   - `PROXY_PORT`: Default proxy server port.
   - `PROXY_USERNAME`: Default username for proxy authentication.
   - `PROXY_PASSWORD`: Default password for proxy authentication.

   These environment variables will be used as defaults if the corresponding options are not provided in the request.

## Geolocation Options

- `geolocation` (dict, optional): Geolocation to spoof. Format: `{"latitude": float, "longitude": float, "accuracy": float}`.

## PDF-specific Options

When capturing PDF content (`format: "pdf"`), the following options are available:

- `pdf_print_background` (bool, default: True): Print background graphics in the PDF.
- `pdf_scale` (float, optional): Scale of the webpage rendering.
- `pdf_page_ranges` (str, optional): Paper ranges to print, e.g., '1-5, 8, 11-13'.
- `pdf_format` (str, optional): Paper format, e.g., 'A4', 'Letter'.
- `pdf_width` (str, optional): Paper width, accepts values labeled with units (e.g., '8.5in').
- `pdf_height` (str, optional): Paper height, accepts values labeled with units (e.g., '11in').

## HTML-specific Options

When capturing HTML content (`format: "html"`), the following options are available:

- `html_wait_for_selector` (str, optional): Wait for a specific selector to appear before capturing the HTML.
- `html_wait_for_timeout` (int, default: 5000): Time in milliseconds to wait before capturing the HTML.
- `html_include_resources` (bool, default: False): Include all page resources (CSS, images) in the captured HTML.

For advanced features and usage examples, please refer to the [Advanced Features](advanced.md) and [API Examples](api-examples.md) documentation.