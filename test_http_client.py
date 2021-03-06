# coding: utf8

import time
import threading
import multiprocessing as mp
import logging
import traceback

from summerrpc.stub import Stub
from summerrpc.registry import ZookeeperRegistry
from summerrpc.cluster import RandomCluster
from summerrpc.invoker import RpcInvoker
from summerrpc.serializer import PickleSerializer
from summerrpc.extension.http_transport import SimpleBlockingHTTPTransport
from summerrpc.protocol import Protocol
from summerrpc.refer_argument import ReferArgument
from summerrpc.connection_pool import DedicateLRUConnectionPool
from summerrpc.connection import SimpleBlockingConnection

from test_service_interface import TestService

logging.basicConfig(level=logging.NOTSET,
                    format='%(threadName)s %(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
LOGGER = logging.getLogger(__name__)


def main(thread_count, request_count_per_thread):
    # 创建注册中心实例，并启动服务发现
    zkr = ZookeeperRegistry("10.22.1.194:2181,"
                            "10.22.1.194:2182,"
                            "10.22.1.194:2183,"
                            "10.22.1.194:2184",
                            "/summerrpc")
    zkr.discovery()
    while not zkr.discovery_successfully():
        LOGGER.info("discovery failed, sleep for a moment")
        time.sleep(0.1)

    # 使用注册中心构造cluster对象
    cluster = RandomCluster(zkr)

    # 使用Invoker对象创建Protocol对象
    protocol = Protocol() \
        .set_invoker(RpcInvoker())

    stub = Stub() \
        .set_transport(SimpleBlockingHTTPTransport()) \
        .set_serializer(PickleSerializer()) \
        .set_cluster(cluster) \
        .set_protocol(protocol)

    refer_argument = ReferArgument() \
        .set_client_socket_timeout(6) \
        .set_connection_pool_class(DedicateLRUConnectionPool) \
        .set_connection_class(SimpleBlockingConnection) \
        .set_connections_per_key(3)

    refer = stub.refer(TestService, refer_argument)

    def func():
        LOGGER.info("===== start =====")
        ident = threading.currentThread().ident
        for _ in range(request_count_per_thread):
            try:
                result = refer.test_async(ident)
                LOGGER.info("invoke test_async(), result is: %s" % result)
            except:
                traceback.print_exc()
                raise
        LOGGER.info("===== end =====")

    # 调用业务方法
    start = time.time()
    if thread_count > 1:
        threads = []
        for _ in range(thread_count):
            thread = threading.Thread(target=func)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
    else:
        func()
    LOGGER.error("time used: %f" % (time.time() - start, ))

    # 关闭refer
    refer.refer_close()
    # 关闭stub
    stub.close()


if __name__ == "__main__":
    process_count = 5
    thread_count = 20
    request_count_per_thread = 100

    start = time.time()
    if process_count > 1:
        processes = []
        for _ in range(process_count):
            p = mp.Process(target=main,
                args=(thread_count, request_count_per_thread))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()
    else:
        main(thread_count, request_count_per_thread)
    LOGGER.error("total time used: %fs" % (time.time() - start))

