import os
import time
import hmac
import hashlib
import base64
from urllib.parse import parse_qs, urlparse, urlencode

from exceptions import InvalidSignatureError, SignatureExpiredError, AuthenticationError

URL_SIGNING_SECRET = os.environ.get('URL_SIGNING_SECRET')
AUTH_TOKEN = os.environ.get('AUTH_TOKEN')


def verify_auth_token(auth_header):
    if not AUTH_TOKEN:
        return False
    token = auth_header.split(' ')[1] if auth_header and len(auth_header.split(' ')) > 1 else None
    return token == AUTH_TOKEN


def generate_signature(params, secret_key):
    param_string = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
    message = param_string.encode('utf-8')
    return base64.urlsafe_b64encode(
        hmac.new(secret_key.encode('utf-8'), message, hashlib.sha256).digest()
    ).rstrip(b'=').decode('ascii')


def verify_signed_url(query_params, secret_key):
    try:
        signature = query_params.get('signature', [None])[0]
        expires = query_params.get('expires', [None])[0]

        if not signature:
            raise InvalidSignatureError("Missing signature")

        if expires:
            expires = int(expires)
            if time.time() > expires:
                raise SignatureExpiredError("Signature has expired")

        params_to_sign = {k: v[0] for k, v in query_params.items() if k not in ['signature']}
        expected_signature = generate_signature(params_to_sign, secret_key)

        if not hmac.compare_digest(signature, expected_signature):
            raise InvalidSignatureError("Invalid signature")

    except Exception as e:
        raise InvalidSignatureError(str(e))


def generate_signed_url(base_url, params, secret_key, expires_in=3600):
    expiration = int(time.time()) + expires_in
    params['expires'] = expiration

    signature = generate_signature(params, secret_key)

    params['signature'] = signature
    return f"{base_url}?{urlencode(params)}"


def is_authenticated(request):
    auth_header = request.headers.get('Authorization')
    if verify_auth_token(auth_header):
        return True

    parsed_url = urlparse(request.url)
    query_params = parse_qs(parsed_url.query)

    try:
        verify_signed_url(query_params, URL_SIGNING_SECRET)
        return True
    except AuthenticationError:
        return False
