# coding: utf8

__all__ = ["ConnectionPool", "LRUConnectionPool",
            "DedicateLRUConnectionPool", "SharedLRUConnectionPool",
            "get_connection_from_pool"]
__authors__ = ["Tim Chow"]

import abc
import threading
from Queue import Queue, Empty
from contextlib import contextmanager
import logging

from .helper import *
from .exception import *

LOGGER = logging.getLogger(__name__)


@contextmanager
def get_connection_from_pool(pool,
        key,
        connection_factory,
        block=True,
        timeout=None):
    connection = pool.get_connection(key,
        connection_factory,
        block,
        timeout)
    try:
        yield connection
    finally:
        pool.release_connection(key, connection)


class ConnectionPool(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_connection(self,
            key,
            connection_factory,
            block=True,
            timeout=None):
        """从连接池中获取连接"""
        pass

    @abc.abstractmethod
    def release_connection(self, key, connection):
        """将连接放回连接池"""
        pass

    @abc.abstractmethod
    def close(self):
        """关闭连接池及其维护的所有连接"""
        pass


class LRUConnectionPool(ConnectionPool):
    def __init__(self, connection_pool_size, connections_per_key=1):
        # connection_pool_size：连接池的大小，也就是key的最大数量
        self._pool = LRUCache(connection_pool_size)
        self._lock = threading.Lock()
        # connections_per_key：每个key对应的连接的数量
        self._connections_per_key = connections_per_key
        self._closed = False

    def get_connection(self,
                key,
                connection_factory,
                block=True,
                timeout=None):
        # connection_factory：用于创建连接对象的工厂函数
        container = self._create_connections_if_necessary(
            key,
            connection_factory)
        while True:
            connection = self._choice_connection_from_container(
                container,
                block,
                timeout)
            if connection.closing or connection.closed:
                self._remove_connection_from_container(container, connection)
                try:
                    connection = connection_factory()
                except:
                    raise CreateConnectionError
                self._add_connection_to_container(container, connection)
            else:
                return connection
        raise RuntimeError("unreachable")

    def _initialize_connections(self, container, connection_factory):
        for _ in range(self._connections_per_key):
            try:
                connection = connection_factory()
            except:
                raise CreateConnectionError
            self._add_connection_to_container(container, connection)

    def _create_connections_if_necessary(self, key, connection_factory):
        with self._lock:
            if self._closed:
                raise ConnectionPoolAlreadyClosedError

            if key in self._pool:
                return self._pool[key]

            container = self._get_connection_container(self._connections_per_key)
            self._initialize_connections(container, connection_factory)

            entry = self._pool.will_be_kicked_out()
            # 如果连接池已经满了，那么关闭要踢出的连接
            if entry is not None:
                self._close_connections(entry.value)
                LOGGER.info("kicked out key: %s" % (entry.key, ))
            self._pool[key] = container
            return container

    def release_connection(self, key, connection):
        with self._lock:
            if self._closed:
                return
            if key not in self._pool:
                return
            container = self._pool[key]
        self._release_connection_to_container(container, connection)

    def close(self):
        if self._closed:
            return
        with self._lock:
            if self._closed:
                return

            for key, container in self._pool.iteritems():
                self._close_connections(container)
                LOGGER.info("closed connections, key is: %s" % (key, ))
            self._closed = True

    def _get_connection_container(self, max_size):
        raise NotImplementedError

    def _add_connection_to_container(self, container, connection):
        raise NotImplementedError

    def _close_connections(self, container):
        raise NotImplementedError

    def _choice_connection_from_container(self, container, block, timeout):
        raise NotImplementedError

    def _remove_connection_from_container(self, container, connection):
        raise NotImplementedError

    def _release_connection_to_container(self, container, connection):
        raise NotImplementedError


class DedicateLRUConnectionPool(LRUConnectionPool):
    def _get_connection_container(self, max_size):
        return Queue()

    def _add_connection_to_container(self, container, connection):
        container.put(connection)

    def _close_connections(self, container):
        while True:
            try:
                connection = container.get_nowait()
            except Empty:
                break
            connection.close()

    def _choice_connection_from_container(self, container, block, timeout):
        try:
            connection = container.get(block, timeout)
        except Empty:
            raise NoAvailableConnectionError
        return connection

    def _remove_connection_from_container(self, container, connection):
        pass

    def _release_connection_to_container(self, container, connection):
        container.put(connection)


class SharedLRUConnectionPool(LRUConnectionPool):
    def _get_connection_container(self, max_size):
        return CyclicIterator([])

    def _add_connection_to_container(self, container, connection):
        with container.condition:
            container.append(connection)

    def _close_connections(self, container):
        with container.condition:
            container.rewind()
            while container.has_next():
                container.next().close()
                container.remove()

    def _choice_connection_from_container(self, container, block, timeout):
        with container.condition:
            if container.cyclic_has_next():
                return container.next()
            raise RuntimeError("invalid connections_per_key")

    def _remove_connection_from_container(self, container, connection):
        with container.condition:
            try:
                container.remove_element(connection)
            except ValueError:
                pass

    def _release_connection_to_container(self, container, connection):
        pass

