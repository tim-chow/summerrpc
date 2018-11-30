# coding: utf8

import unittest

from summerrpc.transport import RecordTransport


class TestSingleton(unittest.TestCase):
    def testRecordTransport(self):
        rt1 = RecordTransport()
        rt2 = RecordTransport()
        self.assertTrue(rt1 is rt2)

