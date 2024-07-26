import os
import time
import hmac
import hashlib
import base64
from urllib.parse import parse_qs, urlparse

# Secret key for signing URLs (should be stored securely, e.g., as an environment variable)
URL_SIGNING_SECRET = os.environ.get('URL_SIGNING_SECRET')
AUTH_TOKEN = os.environ.get('AUTH_TOKEN')


def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def verify_auth_token(auth_header):
    if not AUTH_TOKEN:
        return False
    token = auth_header.split(' ')[1] if auth_header and len(auth_header.split(' ')) > 1 else None
    return token == AUTH_TOKEN


def verify_signed_url(query_params):
    try:
        signature = query_params.get('signature', [None])[0]
        expires = query_params.get('expires', [None])[0]

        if not signature:
            return False

        if expires:
            expires = int(expires)
            if time.time() > expires:
                return False

        # Reconstruct the string to sign
        params_to_sign = {k: v[0] for k, v in query_params.items() if k not in ['signature']}
        param_string = '&'.join(f"{k}={v}" for k, v in sorted(params_to_sign.items()))

        # Create the expected signature
        message = param_string.encode('utf-8')
        expected_signature = base64url_encode(
            hmac.new(URL_SIGNING_SECRET.encode('utf-8'), message, hashlib.sha256).digest())

        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)
    except Exception:
        return False


def generate_signed_url(base_url, params, secret_key, expires_in=None):
    """
    Generate a signed URL for the Pixashot service.

    :param base_url: The base URL of the Pixashot service
    :param params: Dictionary of query parameters
    :param secret_key: Secret key for signing the URL
    :param expires_in: Number of seconds until the URL expires (optional)
    :return: Signed URL as a string
    """
    # Add expiration timestamp if provided
    if expires_in is not None:
        params['expires'] = int(time.time()) + expires_in

    # Sort parameters and create the string to sign
    param_string = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))

    # Create the signature
    message = param_string.encode('utf-8')
    signature = base64url_encode(hmac.new(secret_key.encode('utf-8'), message, hashlib.sha256).digest())

    # Add the signature to the parameters
    params['signature'] = signature

    # Create the full signed URL
    from urllib.parse import urlencode
    return f"{base_url}?{urlencode(params)}"


def is_authenticated(request):
    # Check for auth token in header
    auth_header = request.headers.get('Authorization')
    if verify_auth_token(auth_header):
        return True

    # Check for signed URL
    parsed_url = urlparse(request.url)
    query_params = parse_qs(parsed_url.query)

    return verify_signed_url(query_params)