# coding: utf8

__all__ = ["HeartBeatRequest", "HeartBeatResponse"]
__authors__ = ["Tim Chow"]

import time


class HeartBeatRequest(object):
    def send(self, *a, **kw):
        h = HeartBeatResponse()
        h.timestamp = time.time()
        h.args = a
        h.kwargs = kw
        return h


class HeartBeatResponse(object):
    def __init__(self):
        self._timestamp = None
        self._args = tuple()
        self._kwargs = dict()

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp):
        self._timestamp = timestamp

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, args):
        if not isinstance(args, tuple):
            raise TypeError("expect tuple, not %s" %
                            type(args).__name__)
        self._args = args

    @property
    def kwargs(self):
        return self._kwargs

    @kwargs.setter
    def kwargs(self, kwargs):
        if not isinstance(kwargs, dict):
            raise TypeError("expect dict, not %s" %
                            type(kwargs).__name__)
        self._kwargs = kwargs

    def __str__(self):
        return "%s{timestamp=%.3f, args=%s, kwargs=%s}" % (
            self.__class__.__name__, self._timestamp, self._args, self._kwargs)
