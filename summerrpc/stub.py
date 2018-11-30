# coding: utf8

__all__ = ["Stub", "Refer"]
__authors__ = ["Tim Chow"]

import inspect
import logging
import threading
from functools import partial

from .transport import *
from .serializer import *
from .cluster import *
from .protocol import Protocol
from .helper import *
from .decorator import *
from .connection import *
from .request import Request
from .exception import *
from .heartbeat import *
from .refer_argument import ReferArgument
from .connection_pool import get_connection_from_pool

LOGGER = logging.getLogger(__name__)


class Stub(object):
    def __init__(self):
        self._transport = None
        self._serializer = None
        self._cluster = None
        self._protocol = None

    def set_transport(self, transport):
        if not isinstance(transport, Transport):
            raise TypeError("expect Transport, not %s" % type(transport).__name__)
        self._transport = transport
        return self

    def set_serializer(self, serializer):
        if not isinstance(serializer, Serializer):
            raise TypeError("expect Serializer, not %s" % type(serializer).__name__)
        self._serializer = serializer
        return self

    def set_cluster(self, cluster):
        if not isinstance(cluster, Cluster):
            raise TypeError("expect Cluster, not %s" % type(cluster).__name__)
        self._cluster = cluster
        return self

    def set_protocol(self, protocol):
        if not isinstance(protocol, Protocol):
            raise TypeError("expect Protocol, not %s" % type(protocol).__name__)
        self._protocol = protocol
        return self

    def refer(self, class_object, refer_argument=None):
        if not inspect.isclass(class_object):
            raise TypeError("expect class, not %s" % type(class_object).__name__)
        if refer_argument is None:
            refer_argument = ReferArgument()

        if self._transport is None:
            raise RuntimeError("transport must be provided")
        if self._serializer is None:
            raise RuntimeError("serializer must be provided")
        if self._cluster is None:
            raise RuntimeError("cluster must be provided")
        if self._protocol is None:
            raise RuntimeError("protocol must be provided")

        return Refer(class_object,
                     self._transport,
                     self._serializer,
                     self._cluster,
                     self._protocol,
                     self.heartbeat_func,
                     refer_argument)

    def close(self):
        if self._cluster is not None:
            self._cluster.close()
            self._cluster = None

    def heartbeat_func(self):
        class_name = HeartBeatRequest.__name__
        export = get_export(HeartBeatRequest)
        if export is not None:
            class_name = export["name"]

        method_name = "send"
        provide = get_provide(HeartBeatRequest.send)
        if provide is not None:
            if provide["filtered"]:
                raise RuntimeError("HeartBeatRequest.send is filtered")
            method_name = provide["name"]

        request = Request()
        request.class_name = class_name
        request.method_name = method_name
        request.args = tuple()
        request.kwargs = dict()
        request.meta = None

        return self._serializer.dumps(request)


class Refer(object):
    def __init__(self,
                 class_object,  # 被引用的类或接口
                 transport,  # 传输层
                 serializer,  # 序列化层
                 cluster,  # 集群层，用于负载均衡，包含Registry
                 protocol,  # 协议层，包含Filter和Invoker
                 heartbeat_func,  # 调用该函数，会返回序列化后的heartbeat请求
                 refer_argument):
        self._class_object = class_object
        self._transport = transport
        self._serializer = serializer
        self._cluster = cluster
        self._heartbeat_func = heartbeat_func
        self._protocol = protocol
        self._refer_argument = refer_argument
        self._connection_pool = refer_argument.connection_pool_class(
            refer_argument.connection_pool_size,
            refer_argument.connections_per_key)

        self._class_name = self._class_object.__name__
        export = get_export(self._class_object)
        if export is not None:
            self._class_name = export["name"]

    def __getattr__(self, attr_name):
        attr = getattr(self._class_object, attr_name, None)
        if attr is None:
            raise AttributeError("instance of %s has no attribute: %s" % (
                    self._class_object.__name__, attr_name))
        if not inspect.ismethod(attr):
            return attr

        method_name = attr_name
        provide = get_provide(attr)
        if provide is not None:
            if provide["filtered"]:
                raise RuntimeError("method %s.%s is not exported" %
                        (self._class_name, attr_name))
            method_name = provide["name"]
        return self._dynamic_proxy(method_name)

    def _connection_factory(self, host, port):
        sock = ClientSocketBuilder() \
            .with_host(host) \
            .with_port(port) \
            .with_tcp_no_delay() \
            .with_blocking() \
            .with_timeout(self._refer_argument.client_socket_timeout) \
            .build()
        connection = self._refer_argument.connection_class(sock,
                                        self._transport,
                                        self._refer_argument.max_pending_writes,
                                        self._refer_argument.max_pending_reads,
                                        self._refer_argument.max_pooling_reads,
                                        self._refer_argument.write_timeout,
                                        self._refer_argument.heartbeat_interval,
                                        self._heartbeat_func)
        return connection

    def _get_connnection_context(self, method_name):
        # 获取要连接到的远程服务的地址
        remote = self._cluster.get_remote(
                self._class_name,
                method_name,
                self._transport.get_name(),
                self._serializer.get_name())
        if remote is None:
            raise NoRemoteServerError(
                "there is no remote server")
        return get_connection_from_pool(
                self._connection_pool,
                remote,
                partial(self._connection_factory, remote[0], remote[1]))

    def _dynamic_proxy(self, method_name):
        def _inner(*args, **kwargs):
            # 生成Request对象
            request = Request()
            request.class_name = self._class_name
            request.method_name = method_name
            request.args = args
            request.kwargs = kwargs

            return self._protocol.invoke(
                        request,
                        self._get_connnection_context(method_name),
                        self._serializer,
                        self._refer_argument.write_timeout,
                        self._refer_argument.read_timeout)
        return _inner

    def refer_close(self):
        # 关闭连接池
        self._connection_pool.close()

