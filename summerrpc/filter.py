# coding: utf8

__all__ = ["Filter", "LogFilter"]
__authors__ = ["Tim Chow"]

from abc import ABCMeta, abstractmethod
import logging

LOGGER = logging.getLogger(__name__)


class Filter(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def filter(self, request):
        pass

    @abstractmethod
    def get_order(self):
        pass


class LogFilter(Filter):
    def filter(self, request):
        LOGGER.info("%s.%s() is invoked, " % (request.class_name,
                                              request.method_name) +
                    "with arguments: %s, " % (request.args, ) +
                    "keyword arguments: %s, " % (request.kwargs, ) +
                    "meta: %s" % request.meta)

    def get_order(self):
        import sys
        return sys.maxint
