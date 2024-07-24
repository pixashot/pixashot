# API Reference

The Pixashot service exposes a single endpoint for capturing screenshots.

## Endpoint

- **POST** `/screenshot`

## Request Format

Send a JSON payload to this endpoint with the screenshot options.

Example payload:

```json
{
  "url": "https://example.com",
  "window_width": 1920,
  "window_height": 1080,
  "format": "png",
  "full_page": true,
  "wait_for_timeout": 5000,
  "custom_js": "document.body.style.backgroundColor = 'lightblue';"
}
```

For a complete list of available options, see the [Configuration Options](configuration-options.md) documentation.

## Response

The response type depends on the `response_type` option in the request:

- `"by_format"` (default): Returns the image file directly
- `"empty"`: Returns an empty response (204 No Content)
- `"json"`: Returns a JSON object with a base64-encoded image

## Error Handling

The service uses HTTP status codes to indicate the nature of errors:

- 400: Bad Request (invalid parameters)
- 401: Unauthorized (missing auth token)
- 403: Forbidden (invalid auth token)
- 500: Internal Server Error (unexpected errors during capture)

Detailed error messages and stack traces are provided in the response body for debugging purposes.