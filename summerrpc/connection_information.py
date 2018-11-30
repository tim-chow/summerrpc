# coding: utf8

__all__ = ["ConnectionInformation"]
__authors__ = ["Tim Chow"]


class ConnectionInformation(object):
    def __init__(self, stream=None, timestamp=None, read_condition=None):
        self._stream = stream
        self._timestamp = timestamp
        self._read_condition = read_condition
        self._stream_closed = False

    @property
    def stream(self):
        return self._stream

    @stream.setter
    def stream(self, stream):
        self._stream = stream

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp):
        self._timestamp = timestamp

    @property
    def read_condition(self):
        return self._read_condition

    @read_condition.setter
    def read_condition(self, read_condition):
        self._read_condition = read_condition

    @property
    def stream_closed(self):
        return self._stream_closed

    @stream_closed.setter
    def stream_closed(self, stream_closed):
        self._stream_closed = bool(stream_closed)

