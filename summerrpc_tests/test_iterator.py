import unittest

from summerrpc.helper import Iterator


class TestIterator(unittest.TestCase):
    def testIterator(self):
        lst = range(10)
        it = Iterator(lst)
        removed = []
        while it.has_next():
            ele = it.next()
            if ele % 2 == 0:
                removed.append(it.remove())

        self.assertTrue(lst == range(1, 10, 2))
        self.assertTrue(removed == range(0, 10, 2))

