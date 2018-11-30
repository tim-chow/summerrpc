import unittest

from summerrpc.connection_pool import (
    DedicateLRUConnectionPool,
    SharedLRUConnectionPool,
    get_connection_from_pool
)
from summerrpc.exception import NoAvailableConnectionError


class FakeConnection(object):
    def __init__(self):
        self.closed = False
        self.closing = False

    def close(self):
        pass


class TestConnectionPool(unittest.TestCase):
    def testDedicateLRUConnectionPool(self):
        pool = DedicateLRUConnectionPool(1, 2)
        connection_factory = lambda : FakeConnection()
        key = "1"
        print("===testDedicateLRUConnectionPool===")
        conn1 = pool.get_connection(key, connection_factory, True, None)
        print("conn1: %s" % conn1)
        conn2 = pool.get_connection(key, connection_factory, True, None)
        print("conn2: %s" % conn2)
        try:
            conn3 = pool.get_connection(key, connection_factory, False, None)
            raise RuntimeError("unreachable")
        except NoAvailableConnectionError:
            print("NoAvailableConnectionError")
        pool.release_connection(key, conn1)
        conn3 = pool.get_connection(key, connection_factory, True, None)
        print("conn3: %s" % conn3)
        print("===testDedicateLRUConnectionPool===")
        self.assertTrue(conn1 == conn3)
        pool.close()

    def testSharedLRUConnectionPool(self):
        pool = SharedLRUConnectionPool(1, 2)
        connection_factory = lambda : FakeConnection()
        key = "2"
        print("===testSharedLRUConnectionPool===")
        conn1 = pool.get_connection(key, connection_factory)
        print("conn1: %s" % conn1)
        conn2 = pool.get_connection(key, connection_factory)
        print("conn2: %s" % conn2)
        print("===testSharedLRUConnectionPool===")
        conn3 = pool.get_connection(key, connection_factory)
        self.assertTrue(conn1 == conn3)
        pool.close()

    def testContextManager(self):
        pool = DedicateLRUConnectionPool(1, 1)
        connection_factory = lambda : FakeConnection()
        key = "3"
        print("===testContextManager===")
        with get_connection_from_pool(pool, key, connection_factory) as conn1:
            print("conn1: %s" % conn1)
        with get_connection_from_pool(pool, key, connection_factory) as conn2:
            print("conn2: %s" % conn2)
        with get_connection_from_pool(pool, key, connection_factory) as conn3:
            print("conn3: %s" % conn3)
        print("===testContextManager===")
        self.assertTrue(conn1 is conn2 and conn2 is conn3)
        pool.close()

    def testClosedSharedConnection(self):
        pool = SharedLRUConnectionPool(1, 1)
        connection_factory = lambda : FakeConnection()
        key = "4"
        print("===testClosedSharedConnection===")
        conn1 = pool.get_connection(key, connection_factory)
        print("conn1: %s" % conn1)
        conn2 = pool.get_connection(key, connection_factory)
        print("conn2: %s" % conn2)
        self.assertTrue(conn1 is conn2)
        conn1.closed = True
        conn3 = pool.get_connection(key, connection_factory)
        print("conn3: %s" % conn3)
        self.assertTrue(conn3 is not conn1)
        print("===testClosedSharedConnection===")
        pool.close()

    def testClosedDedicateConnection(self):
        pool = DedicateLRUConnectionPool(1, 1)
        connection_factory = lambda : FakeConnection()
        key = "4"
        print("===testClosedDedicateConnection===")
        with get_connection_from_pool(pool, key, connection_factory) as conn1:
            print("conn1: %s" % conn1)
        with get_connection_from_pool(pool, key, connection_factory) as conn2:
            print("conn2: %s" % conn2)
        self.assertTrue(conn1 is conn2)
        conn1.closed = True
        with get_connection_from_pool(pool, key, connection_factory) as conn3:
            print("conn3: %s" % conn3)
            self.assertTrue(conn3 is not conn1)
        print("===testClosedDedicateConnection===")
        pool.close()

