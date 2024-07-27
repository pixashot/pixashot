class ScreenshotServiceException(Exception):
    """Base exception for the Screenshot Service"""


class BrowserException(ScreenshotServiceException):
    """Exception raised for errors in browser operations"""


class NetworkException(ScreenshotServiceException):
    """Exception raised for network-related errors"""


class ElementNotFoundException(ScreenshotServiceException):
    """Exception raised when a required element is not found on the page"""


class JavaScriptExecutionException(ScreenshotServiceException):
    """Exception raised when there's an error executing JavaScript"""


class TimeoutException(ScreenshotServiceException):
    """Exception raised when an operation times out"""


class InteractionException(ScreenshotServiceException):
    """Exception raised when there's an error during user interaction simulation"""


class AuthenticationError(Exception):
    pass


class SignatureExpiredError(AuthenticationError):
    pass


class InvalidSignatureError(AuthenticationError):
    pass
