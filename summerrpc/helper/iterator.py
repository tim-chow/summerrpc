# coding: utf8

import threading

__all__ = ["Iterator", "CyclicIterator"]
__authors__ = ["Tim Chow"]


class Iterator(object):
    def __init__(self, it):
        self._it = it
        self._cursor = 0
        self._condition = threading.Condition()

    def has_next(self):
        return self._cursor < len(self._it)

    def next(self):
        try:
            return self._it[self._cursor]
        finally:
            self._cursor = self._cursor + 1

    def remove(self):
        try:
            return self._it.pop(self._cursor - 1)
        finally:
            self._cursor = self._cursor - 1

    def append(self, element):
        self._it.append(element)

    def size(self):
        return len(self._it)

    def rewind(self):
        self._cursor = 0

    @property
    def cursor(self):
        return self._cursor

    @property
    def condition(self):
        return self._condition

    def remove_element(self, element):
        # 可能抛出ValueError
        index = self._it.index(element)
        self._it.pop(index)
        if self._cursor > index:
            self._cursor = self._cursor - 1


class CyclicIterator(Iterator):
    def cyclic_has_next(self):
        if not Iterator.has_next(self):
            self.rewind()
        return Iterator.has_next(self)

