# Configuration Options

Pixashot offers a wide range of configuration options to customize the screenshot capture process. These options are defined in the `CaptureRequest` class in `src/capture_request.py`.

## Basic Options

- `url` (HttpUrl, optional): The URL of the webpage to capture.
- `html_content` (str, optional): HTML content to render and capture instead of a URL.
- `window_width` (int, optional, default: 1280): Width of the browser viewport in pixels.
- `window_height` (int, optional, default: 720): Height of the browser viewport in pixels.
- `format` (str, optional, default: "png"): Output format for the capture. Options: "png", "jpeg", "webp", "pdf", "html".
- `response_type` (str, optional, default: "by_format"): Type of response to return. Options: "by_format" (image file), "empty" (no content), "json" (base64 encoded image).

## Capture Options

- `selector` (str, optional): CSS selector of a specific element to capture. If provided, only this element will be captured.
- `full_page` (bool, optional, default: False): Capture the full scrollable page instead of just the viewport.
- `omit_background` (bool, optional, default: False): Make the screenshot transparent where possible.

## Wait Options

- `wait_for_timeout` (int, optional, default: 5000): Time in milliseconds to wait for the page to load before capturing.
- `wait_for_selector` (str, optional): Wait for a specific CSS selector to appear in the DOM before capturing.

## Image Quality Options

- `image_quality` (int, optional, default: 80): Image quality for formats that support it (JPEG, WebP). Range: 0-100.
- `pixel_density` (float, optional, default: 2.0): Device scale factor (DPR) for the screenshot.

## Custom JavaScript and Extensions

- `custom_js` (str, optional): Custom JavaScript to inject and execute before taking the screenshot.
- `use_popup_blocker` (bool, optional, default: True): Use the built-in popup blocker extension.
- `use_cookie_blocker` (bool, optional, default: True): Use the built-in cookie consent blocker extension.

## Proxy Configuration

- `proxy_server` (str, optional): Proxy server address.
- `proxy_port` (int, optional): Proxy server port.
- `proxy_username` (str, optional): Username for proxy authentication.
- `proxy_password` (str, optional): Password for proxy authentication.

## Error Handling

- `ignore_https_errors` (bool, optional, default: True): Ignore HTTPS errors during navigation.

## HTML Capture Options

When capturing HTML content (`format: "html"`), the following options are available:

- `html_wait_for_selector` (str, optional): Wait for a specific selector to appear before capturing the HTML.
- `html_wait_for_timeout` (int, optional, default: 5000): Time in milliseconds to wait before capturing the HTML.
- `html_include_resources` (bool, optional, default: False): Include all page resources (CSS, images) in the captured HTML.

## PDF Capture Options

When capturing PDF content (`format: "pdf"`), the following options are available:

- `pdf_print_background` (bool, optional, default: True): Print background graphics in the PDF.
- `pdf_scale` (float, optional, default: 1.0): Scale of the webpage rendering.
- `pdf_page_ranges` (str, optional): Paper ranges to print, e.g., '1-5, 8, 11-13'.
- `pdf_format` (str, optional): Paper format, e.g., 'A4', 'Letter'.
- `pdf_width` (str, optional): Paper width, accepts values labeled with units (e.g., '8.5in').
- `pdf_height` (str, optional): Paper height, accepts values labeled with units (e.g., '11in').

For advanced options and features, please refer to the [Advanced Features](advanced.md) documentation.