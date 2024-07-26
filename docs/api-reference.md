# Pixashot API Reference

## Endpoint

- **POST** `/capture`

## Authentication

All requests to the Pixashot API must include an `Authorization` header with a valid token.

```
Authorization: Bearer YOUR_AUTH_TOKEN
```

## Request Format

Send a JSON payload to the `/capture` endpoint with the screenshot options.

### Example Payload

```json
{
  "url": "https://example.com",
  "window_width": 1920,
  "window_height": 1080,
  "format": "png",
  "full_page": true,
  "wait_for_timeout": 5000,
  "custom_js": "document.body.style.backgroundColor = 'lightblue';",
  "use_random_user_agent": true
}
```

## Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| url | string (HttpUrl) | - | URL of the site to capture (required if html_content is not provided) |
| html_content | string | - | HTML content to render and capture (required if url is not provided) |
| window_width | integer | 1920 | Width of the browser viewport in pixels |
| window_height | integer | 1080 | Height of the browser viewport in pixels |
| full_page | boolean | false | Capture the full scrollable page |
| selector | string | - | CSS selector of a specific element to capture |
| format | string | "png" | Output format: "png", "jpeg", "webp", "pdf", or "html" |
| response_type | string | "by_format" | Response type: "by_format", "empty", or "json" |
| image_quality | integer (0-100) | 90 | Image quality for JPEG and WebP formats |
| pixel_density | float | 1.0 | Device scale factor (DPR) for the screenshot |
| omit_background | boolean | false | Make the screenshot transparent where possible |
| dark_mode | boolean | false | Enable dark mode for the screenshot |
| wait_for_timeout | integer | 30000 | Time in milliseconds to wait after initial page load |
| wait_for_selector | string | - | Wait for a specific CSS selector to appear in the DOM before capturing |
| delay_capture | integer | 0 | Delay in milliseconds before taking the screenshot after page preparation |
| custom_js | string | - | Custom JavaScript to inject and execute before taking the screenshot |
| use_popup_blocker | boolean | true | Use the built-in popup blocker extension |
| use_cookie_blocker | boolean | true | Use the built-in cookie consent blocker extension |
| ignore_https_errors | boolean | true | Ignore HTTPS errors during navigation |
| block_media | boolean | false | Block images, video, and audio from loading |
| proxy_server | string | - | Proxy server address |
| proxy_port | integer (1-65535) | - | Proxy server port |
| proxy_username | string | - | Username for proxy authentication |
| proxy_password | string | - | Password for proxy authentication |
| geolocation | object | - | Geolocation to spoof: `{"latitude": float, "longitude": float, "accuracy": float}` |
| use_random_user_agent | boolean | false | Use a random user agent |
| user_agent_device | string | - | Device type for user agent generation: "desktop" or "mobile" |
| user_agent_platform | string | - | Platform for user agent generation: "windows", "macos", "ios", "linux", or "android" |
| user_agent_browser | string | "chrome" | Browser for user agent generation: "chrome", "edge", "firefox", or "safari" |
| custom_headers | object | - | Custom headers to be sent with the request |

### PDF-specific Options

The following options are only applicable when `format` is set to "pdf":

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| pdf_print_background | boolean | true | Print background graphics in the PDF |
| pdf_scale | float | 1.0 | Scale of the webpage rendering |
| pdf_page_ranges | string | - | Paper ranges to print, e.g., '1-5, 8, 11-13' |
| pdf_format | string | "A4" | Paper format: "A4", "Letter", or "Legal" |
| pdf_width | string | - | Paper width, accepts values labeled with units (e.g., '8.5in') |
| pdf_height | string | - | Paper height, accepts values labeled with units (e.g., '11in') |

### Interaction Steps

You can define a series of interactions to be performed before capturing the screenshot using the `interactions` parameter. Each interaction step is an object with the following properties:

| Property | Type | Description |
|----------|------|-------------|
| action | string | The type of action: "click", "type", "hover", "scroll", or "wait_for" |
| selector | string | CSS selector for the element to interact with (for "click", "type", and "hover" actions) |
| text | string | Text to type (for "type" action) |
| x | integer | Horizontal scroll position (for "scroll" action) |
| y | integer | Vertical scroll position (for "scroll" action) |
| wait_for | object | Specifies what to wait for (for "wait_for" action) |

The `wait_for` object has the following properties:

| Property | Type | Description |
|----------|------|-------------|
| type | string | Type of wait: "network_idle", "network_mostly_idle", "selector", or "timeout" |
| value | string or integer | Selector string for "selector", milliseconds for others |

Example of interaction steps:

```json
"interactions": [
  {"action": "click", "selector": "#accept-cookies"},
  {"action": "type", "selector": "#search-input", "text": "example search"},
  {"action": "click", "selector": "#search-button"},
  {"action": "wait_for", "wait_for": {"type": "network_idle", "value": 5000}},
  {"action": "scroll", "x": 0, "y": 500}
]
```

## Response

The response type depends on the `response_type` parameter in the request:

- `"by_format"` (default): Returns the image file directly with the appropriate MIME type.
- `"empty"`: Returns an empty response (204 No Content).
- `"json"`: Returns a JSON object with a base64-encoded image or HTML content.

### JSON Response Format

When `response_type` is set to "json", the response will have the following structure:

```json
{
  "file": "base64_encoded_content",
  "format": "png"
}
```

## Error Handling

The service uses HTTP status codes to indicate the nature of errors:

- 400: Bad Request (invalid parameters)
- 401: Unauthorized (missing auth token)
- 403: Forbidden (invalid auth token)
- 429: Too Many Requests (rate limit exceeded)
- 500: Internal Server Error (unexpected errors during capture)

Error responses will have the following JSON structure:

```json
{
  "status": "error",
  "message": "Detailed error message",
  "errorType": "ErrorClassName"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. The current rate limit is defined by the `RATE_LIMIT_CAPTURE` environment variable. If you exceed the rate limit, you'll receive a 429 Too Many Requests response.

## Examples

### Capture a Full Page Screenshot

```bash
curl -X POST https://api.pixashot.com/capture \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "format": "png",
    "full_page": true,
    "window_width": 1920,
    "window_height": 1080
  }'
```

### Capture a PDF with Custom Options

```bash
curl -X POST https://api.pixashot.com/capture \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "format": "pdf",
    "pdf_format": "A4",
    "pdf_print_background": true,
    "pdf_scale": 0.8
  }'
```

### Capture with Custom JavaScript and Geolocation

```bash
curl -X POST https://api.pixashot.com/capture \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "format": "png",
    "custom_js": "document.body.style.backgroundColor = 'lightblue';",
    "geolocation": {
      "latitude": 37.7749,
      "longitude": -122.4194,
      "accuracy": 100
    }
  }'
```

### Capture with Random User Agent

```bash
curl -X POST https://api.pixashot.com/capture \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "format": "png",
    "use_random_user_agent": true,
    "user_agent_device": "desktop",
    "user_agent_platform": "windows",
    "user_agent_browser": "chrome"
  }'
```

This request will include randomly generated headers, such as:

- `user-agent`: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.94 Safari/537.36
- `sec-ch-ua`: "Not A(Brand";v="99", "Chromium";v="122", "Google Chrome";v="122"
- `sec-ch-ua-mobile`: ?0
- `sec-ch-ua-platform`: "Windows"

Note: The actual values will vary based on the randomly generated user agent.

For more examples and detailed information on using the Pixashot API, please refer to the [API Examples](api-examples.md) documentation.