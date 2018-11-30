# coding: utf8

__all__ = ["RateLimiter"]
__authors__ = ["Tim Chow"]

from abc import abstractmethod, ABCMeta


class RateLimiter(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def acquire(self, requested_number=1):
        pass

    @abstractmethod
    def close(self):
        pass

