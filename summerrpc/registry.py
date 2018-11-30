# coding: utf8

__all__ = ["RegisterEntrySet", "Registry", "ZookeeperRegistry"]
__authors__ = ["Tim Chow"]

from abc import ABCMeta, abstractmethod
from urllib import unquote
from urlparse import urlparse
import logging
import traceback

import zookeeper

from .helper import (
            SafeDict,
            parse_query)

LOGGER = logging.getLogger(__name__)


class RegisterEntrySet(object):
    def __init__(self):
        self.__map = {}

    def with_entry(self, path, data):
        self.__map[path] = data
        return self

    def iter_entry(self):
        for k, v in self.__map.iteritems():
            yield k, v


class Registry(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def register(self, register_entry_set, delete_if_exists):
        pass

    @abstractmethod
    def discovery(self):
        pass

    @abstractmethod
    def get_remotes(self, class_name, method_name, transport, serializer):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def discovery_successfully(self):
        pass


class ZookeeperRegistry(Registry):
    def __init__(self, hosts, base_znode, retry_policy=None,
                 log_level=zookeeper.LOG_LEVEL_ERROR):
        # 合法的znode名称是：以/开头，除了根znode，其他znode不能以/结尾
        if not isinstance(base_znode, str) or \
                not base_znode.startswith("/") or \
                (base_znode != "/" and base_znode.endswith("/")):
            raise RuntimeError("invalid base_znode")
        self._base_znode = base_znode
        self._hosts = hosts
        zookeeper.set_debug_level(log_level)

        self._register_handler = None
        self._register_entry_set = None
        self._delete_if_exists = True

        self._discovery_handler = None
        self._local_cache = SafeDict()

    def register(self, register_entry_set, delete_if_exists=True):
        if not isinstance(register_entry_set, RegisterEntrySet):
            raise TypeError("expect RegisterEntrySet, not %s" %
                            type(register_entry_set).__name__)
        if self._register_handler is not None:
            raise RuntimeError("register already started")

        self._register_entry_set = register_entry_set
        self._delete_if_exists = delete_if_exists
        self._initialize_register()

    def _initialize_register(self):
        if self._register_handler is None:
            self._register_handler = zookeeper.init(self._hosts,
                                                    self._register_watcher)

    def _register_watcher(self, handler, type, state, path):
        LOGGER.info("register_handler state is: %d" % state)
        zookeeper.set_watcher(
            self._register_handler,
            self._register_watcher)

        # 连接或重连成功
        if state == zookeeper.CONNECTED_STATE:
            LOGGER.info("register_handler: connect or reconnect successfully")
            self._real_register()

    def _real_register(self):
        for znode, data in self._register_entry_set.iter_entry():
            if self._base_znode == "/":
                znode = "/%s" % znode
            else:
                znode = "%s/%s" % (self._base_znode, znode)

            while True:
                try:
                    zookeeper.create(
                        self._register_handler,
                        znode,
                        data,
                        # 权限
                        [{"perms": 0x1f, "scheme": "world", "id": "anyone"}],
                        # 节点类型
                        zookeeper.EPHEMERAL)
                    LOGGER.info("create znode: %s successfully" % znode)
                    break
                except zookeeper.NodeExistsException:
                    if self._delete_if_exists:
                        LOGGER.info("%s already exists, delete it anyway" % znode)
                        try:
                            zookeeper.delete(
                                self._register_handler,
                                znode)
                        except zookeeper.NoNodeException:
                            pass
                        continue
                    raise

    def discovery(self):
        if self._discovery_handler is not None:
            raise RuntimeError("discovery already started")
        self._initialize_discovery()

    def _initialize_discovery(self):
        if self._discovery_handler is None:
            self._discovery_handler = zookeeper.init(self._hosts,
                                                     self._discovery_watcher)

    def _discovery_watcher(self, handler, type, state, path):
        LOGGER.info("discovery_handler state is: %d" % state)
        zookeeper.set_watcher(
            self._discovery_handler,
            self._discovery_watcher)

        # 连接或重连成功
        if state == zookeeper.CONNECTED_STATE:
            LOGGER.info("discovery_handler: connect or reconnect successfully")
            self._real_discovery(
                    handler,
                    type,
                    state,
                    self._base_znode)

    def _real_discovery(self, handler, type, state, path):
        children = zookeeper.get_children(
            handler,
            path,
            self._real_discovery)

        temp_cache = SafeDict()
        for child in children:
            url = urlparse(unquote(child))
            query = parse_query(url.query)
            if "serializer" not in query:
                continue
            serializer = query["serializer"][0]

            netloc = url.netloc.split(":", 1)
            if len(netloc) != 2:
                continue
            host = netloc[0]
            port = int(netloc[1])

            k = (url.scheme, url.path, serializer)
            v = (host, port)
            temp_cache.setdefault(k, []).append(v)
        self._local_cache = temp_cache
        LOGGER.info("local_cache is: %s", self._local_cache)

    def get_remotes(self, class_name, method_name, transport, serializer):
        k = (transport, "/%s/%s" % (class_name, method_name), serializer)
        return self._local_cache.get(k, [])

    def close(self):
        LOGGER.info("close ZookeeperRegistry")
        try:
            if self._register_handler is not None:
                zookeeper.close(self._register_handler)
        except BaseException:
            traceback.print_exc()

        try:
            if self._discovery_handler is not None:
                zookeeper.close(self._discovery_handler)
        except BaseException:
            traceback.print_exc()

        self._register_handler = None
        self._discovery_handler = None
        self._local_cache.clear()

    def discovery_successfully(self):
        return len(self._local_cache) > 0
