import unittest

from summerrpc.helper.lru_cache import LRUCache


class TestLRUCache(unittest.TestCase):
    def testIterItems(self):
        lst = [(1, 1), (2, 2), (3, 3), (4, 4)]
        cache = LRUCache(len(lst))

        for pair in lst:
            cache[pair[0]] = pair[1]

        self.assertEqual(list(cache.iteritems()), lst)
        self.assertEqual(cache.current_size, len(lst))
