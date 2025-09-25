import time
from collections import defaultdict, deque

class TokenBucketLimiter:
    """Simple per-IP token bucket for rate limiting."""
    def __init__(self, per_minute=120, burst=30):
        self.capacity = burst
        self.refill_rate = per_minute / 60.0  # tokens per second
        self.buckets = defaultdict(lambda: {'tokens': burst, 'last': time.time()})

    def allow(self, key: str) -> bool:
        now = time.time()
        b = self.buckets[key]
        elapsed = now - b['last']
        b['tokens'] = min(self.capacity, b['tokens'] + elapsed * self.refill_rate)
        b['last'] = now
        if b['tokens'] >= 1.0:
            b['tokens'] -= 1.0
            return True
        return False