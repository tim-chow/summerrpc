# coding: utf8

__all__ = ["Cluster", "AbstractCluster", "RandomCluster"]
__authors__ = ["Tim Chow"]

from abc import ABCMeta, abstractmethod
import random


class Cluster(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_remote(self, class_name, method_name, transport, serializer):
        pass


class AbstractCluster(Cluster):
    def __init__(self, registry):
        self._registry = registry

    def get_remote(self, class_name, method_name, transport, serializer):
        remotes = self._registry.get_remotes(
                        class_name,
                        method_name,
                        transport,
                        serializer)
        if len(remotes) == 0:
            return None

        # 按照负载均衡算法选择一个remote
        remote = self.choice_remote(remotes)
        return remote

    def close(self):
        self._registry.close()

    def choice_remote(self, remotes):
        raise NotImplementedError


class RandomCluster(AbstractCluster):
    def choice_remote(self, remotes):
        # 从remotes中随机选择一个
        return random.choice(remotes)

