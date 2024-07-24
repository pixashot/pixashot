# Configuration Options

Pixashot offers a wide range of configuration options to customize the screenshot capture process. These options are defined in the `ScreenshotRequest` class in `src/screenshot_request.py`.

## Basic Options

- `url` (HttpUrl, required): The URL of the webpage to capture.
- `window_width` (int, optional, default: 1280): Width of the browser viewport in pixels.
- `window_height` (int, optional, default: 720): Height of the browser viewport in pixels.
- `format` (str, optional, default: "png"): Image format for the screenshot. Options: "png", "jpeg", "webp".
- `response_type` (str, optional, default: "by_format"): Type of response to return. Options: "by_format" (image file), "empty" (no content), "json" (base64 encoded image).

## Capture Options

- `selector` (str, optional): CSS selector of a specific element to capture. If provided, only this element will be captured.
- `capture_beyond_viewport` (bool, optional): Whether to capture content beyond the initial viewport.
- `full_page` (bool, optional, default: True): Capture the full scrollable page instead of just the viewport.
- `omit_background` (bool, optional, default: False): Make the screenshot transparent where possible.

## Wait Options

- `wait_for_timeout` (int, optional, default: 5000): Time in milliseconds to wait for the page to load before capturing.
- `wait_for_selector` (str, optional): Wait for a specific CSS selector to appear in the DOM before capturing.

## Scroll Options

- `scroll_to_bottom` (bool, optional, default: True): Scroll to the bottom of the page before capturing to ensure all dynamic content is loaded.
- `max_scrolls` (int, optional, default: 10): Maximum number of scroll attempts when scrolling to the bottom.
- `scroll_timeout` (int, optional, default: 30): Timeout in seconds for the entire scrolling operation.

## Image Quality Options

- `image_quality` (int, optional, default: 80): Image quality for formats that support it (JPEG, WebP). Range: 0-100.
- `pixel_density` (float, optional, default: 2.0): Device scale factor (DPR) for the screenshot.

For advanced options and features, please refer to the [Advanced Features](advanced.md) documentation.