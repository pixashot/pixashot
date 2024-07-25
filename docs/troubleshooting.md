# Troubleshooting Guide

This document provides solutions for common issues you might encounter when using Pixashot.

## Connection Errors

### Issue: Unable to connect to the Pixashot service

1. Verify that the service URL is correct.
2. Check if the service is running and accessible from your network.
3. Ensure that any necessary authentication tokens are provided and valid.

## Capture Errors

### Issue: Timeout during capture

1. Increase the `wait_for_timeout` parameter in your request.
2. Check if the target website is slow to load or has dynamic content.
3. Consider using the `wait_for_selector` option to wait for a specific element.

### Issue: Blank or incomplete screenshots

1. Ensure the target website doesn't have anti-bot measures.
2. Try increasing the `window_width` and `window_height`.
3. For full-page screenshots, make sure `full_page` is set to `true`.

## Format-Specific Issues

### Issue: PDF capture not rendering correctly

1. Check if `pdf_print_background` is set correctly for your needs.
2. Adjust `pdf_scale` if the content appears too large or small.
3. Ensure the target website is optimized for print layouts.

### Issue: Low quality images

1. For JPEG and WebP formats, increase the `image_quality` parameter.
2. For all formats, try increasing the `pixel_density` for higher resolution.

## Custom JavaScript Issues

### Issue: Custom JavaScript not executing

1. Verify that your JavaScript code is correctly escaped in the JSON payload.
2. Ensure the code doesn't contain syntax errors.
3. Check if the target website's Content Security Policy (CSP) is blocking script execution.

## Geolocation and Proxy Issues

### Issue: Geolocation spoofing not working

1. Confirm that the `geolocation` object in your request is correctly formatted.
2. Check if the target website has additional measures to detect actual location.

### Issue: Proxy connection failing

1. Verify that the proxy server details (address, port, credentials) are correct.
2. Ensure the proxy server is operational and accessible.