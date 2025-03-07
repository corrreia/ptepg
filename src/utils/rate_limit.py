# Token Bucket for rate limiting
import asyncio
import datetime

from src.utils.constants import REQUESTS_PER_SECOND


class TokenBucket:
    def __init__(self, rate: int, per: float):
        """Initialize the token bucket.

        Args:
            rate: Number of requests allowed per time period.
            per: Time period in seconds (e.g., 1.0 for per second, 60.0 for per minute).
        """
        self.rate = rate
        self.per = per
        self.capacity = rate
        self.tokens = rate
        self.last_refill = datetime.now()

    async def acquire(self):
        """Acquire a token, waiting if none are available."""
        while self.tokens < 1:
            await asyncio.sleep(0.1)  # Brief sleep to avoid busy-waiting
            self.refill()
        self.tokens -= 1

    def refill(self):
        """Refill tokens based on elapsed time."""
        now = datetime.now()
        time_passed = (now - self.last_refill).total_seconds()
        tokens_to_add = time_passed * (self.rate / self.per)
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now


# Initialize with a default rate limit (e.g., 10 requests per second)
token_bucket = TokenBucket(rate=REQUESTS_PER_SECOND, per=1.0)
