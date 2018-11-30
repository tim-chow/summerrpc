# coding: utf8

__all__ = ["AtomicInteger"]
__authors__ = ["Tim Chow"]

import threading
import sys


class AtomicInteger(object):
    def __init__(self, initial_value=0):
        # initial_value应该大于0
        self._initial_value = initial_value
        self._internal_integer = initial_value
        self._max_integer = sys.maxint
        self._lock = threading.RLock()

    def increase(self, increment=1):
        with self._lock:
            # increment应该大于0
            value = self._max_integer - self._internal_integer - increment
            # 如果没有溢出，则直接累加
            if value >= 0:
                self._internal_integer = self._internal_integer + increment
                return self._internal_integer
            # 如果溢出了，则直接置为初始值
            self._internal_integer = self._initial_value
            return self._internal_integer

    def get_value(self):
        with self._lock:
            return self._internal_integer

    def compare_and_set(self, expect, update):
        with self._lock:
            if self._internal_integer != expect:
                return False
            self._internal_integer = update
            return True
