# coding: utf8

__all__ = ["BaseSerializer"]
__authors__ = ["Tim Chow"]

from ..serializer import Serializer
from ..request import Request
from ..result import Result
from ..exception import DeserializationError, SerializationError


class BaseSerializer(Serializer):
    def loads(self, buff):
        try:
            data = self._loads(buff)
            if not isinstance(data, dict):
                raise TypeError
            is_request = not not data.get("is_request", True)

            if is_request:
                class_name = data.get("class_name")
                method_name = data.get("method_name")
                args = data.get("args", tuple())
                kwargs = data.get("kwargs", dict())
                
                if not isinstance(class_name, basestring) or \
                        not isinstance(method_name, basestring) or \
                        not isinstance(args, (tuple, list)) or \
                        not isinstance(kwargs, dict):
                    raise ValueError
                request = Request()
                request.class_name = class_name
                request.method_name = method_name
                request.args = args
                request.kwargs = kwargs
                return request
            else:
                result = Result()
                if "result" in data:
                    result.result = data["result"]
                if "exc" in data and data["exc"] is not None:
                    result.exc = RuntimeError(data["exc"])
                if "meta" in data:
                    result.meta = data["meta"]
                return result 
        except (TypeError, ValueError) as ex:
            raise DeserializationError(ex)

    def _loads(self, buff):
        raise NotImplementedError

    def dumps(self, obj, protocol=None):
        d = {}
        if isinstance(obj, Request):
            d["class_name"] = obj.class_name
            d["method_name"] = obj.method_name
            d["args"] = obj.args
            d["kwargs"] = obj.kwargs
            d["meta"] = obj.meta
            d["is_request"] = True
        elif isinstance(obj, Result):
            d["result"] = obj.result
            d["exc"] = None
            if obj.exc is not None:
                d["exc"] = "%s: %s" % (type(obj.exc).__name__, str(obj.exc))
            d["meta"] = obj.meta
            d["is_request"] = False

        try:
            if not d:
                raise TypeError
            return self._dumps(d)
        except (TypeError, ValueError) as ex:
            raise SerializationError(ex)

    def _dumps(self, d):
        raise NotImplementedError

