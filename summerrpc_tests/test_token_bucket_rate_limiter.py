from unittest import TestCase
import time

from summerrpc.rate_limiter import *


class TestTokenBucketRateLimiter(TestCase):
    def setUp(self):
        self._rate_limiter = TokenBucketRateLimiter(10, 1)
        self._redis_rate_limiter = RedisTokenBucketRateLimiter(
            "redis://redis:foobared@timd.cn:6379/0", 10, 1)

    def tearDown(self):
        self._redis_rate_limiter.close()

    def testConsume(self):
        self.assertTrue(self._rate_limiter.acquire(9))
        self.assertFalse(self._rate_limiter.acquire(9))
        time.sleep(0.001)
        self.assertTrue(self._rate_limiter.acquire(2))

    def testRedisConsume(self):
        self.assertTrue(self._redis_rate_limiter.acquire(1))
        self.assertTrue(self._redis_rate_limiter.acquire(9))
        self.assertFalse(self._redis_rate_limiter.acquire(9))

