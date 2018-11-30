# coding: utf8

__all__ = ["MaxRetryCountReached", "RetryPolicy"]
__authors__ = ["Tim Chow"]

import sys
import time
import traceback


class MaxRetryCountReached(StandardError):
    def __init__(self, exc_info, *a, **kw):
        super(self.__class__, self).__init__(*a, **kw)
        self._exc_info = exc_info

    @property
    def exc_info(self):
        return self._exc_info


class RetryPolicy(object):
    __slots__ = ("max_retry_count", "retry_interval", "retry_exceptions")

    def run(self, f, *a, **kw):
        retry_count = 0
        exc_info = None

        while self.max_retry_count == -1 or \
                retry_count <= self.max_retry_count:
            try:
                return f(*a, **kw)
            except self.retry_exceptions:
                exc_info = sys.exc_info()
                traceback.print_exc()
            retry_count = retry_count + 1
            time.sleep(self.retry_interval)
        else:
            raise MaxRetryCountReached(exc_info)

    def __str__(self):
        return "%s{max_retry_count=%d, retry_interval=%f, retry_exceptions=%s}" % \
                    (self.__class__.__name__, self.max_retry_count, 
                        self.retry_interval, str(self.retry_exceptions))

    def __repr__(self):
        return self.__str__() + "@" + hex(id(self))

    class Builder(object):
        def __init__(self):
            self._max_retry_count = 100
            self._retry_interval = 3
            self._retry_exceptions = []

        def with_max_retry_count(self, count):
            if not isinstance(count, (int, long)):
                raise TypeError("expect int or long, not %s" %
                                type(count).__name__)
            if count < -1:
                raise ValueError("max_retry_count should not be less than -1")
            self._max_retry_count = count
            return self

        def with_retry_interval(self, interval):
            if not isinstance(interval, (int, long, float)):
                raise TypeError("expect float, not %s" %
                                type(interval).__name__)
            if interval <= 0:
                raise ValueError("retry_interval should be more than 0")
            self._retry_interval = interval
            return self

        def add_retry_exception(self, exception):
            if not issubclass(exception, BaseException):
                raise TypeError("expect subclass of BaseException")
            self._retry_exceptions.append(exception)
            return self

        def build(self):
            retry_policy = RetryPolicy()
            retry_policy.max_retry_count = self._max_retry_count
            retry_policy.retry_interval = self._retry_interval
            retry_policy.retry_exceptions = tuple(set(self._retry_exceptions))
            return retry_policy
