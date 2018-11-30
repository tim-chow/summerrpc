# coding: utf8

__all__ = ["Protocol"]
__authors__ = ["Tim Chow"]

from .filter import Filter
from .invoker import Invoker


class Protocol(object):
    def __init__(self):
        self._filters = []
        self._invoker = None

    def add_filter(self, filter_):
        if not isinstance(filter_, Filter):
            raise TypeError("expect Filter, not %s" % type(filter_).__name__)
        self._filters.append(filter_)
        return self

    def set_invoker(self, invoker):
        if not isinstance(invoker, Invoker):
            raise TypeError("expect Invoker, not %s" % type(invoker).__name__)
        self._invoker = invoker
        return self

    def invoke(self, request, connection_context, serializer, write_timeout, read_timeout):
        filters = sorted(self._filters, key=lambda f: f.get_order(), reverse=True)
        for filter_ in filters:
            filter_.filter(request)
        return self._invoker.invoke(request,
                                    connection_context,
                                    serializer,
                                    write_timeout,
                                    read_timeout)
