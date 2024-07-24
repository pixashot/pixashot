# Screenshot Capture Service

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [Project Structure](#project-structure)
4. [Requirements](#requirements)
5. [Installation](#installation)
6. [Usage](#usage)
7. [API Endpoint](#api-endpoint)
8. [Configuration Options](#configuration-options)
9. [Custom JavaScript Injection](#custom-javascript-injection)
10. [Browser Extensions](#browser-extensions)
11. [Error Handling](#error-handling)
12. [Docker Support](#docker-support)
13. [Security Considerations](#security-considerations)
14. [Contributing](#contributing)
15. [License](#license)

## Introduction

The Screenshot Capture Service is a robust, Flask-based web application that allows users to capture high-quality screenshots of web pages. It utilizes Playwright for browser automation and offers a wide range of customization options to cater to various screenshot requirements.

## Features

- Capture full-page or viewport-specific screenshots
- Support for multiple image formats (PNG, JPEG, WebP)
- Custom viewport size configuration
- Ability to wait for specific page elements
- Custom JavaScript injection before capture
- Built-in popup and cookie consent blockers
- Proxy support for accessing restricted content
- Scroll-to-bottom functionality for dynamic content
- Configurable image quality and pixel density
- Docker support for easy deployment

## Project Structure

```
.
├── context_creator.py
├── requirements.txt
├── js
│   ├── page-utils.js
│   └── dynamic-content-detector.js
├── Dockerfile
├── screenshot_request.py
├── browser_controller.py
├── app.py
└── screenshot_capture_service.py
```

- `app.py`: Main Flask application entry point
- `screenshot_capture_service.py`: Core screenshot capture logic
- `browser_controller.py`: Manages browser interactions and page preparation
- `context_creator.py`: Sets up the browser context with specified options
- `screenshot_request.py`: Defines the schema for screenshot requests
- `js/`: Contains JavaScript utilities for page manipulation
- `Dockerfile`: Configures the Docker environment for the application

## Requirements

- Python 3.7+
- Flask
- Playwright
- Pillow
- Pydantic

See `requirements.txt` for a complete list of dependencies.

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd screenshot-capture-service
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```
   playwright install
   ```

## Usage

To start the Flask server:

```
python app.py
```

By default, the server will run on `http://localhost:8080`. You can change the port by setting the `PORT` environment variable.

## API Endpoint

The service exposes a single endpoint:

- **POST** `/screenshot`

Send a JSON payload to this endpoint with the screenshot options. See [Configuration Options](#configuration-options) for available parameters.

## Configuration Options

The `ScreenshotRequest` class in `screenshot_request.py` defines all available options for customizing the screenshot capture process. Below is a comprehensive list of configuration parameters:

### Basic Options
- `url` (HttpUrl, required): The URL of the webpage to capture.
- `windowWidth` (int, optional, default: 1280): Width of the browser viewport in pixels.
- `windowHeight` (int, optional, default: 720): Height of the browser viewport in pixels.
- `format` (str, optional, default: "png"): Image format for the screenshot. Options: "png", "jpeg", "webp".
- `response_type` (str, optional, default: "by_format"): Type of response to return. Options: "by_format" (image file), "empty" (no content), "json" (base64 encoded image).

### Capture Options
- `selector` (str, optional): CSS selector of a specific element to capture. If provided, only this element will be captured.
- `capture_beyond_viewport` (bool, optional): Whether to capture content beyond the initial viewport.
- `full_page` (bool, optional, default: True): Capture the full scrollable page instead of just the viewport.
- `omit_background` (bool, optional, default: False): Make the screenshot transparent where possible.

### Wait Options
- `wait_for_timeout` (int, optional, default: 5000): Time in milliseconds to wait for the page to load before capturing.
- `wait_for_selector` (str, optional): Wait for a specific CSS selector to appear in the DOM before capturing.

### Scroll Options
- `scroll_to_bottom` (bool, optional, default: True): Scroll to the bottom of the page before capturing to ensure all dynamic content is loaded.
- `max_scrolls` (int, optional, default: 10): Maximum number of scroll attempts when scrolling to the bottom.
- `scroll_timeout` (int, optional, default: 30): Timeout in seconds for the entire scrolling operation.

### Image Quality Options
- `image_quality` (int, optional, default: 80): Image quality for formats that support it (JPEG, WebP). Range: 0-100.
- `pixel_density` (float, optional, default: 2.0): Device scale factor (DPR) for the screenshot.

### Custom Behavior
- `custom_js` (str, optional): Custom JavaScript to inject and execute before taking the screenshot.

### Browser Extensions
- `use_popup_blocker` (bool, optional, default: True): Use the built-in popup blocker extension.
- `use_cookie_blocker` (bool, optional, default: True): Use the built-in cookie consent blocker extension.

### Proxy Configuration
- `proxy_server` (str, optional): Proxy server address.
- `proxy_port` (int, optional): Proxy server port.
- `proxy_username` (str, optional): Username for proxy authentication.
- `proxy_password` (str, optional): Password for proxy authentication.

### Error Handling
- `ignore_https_errors` (bool, optional, default: True): Ignore HTTPS errors during navigation.

### Timeout
- `timeout` (int, optional, default: 30000): Timeout in milliseconds for the entire screenshot capture operation.

To use these options, include them in the JSON payload when making a POST request to the `/screenshot` endpoint. For example:

```json
{
  "url": "https://example.com",
  "windowWidth": 1920,
  "windowHeight": 1080,
  "format": "jpeg",
  "full_page": true,
  "wait_for_timeout": 10000,
  "custom_js": "document.body.style.backgroundColor = 'lightblue';",
  "image_quality": 90,
  "use_popup_blocker": true,
  "proxy_server": "proxy.example.com",
  "proxy_port": 8080
}
```

This configuration will capture a full-page JPEG screenshot of example.com with a 1920x1080 viewport, wait up to 10 seconds for the page to load, change the background color to light blue, set the image quality to 90%, use the popup blocker, and route the request through a proxy server.

## Custom JavaScript Injection

You can inject custom JavaScript to be executed before the screenshot is taken. This allows for manipulating the page content or style. For example:

```json
{
  "url": "https://example.com",
  "custom_js": "document.body.style.backgroundColor = 'red';"
}
```

## Browser Extensions

The service includes two built-in browser extensions:

1. Popup Blocker: Prevents annoying popups from interfering with the screenshot
2. Cookie Consent Blocker: Automatically handles cookie consent prompts

These can be enabled or disabled using the `use_popup_blocker` and `use_cookie_blocker` options.

## Error Handling

The service provides detailed error messages and stack traces in case of failures. HTTP status codes are used to indicate the nature of errors:

- 400: Bad Request (invalid parameters)
- 401: Unauthorized (missing auth token)
- 403: Forbidden (invalid auth token)
- 500: Internal Server Error (unexpected errors during capture)

## Docker Support

To build and run the service using Docker:

1. Build the Docker image:
   ```
   docker build -t screenshot-service .
   ```

2. Run the container:
   ```
   docker run -p 8080:8080 screenshot-service
   ```

The service will be available at `http://localhost:8080`.

## Security Considerations

- The service includes optional token-based authentication. Set the `AUTH_TOKEN` environment variable to enable it.
- Be cautious when allowing custom JavaScript injection, as it can potentially expose sensitive information.
- When deploying, ensure proper firewall rules and access controls are in place.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Browser Extensions

The service includes support for two third-party Chrome extensions:

1. Popup Blocker: Prevents annoying popups from interfering with the screenshot
2. Cookie Consent Blocker: Automatically handles cookie consent prompts

These extensions are located in the `/extensions` directory and are not part of this project's source code. They are third-party Chrome extensions that have been included to enhance the functionality of the screenshot service.

These can be enabled or disabled using the `use_popup_blocker` and `use_cookie_blocker` options in the screenshot request.

Please note:
- The inclusion of these third-party extensions is subject to their respective licenses and terms of use.
- Users should review and comply with the licensing terms of these extensions before using them in their deployments.
- The maintainers of this project are not responsible for the functionality or security of these third-party extensions.

If you prefer not to use these extensions or want to use different ones, you can modify the `context_creator.py` file to change the extension paths or remove them entirely.

## License

This project is licensed under the MIT License. Please note that while the project's code is licensed under MIT, the third-party Chrome extensions located in the `/extensions` directory are subject to their own respective licenses. Users should review and comply with the licensing terms of these extensions separately.

```
MIT License

Copyright (c) 2024 Greg Priday

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```