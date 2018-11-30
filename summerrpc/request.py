# coding: utf8

__all__ = ["Request"]
__authors__ = ["Tim Chow"]

from .exception import RequestValidateError


class Request(object):
    def __init__(self):
        self._class_name = None
        self._method_name = None
        self._args = tuple()
        self._kwargs = dict()
        self._meta = None

    @property
    def class_name(self):
        return self._class_name

    @class_name.setter
    def class_name(self, class_name):
        self._class_name = class_name

    @property
    def method_name(self):
        return self._method_name

    @method_name.setter
    def method_name(self, method_name):
        self._method_name = method_name

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, args):
        self._args = args

    @property
    def kwargs(self):
        return self._kwargs

    @kwargs.setter
    def kwargs(self, kwargs):
        self._kwargs = kwargs

    @property
    def meta(self):
        return self._meta

    @meta.setter
    def meta(self, meta):
        self._meta = meta

    def validate(self):
        if self.class_name is None or self.method_name is None:
            raise RequestValidateError(
                    "missing class name or method name")

    def __str__(self):
        return "Request{class_name=%s, \
                method_name=%s, args=%s, \
                kwargs=%s, meta=%s}" % \
                (self.class_name, self.method_name, \
                    self.args, self.kwargs, self.meta)

