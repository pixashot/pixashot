# API Examples

This document provides examples of how to use the Pixashot API for various common scenarios.

## Basic Screenshot

```bash
curl -X POST http://your-service-url/capture \
     -H "Content-Type: application/json" \
     -d '{
           "url": "https://example.com",
           "format": "png"
         }'
```

## Full Page Screenshot with Custom Dimensions

```bash
curl -X POST http://your-service-url/capture \
     -H "Content-Type: application/json" \
     -d '{
           "url": "https://example.com",
           "format": "jpeg",
           "full_page": true,
           "window_width": 1920,
           "window_height": 1080,
           "image_quality": 90
         }'
```

## Capture with Delay

```bash
curl -X POST http://your-service-url/capture \
     -H "Content-Type: application/json" \
     -d '{
           "url": "https://example.com",
           "format": "png",
           "delay_capture": 5000
         }'
```

## Capture PDF with Custom Options

```bash
curl -X POST http://your-service-url/capture \
     -H "Content-Type: application/json" \
     -d '{
           "url": "https://example.com",
           "format": "pdf",
           "pdf_format": "A4",
           "pdf_print_background": true
         }'
```

## Capture with Custom JavaScript

```bash
curl -X POST http://your-service-url/capture \
     -H "Content-Type: application/json" \
     -d '{
           "url": "https://example.com",
           "format": "png",
           "custom_js": "document.body.style.backgroundColor = 'red';"
         }'
```

## Capture with Geolocation Spoofing

```bash
curl -X POST http://your-service-url/capture \
     -H "Content-Type: application/json" \
     -d '{
           "url": "https://example.com",
           "format": "png",
           "geolocation": {
             "latitude": 37.7749,
             "longitude": -122.4194,
             "accuracy": 100
           }
         }'
```

## Capture HTML Content

```bash
curl -X POST http://your-service-url/capture \
     -H "Content-Type: application/json" \
     -d '{
           "html_content": "<html><body><h1>Hello, World!</h1></body></html>",
           "format": "png"
         }'
```

## Capture with Interactions

```bash
curl -X POST http://your-service-url/capture \
     -H "Content-Type: application/json" \
     -d '{
           "url": "https://example.com/form",
           "format": "png",
           "interactions": [
             {
               "action": "type",
               "selector": "#username",
               "text": "johndoe"
             },
             {
               "action": "type",
               "selector": "#password",
               "text": "secretpassword"
             },
             {
               "action": "click",
               "selector": "#login-button"
             },
             {
               "action": "wait_for",
               "wait_for": {
                 "type": "network_idle",
                 "value": 5000
               }
             }
           ]
         }'
```

This example demonstrates how to fill out a login form and wait for the page to load before capturing the screenshot. For more details on interaction options, see the [Interactions documentation](interactions.md).

Remember to replace `http://your-service-url` with the actual URL of your deployed Pixashot service.