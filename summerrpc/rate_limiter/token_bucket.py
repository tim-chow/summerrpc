# coding: utf8

__all__ = ["TokenBucketRateLimiter"]
__authors__ = ["Tim Chow"]

import threading
import time
import math

from .interface import RateLimiter


class TokenBucketRateLimiter(RateLimiter):
    def __init__(self, capacity, rate, lock=None):
        self._capacity = capacity
        self._rate = rate
        self._lock = lock or threading.Lock()
        self._last_refresh_time = 0.
        self._consumed_tokens = 0

    def acquire(self, requested_number=1):
        with self._lock:
            return self._acquire(requested_number)

    def _acquire(self, requested_number):
        # 计算新产生的token
        now = long(math.floor(time.time() * 1000))
        time_elapsed_ms = max(0, now - self._last_refresh_time)
        new_generated_tokens = long(math.floor(time_elapsed_ms * self._rate))

        # 调整更新时间，注意：不能吃掉不足以产生一个令牌的时间
        self._last_refresh_time = \
            now - (time_elapsed_ms - long(new_generated_tokens / self._rate))

        # 当调小令牌桶容量时，需要保证消耗的令牌数不能超过容量
        self._consumed_tokens = min(self._capacity, self._consumed_tokens)

        # 填充令牌
        self._consumed_tokens = max(0, self._consumed_tokens - new_generated_tokens)

        if self._consumed_tokens + requested_number <= self._capacity:
            self._consumed_tokens = self._consumed_tokens + requested_number
            return True
        return False

    def close(self):
        pass

