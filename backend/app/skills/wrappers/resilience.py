from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class ExternalAPIException(Exception):
    """Exception raised when an external API call fails after all retries."""
    pass

class TransientNetworkError(Exception):
    """Exception raised for temporary network issues (e.g., timeouts, 503s)."""
    pass

def with_retry():
    """
    Standard resilience decorator.
    Retries up to 3 times with exponential backoff (1s, 2s, 4s).
    Only retries on TransientNetworkError.
    """
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(TransientNetworkError),
        reraise=True
    )
