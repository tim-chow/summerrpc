# coding: utf8

__all__ = ["Result"]
__authors__ = ["Tim Chow"]


class Result(object):
    def __init__(self):
        self._result = None
        self._exc = None
        self._meta = None

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, result):
        self._result = result

    @property
    def exc(self):
        return self._exc

    @exc.setter
    def exc(self, exc):
        self._exc = exc

    @property
    def meta(self):
        return self._meta

    @meta.setter
    def meta(self, meta):
        self._meta = meta
