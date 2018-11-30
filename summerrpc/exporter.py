# coding: utf8

"""
exporter：导入要暴漏的方法
"""

__all__ = ["Exporter"]
__authors__ = ["Tim Chow"]

import inspect
import warnings

from .decorator import get_export, get_provide
from .heartbeat import HeartBeatRequest


class Exporter(object):
    def __init__(self, install_heartbeat=True):
        self._exported = {}
        self._class_name_to_object = {}
        if install_heartbeat:
            self.export(HeartBeatRequest)

    def export(self, cls, cover=False):
        if not inspect.isclass(cls):
            warnings.warn("expect class, not %s" %
                          type(cls).__name__, RuntimeWarning)
            return self

        export_info = get_export(cls)
        if export_info is None:
            class_name = getattr(cls, "__name__")
        else:
            class_name = export_info["name"]

        if class_name in self._exported and not cover:
            warnings.warn("%s already exists" % repr(cls),
                          RuntimeWarning)
            return self

        d = self._exported[class_name] = {}
        # 创建类的实例
        instance = cls()
        self._class_name_to_object[class_name] = instance

        for attr_name, attr_value in vars(cls).iteritems():
            # 过滤掉所有的非方法属性
            if not inspect.isfunction(attr_value) and \
                    not inspect.ismethod(attr_value):
                continue
            # 过滤掉所有以_开头的方法
            if attr_name.startswith("_"):
                continue

            provide_info = get_provide(attr_value)
            if provide_info is not None:
                if provide_info["filtered"]:
                    continue
                d[provide_info["name"]] = getattr(instance, attr_name)
            else:
                d[attr_name] = getattr(instance, attr_name)

        return self

    def get_method(self, class_name, method_name):
        return self._exported.get(class_name, {}).get(method_name)

    def iter_method(self):
        for class_name, name_to_method in self._exported.iteritems():
            for method_name, method in name_to_method.iteritems():
                yield class_name, method_name, method

    def get_object(self, class_name):
        return self._class_name_to_object.get(class_name)
