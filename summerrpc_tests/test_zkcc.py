import unittest
import time

from summerrpc.configuration_center import ZookeeperConfigurationCenter

class TestZookeeperConfigurationCenter(unittest.TestCase):
    def setUp(self):
        self._zkcc = ZookeeperConfigurationCenter(
            "10.22.1.194:2181,"
            "10.22.1.194:2182,"
            "10.22.1.194:2183,"
            "10.22.1.194:2184",
            "/summerrpc_configuration")

    def testZkcc(self):
        with self._zkcc:
            time.sleep(1.5)

