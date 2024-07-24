# Usage

## Starting the Server

To start the Flask server:

```
python src/app.py
```

By default, the server will run on `http://localhost:8080`. You can change the port by setting the `PORT` environment variable.

## Making a Screenshot Request

To capture a screenshot, send a POST request to the `/screenshot` endpoint with a JSON payload containing the screenshot options.

Example using curl:

```bash
curl -X POST http://localhost:8080/screenshot \
     -H "Content-Type: application/json" \
     -d '{
           "url": "https://example.com",
           "window_width": 1920,
           "window_height": 1080,
           "format": "png",
           "full_page": true
         }'
```

For a complete list of configuration options, see the [Configuration Options](configuration.md) documentation.

## Security Considerations

- The service includes optional token-based authentication. Set the `AUTH_TOKEN` environment variable to enable it.
- Be cautious when allowing custom JavaScript injection, as it can potentially expose sensitive information.
- When deploying, ensure proper firewall rules and access controls are in place.

For more advanced usage and features, please refer to the [Advanced Features](advanced.md) documentation.