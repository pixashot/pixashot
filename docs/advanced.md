# Advanced Features

## Custom JavaScript Injection

You can inject custom JavaScript to be executed before the screenshot is taken. This allows for manipulating the page content or style.

Example:

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

## Proxy Configuration

You can route requests through a proxy server:

- `proxy_server` (str, optional): Proxy server address.
- `proxy_port` (int, optional): Proxy server port.
- `proxy_username` (str, optional): Username for proxy authentication.
- `proxy_password` (str, optional): Password for proxy authentication.

## Error Handling

- `ignore_https_errors` (bool, optional, default: True): Ignore HTTPS errors during navigation.

## Timeout Configuration

- `timeout` (int, optional, default: 30000): Timeout in milliseconds for the entire screenshot capture operation.

For information on basic configuration options, please refer to the [Configuration Options](configuration.md) documentation.

## Interaction Simulation

Pixashot supports advanced interaction simulation, allowing you to perform actions on the page before capturing the screenshot. This is useful for scenarios where you need to interact with dynamic content, fill forms, or navigate through multiple steps.

For detailed information on how to use this feature, please refer to the [Interactions](interactions.md) documentation.