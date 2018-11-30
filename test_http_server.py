# coding: utf8

import logging
import threading

from summerrpc.helper import (
        ServerSocketBuilder,
        get_local_ip)
from summerrpc.exporter import Exporter
from summerrpc.rpc_server import RpcServerBuilder
from summerrpc.serializer import PickleSerializer 
from summerrpc.extension.http_transport import HTTPTransport
from summerrpc.registry import ZookeeperRegistry

from test_service import TestService

logging.basicConfig(level=logging.WARN,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')

LOGGER = logging.getLogger(__name__)


def main():
    host = "127.0.0.1"
    for ip in get_local_ip(exclude_interfaces=["lo", "eth0", "eth1"]):
        host = ip
        break

    # 创建Server Socket
    server_socket = ServerSocketBuilder() \
        .with_host(host) \
        .with_port(0) \
        .with_non_blocking() \
        .with_tcp_no_delay() \
        .with_backlog(5) \
        .build()
    host, port = server_socket.getsockname()
    LOGGER.debug("server socket bind (%s, %d)" % (host, port))

    # 定义要暴漏的方法
    exporter = Exporter().export(TestService)

    # 创建注册中心实例
    registry = ZookeeperRegistry("10.22.1.194:2181,"
                                 "10.22.1.194:2182,"
                                 "10.22.1.194:2183,"
                                 "10.22.1.194:2184",
                                 "/summerrpc")

    rpc_server = RpcServerBuilder() \
        .with_server_socket(server_socket) \
        .with_exporter(exporter) \
        .with_max_idle_time(120) \
        .with_serializer(PickleSerializer()) \
        .with_transport(HTTPTransport()) \
        .with_registry(registry) \
        .with_concurrent_request_per_connection(100) \
        .with_thread_pool_size(3) \
        .build()

    rpc_server.start()


if __name__ == "__main__":
    main()

