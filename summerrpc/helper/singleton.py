# coding: utf8

__all__ = ["Singleton"]
__authors__ = ["Tim Chow"]

import threading


class Singleton(object):
    _instances = {}
    _lock = threading.Lock()

    def __new__(cls, *a, **kw):
        if cls in Singleton._instances:
            return Singleton._instances[cls]

        with Singleton._lock:
            if cls in Singleton._instances:
                return Singleton._instances[cls]

            instance = super(Singleton, cls).__new__(cls, *a, **kw)
            Singleton._instances[cls] = instance
            return instance
