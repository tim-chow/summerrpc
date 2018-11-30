import unittest

from summerrpc.helper.list import StaticList, ListFullError, ListEmptyError


class TestStaticList(unittest.TestCase):
    def testStaticList(self):
        static_list = StaticList(3)
        static_list.insert_left(1)
        static_list.insert_left(2)
        static_list.insert_left(3)
        self.assertRaises(ListFullError, static_list.insert_left, 4)
        self.assertEqual(static_list.size, 3)
        self.assertEqual(static_list.pop_left(), 3)
        self.assertEqual(static_list.size, 2)
        static_list.pop_left()
        static_list.pop_left()
        self.assertRaises(ListEmptyError, static_list.pop_left)
        static_list.insert_left(4)
        self.assertEqual(static_list.peek_left(), 4)
