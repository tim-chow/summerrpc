# coding: utf8

__all__ = ["Invoker", "RpcInvoker"]
__authors__ = ["Tim Chow"]

from abc import ABCMeta, abstractmethod

from concurrent.futures import TimeoutError

from .result import Result
from .exception import *
from .helper import *


class Invoker(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def invoke(self, request, connection_context, serializer, write_timeout, read_timeout):
        pass


class RpcInvoker(Invoker):
    def invoke(self, request, connection_context, serializer,
                write_timeout, read_timeout):
        # 序列化Request对象
        buff = serializer.dumps(request)

        with connection_context as connection:
            with time_used("connection write", 0.01):
                transaction_id, write_future = connection.write(buff, write_timeout)
                try:
                    write_future.result(write_timeout)
                except TimeoutError:
                    raise ConnectionWriteTimeout("timeout: %s" % write_timeout)
            read_future = connection.read(transaction_id)
        try:
            response = read_future.result(read_timeout)
        except TimeoutError:
            raise ConnectionReadTimeout("timeout: %s" % read_timeout)
        result = serializer.loads(response)
        if not isinstance(result, Result):
            raise InvalidResponseError("expect Result, not %s" %
                                       type(result).__name__)
        if result.exc is not None:
            raise result.exc
        return result.result

