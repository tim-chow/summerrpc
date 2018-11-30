# coding: utf8

__all__ = ["ZookeeperConfigurationCenter"]
__authors__ = ["Tim Chow"] 

import logging
import zookeeper
from .interface import ConfigurationCenter

LOGGER = logging.getLogger(__name__)


class ZookeeperConfigurationCenter(ConfigurationCenter):
    def __init__(self, hosts, base_znode, log_level=zookeeper.LOG_LEVEL_ERROR):
        self._hosts = hosts
        self._base_znode = base_znode
        zookeeper.set_debug_level(log_level)
        self._handler = None
        self._local_cache = None
        self._main_version = None

    def start(self):
        if self._handler is None:
            self._handler = zookeeper.init(
                self._hosts,
                self._connection_state_watcher)
            LOGGER.info("create zookeeper client successfully, "
                "handler is: %s" % self._handler)

    def _connection_state_watcher(self, handler, type_, state, path):
        LOGGER.info("connection state is: %s" % state)
        zookeeper.set_watcher(
            handler,
            self._connection_state_watcher)

        # 连接或重连成功
        if state == zookeeper.CONNECTED_STATE:
            LOGGER.info("connect or reconnect successfully, "
                "handler is: %s" % handler)
            # 拉取配置
            self._real_start(handler, type_, state, self._base_znode)

    def _real_start(self, handler, type_, state, path):
        znode = zookeeper.get(handler, path, self._real_start)
        main_version = znode[1]["version"]
        LOGGER.info("main version is: %s" % main_version)

        tmp_cache = {}
        children = zookeeper.get_children(handler, path)
        for child in children:
            znode = zookeeper.get(handler, path + "/" + child)
            tmp_cache[child] = znode[0]
            LOGGER.info("key=%s, value=%s, version=%s" %
                (child, znode[0], znode[1]["version"]))
        self._local_cache = tmp_cache
        self._main_version = main_version

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_typ, exc_val, exc_tb):
        self.close()

    def close(self):
        if self._handler is not None:
            try:
                zookeeper.close(self._handler)
            finally:
                self._handler = None

    def get_key(self, key):
        return self._local_cache.get(key)

    @property
    def success(self):
        return self._local_cache is not None

    @property
    def main_version(self):
        return self._main_version

    def iteritems(self):
        if self._local_cache is None:
            raise RuntimeError

        for k, v in self._local_cache.iteritems():
            yield k, v

