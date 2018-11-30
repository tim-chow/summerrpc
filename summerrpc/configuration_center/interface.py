# coding: utf8

__all__ = ["ConfigurationCenter"]
__authors__ = ["Tim Chow"]

import abc


class ConfigurationCenter(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def start(self, key):
        pass

    @abc.abstractmethod
    def close(self, key, value):
        pass

    @abc.abstractmethod
    def get_key(self, key):
        pass

    @abc.abstractproperty
    def success(self):
        pass

    @abc.abstractproperty
    def main_version(self):
        pass

    @abc.abstractmethod
    def iteritems(self):
        pass

