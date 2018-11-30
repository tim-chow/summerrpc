# coding: utf8

"""
线程安全的字典
"""

__all__ = ["SafeDict"]
__authors__ = ["Tim Chow"]

import threading
import inspect
from functools import wraps


class SafeDict(object):
    def __init__(self):
        self.__dict = {}
        self.__lock = threading.RLock()

    def __getattr__(self, attr_name):
        attr_value = getattr(self.__dict, attr_name, None)
        if attr_value is None:
            raise AttributeError("instance of %s has no attribute %s" %
                                 (self.__class__.__name__, attr_name))
        if not inspect.ismethod(attr_value):
            return attr_value
        return self._thread_safe_wrapper(attr_value)

    def _thread_safe_wrapper(self, method):
        @wraps(method)
        def _inner(*a, **kw):
            with self.__lock:
                return method(*a, **kw)
        return _inner

    def __getitem__(self, *a, **kw):
        with self.__lock:
            return getattr(self.__dict, "__getitem__")(*a, **kw)

    def __setitem__(self, *a, **kw):
        with self.__lock:
            return getattr(self.__dict, "__setitem__")(*a, **kw)

    def __delitem__(self, *a, **kw):
        with self.__lock:
            return getattr(self.__dict, "__delitem__")(*a, **kw)

    def __str__(self, *a, **kw):
        with self.__lock:
            return getattr(self.__dict, "__str__")(*a, **kw)

    def __repr__(self, *a, **kw):
        with self.__lock:
            return getattr(self.__dict, "__repr__")(*a, **kw)

    def __len__(self, *a, **kw):
        with self.__lock:
            return getattr(self.__dict, "__len__")(*a, **kw)
