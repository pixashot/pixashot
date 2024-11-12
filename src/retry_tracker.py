import time
from typing import List, Dict, Any, Optional


class RetryAttemptInfo:
    def __init__(self, attempt_number: int, error: Optional[Exception], timestamp: float):
        self.attempt_number = attempt_number
        self.error = error
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt": self.attempt_number,
            "error": str(self.error) if self.error else "No error information available",
            "error_type": self.error.__class__.__name__ if self.error else "Unknown",
            "timestamp": self.timestamp
        }


class RetryTracker:
    def __init__(self):
        self.attempts: List[RetryAttemptInfo] = []

    def add_attempt(self, attempt: RetryAttemptInfo) -> None:
        self.attempts.append(attempt)

    def get_attempts(self) -> List[Dict[str, Any]]:
        return [attempt.to_dict() for attempt in self.attempts]


def before_retry(retry_state):
    """Handler to be called before each retry attempt"""
    if not hasattr(retry_state, 'retry_tracker'):
        retry_state.retry_tracker = RetryTracker()

    # Get the exception if available, otherwise None
    exception = retry_state.outcome.exception() if retry_state.outcome else None

    retry_state.retry_tracker.add_attempt(RetryAttemptInfo(
        attempt_number=len(retry_state.retry_tracker.attempts) + 1,
        error=exception,
        timestamp=time.time()
    ))