# Authentication in Pixashot

Pixashot provides a flexible authentication system that supports two methods:
1. Auth Token
2. Signed URLs

This document outlines how to use each method, their pros and cons, and best practices for securing your Pixashot service.

## Auth Token

The Auth Token method is a simple, header-based authentication system.

### How to Use

1. Set the `AUTH_TOKEN` environment variable on your server:
   ```
   export AUTH_TOKEN=your_secure_token_here
   ```

2. Include the token in the `Authorization` header of your requests:
   ```
   Authorization: Bearer your_secure_token_here
   ```

### Pros
- Simple to implement and use
- Works well for server-to-server communication
- Suitable for scenarios where you have full control over the client

### Cons
- Token needs to be securely stored and transmitted
- All requests have the same level of access
- Revoking access requires changing the token

## Signed URLs

Signed URLs provide a way to grant temporary or permanent access to the Pixashot service without sharing your auth token.

### How to Use

1. Set the `URL_SIGNING_SECRET` environment variable on your server:
   ```
   export URL_SIGNING_SECRET=your_signing_secret_here
   ```

2. Use the `generate_signed_url` function from `request_auth.py` to create signed URLs:

   ```python
   from request_auth import generate_signed_url

   base_url = "https://your-pixashot-service.com/capture"
   params = {
       "url": "https://example.com",
       "format": "png"
   }
   secret_key = "your_signing_secret_here"

   # Generate a URL that never expires (default behavior)
   signed_url_no_expiry = generate_signed_url(base_url, params, secret_key)

   # Generate a URL that expires in 1 hour
   signed_url_with_expiry = generate_signed_url(base_url, params, secret_key, expires_in=3600)
   ```

### Pros
- Can create URLs with or without expiration
- Allows for fine-grained access control (each URL can have different parameters)
- No need to share or transmit tokens
- Suitable for client-side applications or sharing screenshots with third parties

### Cons
- Requires more setup and understanding to implement correctly
- Non-expiring URLs can pose a security risk if not managed properly

## Best Practices

1. **Secure Storage**: Store your `AUTH_TOKEN` and `URL_SIGNING_SECRET` securely. Never expose them in client-side code or public repositories.

2. **HTTPS**: Always use HTTPS to encrypt all communications with the Pixashot service.

3. **Expiring URLs**: For sensitive operations or private data, use expiring URLs to limit the window of potential misuse.

4. **Principle of Least Privilege**: Generate URLs with only the necessary permissions and for the shortest required duration.

5. **Rotate Secrets**: Periodically rotate your `AUTH_TOKEN` and `URL_SIGNING_SECRET` to mitigate the risk of compromised credentials.

6. **Monitoring**: Implement logging and monitoring to detect unusual patterns of access or potential abuse.

7. **Rate Limiting**: Use Pixashot's built-in rate limiting features to prevent abuse.

## Implementation Details

The authentication logic is encapsulated in the `request_auth.py` file. This module contains functions for verifying auth tokens, generating and verifying signed URLs, and checking if a request is authenticated.

Key functions:
- `verify_auth_token(auth_header)`: Verifies the auth token from the request header.
- `verify_signed_url(query_params)`: Verifies a signed URL.
- `generate_signed_url(base_url, params, secret_key, expires_in=None)`: Generates a signed URL.
- `is_authenticated(request)`: Checks if a request is authenticated using either method.

For more details on these functions, refer to the comments in the `request_auth.py` file.

## Troubleshooting

If you're experiencing authentication issues:

1. Check that your `AUTH_TOKEN` or `URL_SIGNING_SECRET` is correctly set in your environment variables.
2. Ensure you're using HTTPS for all requests.
3. Verify that the clock on your server is correctly synchronized (important for expiring URLs).
4. Check the Pixashot server logs for any authentication-related error messages.

If problems persist, please contact Pixashot support with details of the issue you're experiencing.