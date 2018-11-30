# coding: utf8

__all__ = ["HTTPTransport", "HTTPRequest", "HTTPUtility",
    "Stage", "HTTPResponseParser", "SimpleBlockingHTTPTransport"]
__authors__ = ["Tim Chow"]

import logging

import tornado.gen as gen
from tornado.web import RequestHandler
from tornado.iostream import UnsatisfiableReadError
from ..transport import Transport, BlockingSocketUtility
from ..exception import InvalidPacketError

LOGGER = logging.getLogger(__name__)


class HTTPRequest(object):
    def __init__(self):
        self._request_method = None
        self._request_uri = None
        self._http_version = None
        self._headers = {}
        self._body = None

    @property
    def request_method(self):
        return self._request_method

    @request_method.setter
    def request_method(self, request_method):
        self._request_method = request_method

    @property
    def request_uri(self):
        return self._request_uri

    @request_uri.setter
    def request_uri(self, request_uri):
        self._request_uri = request_uri

    @property
    def http_version(self):
        return self._http_version

    @http_version.setter
    def http_version(self, http_version):
        self._http_version = http_version

    def add_header(self, header_name, header_value):
        self._headers[header_name] = header_value

    def get_header(self, header_name, default=None):
        return self._headers.get(header_name, default)

    @property
    def headers(self):
        return self._headers

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, body):
        self._body = body

    def __str__(self):
        return ("%s{method=%s, request_uri=%s, version=%s, "
                    "headers=%s, body=%s}") % (
                        self.__class__.__name__,
                        self._request_method,
                        self._request_uri,
                        self._http_version,
                        self._headers,
                        self._body)


class HTTPUtility(object):
    @staticmethod
    def parse_request_line(request_line):
        if request_line.endswith("\r\n"):
            request_line = request_line[:-2]
        items = request_line.split(" ", 2)
        if len(items) != 3:
            return None

        request_method = items[0]
        if request_method not in RequestHandler.SUPPORTED_METHODS:
            return None

        request_uri = items[1]

        version = items[2]
        items = version.split("/", 1)
        if len(items) != 2:
            return None
        if items[0].lower() != "http":
            return None
        if items[1] not in ["0.9", "1.0", "1.1"]:
            return None

        return request_method, request_uri, float(items[1])

    @staticmethod
    def parse_header(header_string):
        if header_string.endswith("\r\n"):
            header_string = header_string[:-2]
        pair = header_string.split(":", 1)
        if len(pair) != 2:
            return None
        return pair[0].strip(), pair[1].strip()

    @staticmethod
    def parse_response_line(response_line):
        if response_line.endswith("\r\n"):
            response_line = response_line[:-2]
        items = response_line.split()
        if len(items) != 3:
            return None
        protocol_and_version = items[0].split("/")
        if len(protocol_and_version) != 2:
            return None
        if protocol_and_version[0].upper() != "HTTP":
            return None
        if protocol_and_version[1] not in ["0.9", "1.0", "1.1"]:
            return None
        if not items[1].isdigit():
            return None
        return protocol_and_version[0], \
            float(protocol_and_version[1]), \
            int(items[1]), \
            items[2]


class BaseHTTPTransport(Transport):
    def get_name(self):
        return "http"


class HTTPTransport(BaseHTTPTransport):
    def __init__(self, max_request_line_length=2048,
                max_header_length=1024,
                max_header_count=128):
        self._max_request_line_length = max_request_line_length
        self._max_header_length = max_header_length
        self._max_header_count = max_header_count

    @gen.coroutine
    def read(self, stream, ignore_timeout=True):
        request = HTTPRequest()

        # 请求行
        request_line = yield stream.read_until("\r\n",
            max_bytes=self._max_request_line_length)
        ret = HTTPUtility.parse_request_line(request_line)
        if ret is None:
            raise UnsatisfiableReadError
        request.request_method, request.request_uri, request.http_version = ret

        # 请求头
        for _ in range(self._max_header_count):
            header = yield stream.read_until("\r\n",
                max_bytes=self._max_header_length)
            if header == "\r\n":
                LOGGER.debug("received all headers")
                LOGGER.debug("headers are: %s" % request.headers)
                break
            header = HTTPUtility.parse_header(header)
            if header is not None:
                request.add_header(header[0], header[1])
        else:
            raise UnsatisfiableReadError

        # 请求头中必须包含Transaction-Id，且必须是整型
        transaction_id = request.headers.get("Transaction-Id")
        if not transaction_id or not transaction_id.isalnum():
            LOGGER.error("Transaction-Id not found in headers or invalid")
            raise UnsatisfiableReadError
        transaction_id = int(transaction_id)

        # 请求头中必须包含Content-Length
        content_length = request.headers.get("Content-Length")
        if not content_length or not content_length.isalnum():
            LOGGER.error("Content-Length not found in headers or invalid")
            raise UnsatisfiableReadError
        content_length = int(content_length)

        # 读取请求体
        if content_length > 0:
            body = yield stream.read_bytes(content_length)
        else:
            body = None
        request.body = body

        LOGGER.debug(request)
        raise gen.Return((transaction_id, body))

    def generate_packet(self, transaction_id, buff):
        return "HTTP/1.1 200 OK\r\n" + \
                ("Transaction-Id: %d\r\n" % transaction_id) + \
                ("Content-Length: %d\r\n" % len(buff)) + \
                "\r\n" + \
                buff

    @gen.coroutine
    def write(self, stream, transaction_id, buff):
        data = self.generate_packet(transaction_id, buff)
        yield stream.write(data)


