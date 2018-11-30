import unittest
import socket

from summerrpc.helper import ServerSocketBuilder


class TestServerSocket(unittest.TestCase):
    def setUp(self):
        self._server_socket = ServerSocketBuilder() \
                                .with_host("127.0.0.1") \
                                .with_port(0) \
                                .with_timeout(1) \
                                .with_blocking() \
                                .build()

    def tearDown(self):
        self._server_socket.close()

    def testAccept(self):
        host, port = self._server_socket.getsockname()
        print("host='{0}', port='{1}'".format(host, port))

        self.assertRaises(socket.timeout, self._server_socket.accept)
