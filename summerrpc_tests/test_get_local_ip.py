import unittest

from summerrpc.helper import get_local_ip


class TestGetLocalIp(unittest.TestCase):
    def testGetLocalIp(self):
        for ip in get_local_ip(["lo", "eth0", "eth1"]):
            print("ip = %s" % ip)

