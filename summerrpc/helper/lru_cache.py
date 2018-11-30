# coding: utf8

"""
LRU Cache，基于LinkedHashMap实现
"""

__all__ = ["Entry", "LRUCache"]
__authors__ = ["Tim Chow"]


class Entry(object):
    def __init__(self, key, value):
        self._key = key
        self._value = value
        self._prev = None
        self._next = None

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key):
        self._key = key

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def prev(self):
        return self._prev

    @prev.setter
    def prev(self, prev):
        if not isinstance(prev, self.__class__):
            raise TypeError("expect %s, not %s" %
                            (self.__class__.__name__, type(prev).__name__))
        self._prev = prev

    @property
    def next(self):
        return self._next

    @next.setter
    def next(self, next_):
        if not isinstance(next_, self.__class__):
            raise TypeError("expect %s, not %s" %
                            (self.__class__.__name__, type(next_).__name__))
        self._next = next_

    def __str__(self):
        return "%s{key=%s, value=%s}" % \
            (self.__class__.__name__, self.key, self.value)

    __repr__ = __str__


class LRUCache(object):
    def __init__(self, max_size=None):
        # max_size应该大于0
        self._max_size = max(max_size or 65535, 1)
        self._head = Entry(None, None)
        self._head.prev = self._head
        self._head.next = self._head
        self.__map = {}

    @property
    def head(self):
        return self._head

    @head.setter
    def head(self, head):
        raise RuntimeError("head can not be overridden")

    def __change_pointer(self, entry):
        entry.prev.next = entry.next
        entry.next.prev = entry.prev
        entry.prev = self.head
        entry.next = self.head.next
        self.head.next.prev = entry
        self.head.next = entry

    def __setitem__(self, k, v):
        hash_code = hash(k)
        entry = self.__map.get(hash_code)
        if entry is not None:
            entry.key = k
            entry.value = v
            self.__change_pointer(entry)
            return

        if len(self.__map) >= self._max_size:
            entry = self.head.prev
            self.__map.pop(hash(entry.key))
            self.__map[hash_code] = entry
            entry.key = k
            entry.value = v
            self.__change_pointer(entry)
            return

        entry = Entry(k, v)
        entry.prev = self.head
        entry.next = self.head.next
        self.head.next.prev = entry
        self.head.next = entry

        self.__map[hash_code] = entry

    def __getitem__(self, k):
        hash_code = hash(k)
        entry = self.__map[hash_code]
        self.__change_pointer(entry)
        return entry.value

    def __delitem__(self, k):
        entry = self.__map.pop(hash(k))
        entry.prev.next = entry.next
        entry.next.prev = entry.prev

    def __contains__(self, k):
        return hash(k) in self.__map

    def clear(self):
        self.__map.clear()
        self.head.next = self.head
        self.head.prev = self.head

    @property
    def current_size(self):
        return len(self.__map)

    @property
    def max_size(self):
        return self._max_size

    def will_be_kicked_out(self):
        if self.current_size < self.max_size:
            return None
        return self.head.prev

    def iteritems(self):
        entry = self.head.prev
        while entry is not self.head:
            yield entry.key, entry.value
            entry = entry.prev
