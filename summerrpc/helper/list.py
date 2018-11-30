# coding: utf8

__all__ = ["ListFullError", "ListEmptyError", "List", "Node", "StaticList"]
__authors__ = ["Tim Chow"]

from abc import ABCMeta, abstractmethod


class ListFullError(StandardError):
    pass


class ListEmptyError(StandardError):
    pass


class List(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def insert_left(self, element):
        pass

    @abstractmethod
    def append(self, element):
        pass

    @abstractmethod
    def pop_left(self):
        pass

    @abstractmethod
    def pop_right(self):
        pass

    @abstractmethod
    def is_full(self):
        pass

    @abstractmethod
    def peek_left(self):
        pass


class Node(object):
    def __init__(self, element=None, next_=-1):
        self._element = element
        self._next = next_

    @property
    def element(self):
        return self._element

    @element.setter
    def element(self, element):
        self._element = element

    @property
    def next(self):
        return self._next

    @next.setter
    def next(self, next_):
        self._next = next_


class StaticList(List):
    def __init__(self, max_size):
        assert max_size > 0, "max size should be more than 0"
        self._nodes = [Node() for _ in range(max_size)]
        self._head = Node()
        self._space = Node()
        self._current_size = 0

        self._space.next = 0
        for ind in range(max_size-1):
            self._nodes[ind].next = ind + 1

    def insert_left(self, element):
        # 申请node
        node_index = self._space.next
        if node_index == -1:
            raise ListFullError("list is full")
        node = self._nodes[node_index]
        self._space.next = node.next

        node.element = element
        self._current_size = self._current_size + 1

        node.next = self._head.next
        self._head.next = node_index

    def pop_left(self):
        if self._current_size <= 0:
            raise ListEmptyError("list is empty")

        node_index = self._head.next
        node = self._nodes[node_index]
        try:
            return node.element
        finally:
            self._head.next = node.next
            self._current_size = self._current_size - 1
            # 回收node
            node.next = self._space.next
            self._space.next = node_index

    def peek_left(self):
        if self._current_size <= 0:
            raise ListEmptyError("list is empty")

        return self._nodes[self._head.next].element

    def pop_right(self):
        raise NotImplementedError("not implemented now")

    def append(self, element):
        raise NotImplementedError("not implemented now")

    @property
    def size(self):
        return self._current_size

    @size.setter
    def size(self, size):
        raise RuntimeError("can not override size")

    def is_full(self):
        return self._space.next is None
