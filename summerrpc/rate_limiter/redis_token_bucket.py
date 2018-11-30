# coding: utf8

__all__ = ["RedisTokenBucketRateLimiter"]
__authors__ = ["Tim Chow"]

import time
import math

import redis

from .interface import RateLimiter


SCRIPT = """
local tokens_key = KEYS[1]
local timestamp_key = KEYS[2]

local rate = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local fill_time = capacity/rate
local ttl = math.floor(fill_time*2)

local last_tokens = tonumber(redis.call("get", tokens_key))
if last_tokens == nil then
  last_tokens = capacity
end

local last_refreshed = tonumber(redis.call("get", timestamp_key))
if last_refreshed == nil then
  last_refreshed = 0
end

local delta = math.max(0, now-last_refreshed)
local filled_tokens = math.min(capacity, last_tokens+(delta*rate))
local allowed = filled_tokens >= requested
local new_tokens = filled_tokens
local allowed_num = 0
if allowed then
  new_tokens = filled_tokens - requested
  allowed_num = 1
end

redis.call("setex", tokens_key, ttl, new_tokens)
redis.call("setex", timestamp_key, ttl, now)

return { allowed_num, new_tokens }
"""


class RedisTokenBucketRateLimiter(object):
    def __init__(self, redis_url, capacity, rate):
        self._redis_client = redis.from_url(redis_url)
        self._script = self._redis_client.register_script(SCRIPT)
        self._capacity = capacity
        self._rate = rate

    def acquire(self, requested_number=1, key="RedisTokenBucketRateLimiter"):
        allowed, _ = self._script(keys=[key, "%s.ts" % key],
                args=[self._rate, self._capacity,
                    long(time.time()), requested_number])
        return not not allowed

    def close(self):
        pass

