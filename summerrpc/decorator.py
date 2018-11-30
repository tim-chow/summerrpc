# coding: utf8

"""
修改类的导出名称、过滤掉不想暴漏的方法

@export("service")
class Service(object):
    @provide(filtered=True)
    def filtered_method(self):
        pass

    def exported_method(self):
        pass
"""

__all__ = ["export", "get_export", "provide", "get_provide",
           "run_in_subprocess", "get_run_in_subprocess"]
__authors__ = ["Tim Chow"]

import inspect
import warnings


def export(name):
    if not isinstance(name, str):
        raise TypeError("expect str, not %s" %
                        type(name).__name__)

    def _inner(cls):
        if not inspect.isclass(cls):
            warnings.warn("expect class, not %s" %
                          type(cls).__name__, RuntimeWarning)
            return cls

        setattr(cls, "__rpc_export__", {"name": name})
        return cls

    return _inner


def get_export(cls):
    if not inspect.isclass(cls):
        warnings.warn("expect class, not %s" %
                      type(cls).__name__, RuntimeWarning)
        return None

    export_info = getattr(cls, "__rpc_export__", None)
    if export_info is None or not isinstance(export_info, dict):
        return None

    return export_info


def provide(name=None, filtered=False):
    def _inner(f):
        if not inspect.isfunction(f) and not inspect.ismethod(f):
            warnings.warn("expect method or function, not %s" %
                          type(f).__name__, RuntimeWarning)
            return f

        if name is None:
            name = f.__name__

        setattr(f, "__rpc_provide__", {"name": name, "filtered": filtered})
        return f
    return _inner


def get_provide(f):
    if not inspect.isfunction(f) and not inspect.ismethod(f):
        warnings.warn("expect method or function, not %s" %
                      type(f).__name__, RuntimeWarning)
        return None

    provide_info = getattr(f, "__rpc_provide__", None)
    if provide_info is None or not isinstance(provide_info, dict):
        return None

    return provide_info


def run_in_subprocess(f):
    if not inspect.isfunction(f) and not inspect.ismethod(f):
        warnings.warn("expect method or function, not %s" %
                      type(f).__name__, RuntimeWarning)
        return f

    setattr(f, "__run_in_subprocess__", True)
    return f


def get_run_in_subprocess(f):
    if not inspect.isfunction(f) and not inspect.ismethod(f):
        warnings.warn("expect method or function, not %s" %
                      type(f).__name__, RuntimeWarning)
        return None

    run_in_subprocess_info = getattr(f, "__run_in_subprocess__", None)
    if not isinstance(run_in_subprocess_info, bool):
        return None

    return run_in_subprocess_info
