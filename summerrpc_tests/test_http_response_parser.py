import unittest

from summerrpc.extension.http_transport import (
    HTTPResponseParser,
    Stage)


class TestHTTPResponseParser(unittest.TestCase):
    def testHTTPResponseParser(self):
        parser = HTTPResponseParser()
        parser.feed("HTTP/1.1 200 ")
        self.assertTrue(parser.get() == Stage.UNCOMPLETE_PHRASE)
        parser.feed("OK\r\n")
        self.assertTrue(parser.get() == Stage.PARSE_HEADERS)
        parser.feed("Content-Length: 5\r\n")
        self.assertTrue(parser.get() == Stage.PARSE_HEADERS)
        parser.feed("\r\n")
        self.assertTrue(parser.get() == Stage.PARSE_CONTENT)
        parser.feed("1")
        self.assertTrue(parser.get() == Stage.UNCOMPLETE_PHRASE)
        parser.feed("2345")
        self.assertTrue(parser.get() == Stage.FINISHED)
        self.assertTrue(parser.content == "12345")

    def testAutoGet(self):
        data = "HTTP/1.1 200 OK\r\nContent-Length: 1\r\n\r\n1"
        parser = HTTPResponseParser()
        parser.feed(data)
        parser.auto_get()
        self.assertTrue(parser.is_finished())