class Stage(object):
    UNCOMPLETE_PHRASE = 0
    PARSE_RESPONSE_LINE = 1
    PARSE_HEADERS = 2
    PARSE_CONTENT = 3
    FINISHED = 4


class HTTPResponseParser(object):
    def __init__(self):
        self._buffer = bytearray()
        self._initialize()

    def _initialize(self):
        self._stage = Stage.PARSE_RESPONSE_LINE
        self.protocol = None
        self.version = None
        self.status = None
        self.message = None
        self.headers = {}
        self.content_length = 0
        self.content = None

    def feed(self, data):
        self._buffer.extend(data)

    def consume_by_delimiter(self, delimiter, count=1):
        assert count > 0, "count should be more than zero"
        start = 0
        for _ in range(count):
            position = self._buffer.find(delimiter, start)
            if position == -1:
                raise RuntimeError("unreachable")
            start = position + len(delimiter)
        mm = memoryview(self._buffer)
        self._buffer = bytearray(mm[position+len(delimiter):])
        return mm[:position+len(delimiter)].tobytes()

    def consume(self, num):
        mm = memoryview(self._buffer)
        self._buffer = bytearray(mm[num:])
        return mm[:num].tobytes()

    def get(self):
        if self._stage == Stage.PARSE_RESPONSE_LINE:
            count = self._buffer.count("\r\n")
            if count < 1:
                return Stage.UNCOMPLETE_PHRASE

            response_line = self.consume_by_delimiter("\r\n", 1)
            ret = HTTPUtility.parse_response_line(response_line)
            if ret is None:
                raise InvalidPacketError(
                    "response line: %s" % response_line)
            self.protocol, self.version, self.status, self.message = ret
            self._stage = Stage.PARSE_HEADERS
            return self._stage

        if self._stage == Stage.PARSE_HEADERS:
            count = self._buffer.count("\r\n")
            if count < 1:
                return Stage.UNCOMPLETE_PHRASE

            header_string = self.consume_by_delimiter("\r\n", 1)
            if header_string == "\r\n":
                if "Content-Length" not in self.headers:
                    self._stage = Stage.FINISHED
                    return self._stage
                content_length_string = self.headers["Content-Length"]
                if not content_length_string.isdigit():
                    raise InvalidPacketError("invalid content length")
                self.content_length = int(content_length_string)
                self._stage = Stage.PARSE_CONTENT
                return self._stage

            ret = HTTPUtility.parse_header(header_string)
            if ret is None:
                raise InvalidPacketError("header string: %s" % header_string)
            self.headers[ret[0]] = ret[1]
            return self._stage

        if self._stage == Stage.PARSE_CONTENT:
            if len(self._buffer) < self.content_length:
                return Stage.UNCOMPLETE_PHRASE

            self.content = self.consume(self.content_length)
            self._stage = Stage.FINISHED
            return self._stage

        if self._stage == Stage.FINISHED:
            return self._stage

    def auto_get(self):
        status = self.get()
        while status != Stage.UNCOMPLETE_PHRASE and \
                status != Stage.FINISHED:
            status = self.get()

    def is_finished(self):
        return self._stage == Stage.FINISHED

    def reset_states(self):
        self._initialize()


class SimpleBlockingHTTPTransport(BaseHTTPTransport):
    def __init__(self, chunk_size=1024):
        self._chunk_size = chunk_size

    def read(self, sock, ignore_timeout=False):
        parser = HTTPResponseParser()
        while not parser.is_finished():
            data = sock.recv(self._chunk_size)
            parser.feed(data)
            parser.auto_get()

        transaction_id = parser.headers.get("Transaction-Id")
        content = parser.content 
        parser.reset_states()
        if transaction_id is None or content is None:
            raise InvalidPacketError("invalid transaction_id or content")
        return int(transaction_id), content

    def generate_packet(self, transaction_id, buff):
        return "GET / HTTP/1.1\r\n" + \
            ("Transaction-Id: %d\r\n" % transaction_id) + \
            ("Content-Length: %d\r\n" % len(buff)) + \
            ("User-Agent: %s\r\n" % self.__class__.__name__) + \
            "\r\n" + \
            buff

    def write(self, sock, transaction_id, buff):
        BlockingSocketUtility.write_data(
            sock,
            self.generate_packet(transaction_id, buff))

