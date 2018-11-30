# coding: utf8

__all__ = ["RpcServerBuilder", "RpcServer", "Runner"]
__authors__ = ["Tim Chow"]

from .rpc_server_imports import *

LOGGER = logging.getLogger(__name__)


class RpcServerBuilder(object):
    def __init__(self):
        # ServerSocket必须是非阻塞的
        self._server_socket = None
        self._exporter = None
        self._transport = RecordTransport()
        self._serializer = PickleSerializer()
        # 最大并发连接数
        self._max_connections = 15000
        # 每个连接并发处理的请求数量
        self._concurrent_request_per_connection = 10
        # 内存buffer的最大大小，默认是100M
        self._max_buffer_size = 100 * 1024 * 1024
        self._ioloop = IOLoop.current()
        # 线程池的大小，默认是CPU数量的2倍加1
        self._thread_pool_size = 2 * multiprocessing.cpu_count() + 1
        # 进程池的大小，默认是None，也就是不会开启进程池
        self._process_pool_size = None
        # 连接的最大空闲时间
        self._max_idle_time = 8 * 60 * 60
        self._registry = None

    def with_server_socket(self, server_socket):
        if not isinstance(server_socket, ServerSocket):
            raise TypeError("expect ServerSocket, not %s" %
                            type(server_socket).__name__)
        if server_socket.gettimeout() != 0.0:
            raise RuntimeError("server_socket must be non-blocking")
        self._server_socket = server_socket
        return self

    def with_exporter(self, exporter):
        if not isinstance(exporter, Exporter):
            raise TypeError("expect Exporter, not %s" %
                            type(exporter).__name__)
        self._exporter = exporter
        return self

    def with_transport(self, transport):
        if not isinstance(transport, Transport):
            raise TypeError("expect Transport, not %s" %
                            type(transport).__name__)
        self._transport = transport
        return self

    def with_serializer(self, serializer):
        if not isinstance(serializer, Serializer):
            raise TypeError("expect Serializer, not %s" %
                            type(serializer).__name__)
        self._serializer = serializer
        return self

    def with_max_connections(self, max_connections):
        if not isinstance(max_connections, int):
            raise TypeError("expect int, not %s" %
                            type(max_connections).__name__)
        if max_connections <= 0:
            raise ValueError("max_connections should be more than 0")
        self._max_connections = max_connections
        return self

    def with_concurrent_request_per_connection(self, crpc):
        if not isinstance(crpc, int):
            raise TypeError("expect int, not %s" % type(crpc).__name__)
        if crpc <= 0:
            raise ValueError("concurrent_request_per_connection"
                             " should be more than 0")
        self._concurrent_request_per_connection = crpc
        return self

    def with_max_buffer_size(self, max_buffer_size):
        if not isinstance(max_buffer_size, int):
            raise TypeError("expect int, not %s" % type(max_buffer_size).__name__)
        if max_buffer_size <= 0:
            raise ValueError("max_buffer_size should be more than 0")
        self._max_buffer_size = max_buffer_size
        return self

    def with_ioloop(self, ioloop):
        if not isinstance(ioloop, IOLoop):
            raise TypeError("expect IOLoop, not %s" % type(ioloop).__name__)
        self._ioloop = ioloop
        return self

    def with_thread_pool_size(self, size):
        # size为None表示不创建线程池
        if not isinstance(size, (int, types.NoneType)):
            raise TypeError("expect int or None, not %s" % type(size).__name__)
        if size is not None and size <= 0:
            raise ValueError("thread_pool_size should be more than 0")
        self._thread_pool_size = size
        return self

    def with_process_pool_size(self, size):
        if not isinstance(size, int):
            raise TypeError("expect int, not %s" % type(size).__name__)
        if size <= 0:
            raise ValueError("process_pool_size should be more than 0")
        self._process_pool_size = size
        return self

    def with_max_idle_time(self, max_idle_time):
        if not isinstance(max_idle_time, int):
            raise TypeError("expect int, not %s" % type(max_idle_time).__name__)
        if max_idle_time <= 0:
            raise ValueError("max_idle_time should be more than 0")
        self._max_idle_time = max_idle_time
        return self

    def with_registry(self, registry):
        if not isinstance(registry, Registry):
            raise TypeError("expect Registry, not %s" % type(registry).__name__)
        self._registry = registry
        return self

    @property
    def server_socket(self):
        return self._server_socket

    @property
    def exporter(self):
        return self._exporter

    @property
    def transport(self):
        return self._transport

    @property
    def serializer(self):
        return self._serializer

    @property
    def max_connections(self):
        return self._max_connections

    @property
    def concurrent_request_per_connection(self):
        return self._concurrent_request_per_connection

    @property
    def max_buffer_size(self):
        return self._max_buffer_size

    @property
    def ioloop(self):
        return self._ioloop

    @property
    def thread_pool_size(self):
        return self._thread_pool_size

    @property
    def process_pool_size(self):
        return self._process_pool_size

    @property
    def max_idle_time(self):
        return self._max_idle_time

    @property
    def registry(self):
        return self._registry

    def build(self):
        if self.server_socket is None or self.exporter is None:
            raise RuntimeError(
                "server socket and exporter must be provided")
        return RpcServer(self.max_connections,
                         self.max_buffer_size,
                         self.ioloop,
                         self.server_socket,
                         self.thread_pool_size,
                         self.process_pool_size,
                         self.transport,
                         self.serializer,
                         self.exporter,
                         self.concurrent_request_per_connection,
                         self.max_idle_time,
                         self.registry)


class RpcServer(object):
    def __init__(self, max_connections, max_buffer_size,
                 ioloop, server_socket, thread_pool_size,
                 process_pool_size,
                 transport, serializer, exporter,
                 concurrent_request_per_connection,
                 max_idle_time, registry):
        # 当前的并发连接数
        self._current_connections = 0
        # 最大并发连接数
        self._max_connections = max_connections
        # 保存当前连接信息的缓存
        self._connection_lru_cache = LRUCache(max_connections)

        self._ioloop = ioloop
        self._server_socket = server_socket
        self._max_buffer_size = max_buffer_size

        self._thread_pool_size = thread_pool_size
        self._process_pool_size = process_pool_size
        # 线程池对象
        self._thread_pool = None
        # 进程池对象
        self._process_pool = None

        self._transport = transport
        self._serializer = serializer
        self._exporter = exporter
        self._registry = registry

        self._concurrent_request_per_connection = concurrent_request_per_connection
        self._max_idle_time = max_idle_time

        self._started = False
        self._starting = False
        self._closed = False
        self._closing = False
        self._start_stop_lock = threading.Lock()

        self._id_generator = partial(AtomicInteger(0).increase, 1)

    @property
    def started(self):
        return self._started

    @property
    def starting(self):
        return self._starting

    @property
    def closed(self):
        return self._closed

    @property
    def closing(self):
        return self._closing

    def _on_connection_close(self, connection_id, remote_address):
        LOGGER.debug("disconnect from: %s" % str(remote_address))
        self._current_connections = max(self._current_connections - 1, 0)
        LOGGER.debug("current connections: %d" % self._current_connections)
        connection_information = self._connection_lru_cache[connection_id]
        connection_information.stream_closed = True
        LOGGER.debug("notify read condition of id: %s" % connection_id)
        connection_information.read_condition.notify_all()
        LOGGER.debug("remove connection id: %d from connections" % connection_id)
        del self._connection_lru_cache[connection_id]

    def _accept_connection(self, server_socket, fd, events):
        # “抱住”server_socket，防止在边缘触发时，
        # + 同时进入大量连接，无法及时accept
        while True:
            # 当前并发连接数达到设置的最大值时，不再接受连接
            if self._current_connections >= self._max_connections:
                LOGGER.info("max connections reached, "
                            "current connections: %d" % self._current_connections)
                return

            try:
                sock, remote_address = server_socket.accept()
            except socket.error as ex:
                if ex.errno in EWOULDBLOCK:
                    break
                raise
            else:
                sock.setblocking(False)
                self._current_connections = self._current_connections + 1
                stream = IOStream(sock, max_buffer_size=self._max_buffer_size)
                connection_id = self._id_generator()
                stream.set_close_callback(partial(self._on_connection_close,
                    connection_id, remote_address))
                connection_information = ConnectionInformation(
                                            stream,
                                            self._ioloop.time(),
                                            Condition())
                self._connection_lru_cache[connection_id] = connection_information
                Runner(connection_information,
                       remote_address,
                       self._transport,
                       self._serializer,
                       self._exporter,
                       self._thread_pool,
                       self._process_pool,
                       self._ioloop,
                       self._concurrent_request_per_connection)

    def _close_inactive_connections(self):
        """关闭不活跃连接"""
        when = self._max_idle_time

        for connection_id, info in self._connection_lru_cache.iteritems():
            current_time = self._ioloop.time()
            if current_time - info.timestamp < self._max_idle_time:
                when = info.timestamp + self._max_idle_time - self._ioloop.time()
                when = max(when, 0)
                break

            LOGGER.info("closing inactive connection, id: %d" % connection_id)
            if not info.stream.closed():
                info.stream.close()
            info.read_condition.notify_all()

        LOGGER.debug("invoke _close_inactive_connections after %f" % when)
        self._ioloop.call_later(when, self._close_inactive_connections)

    def _register_if_necessary(self):
        if self._registry is None:
            LOGGER.info("registry is not provided")
            return

        LOGGER.info("begin to register")
        # 获取服务端的ip和port
        host, port = self._server_socket.getsockname()
        res = RegisterEntrySet()
        for class_name, method_name, _ in self._exporter.iter_method():
            register_url = URLBuilder() \
                    .with_scheme(self._transport.get_name()) \
                    .with_host(host) \
                    .with_port(port) \
                    .with_path("/%s/%s" % (class_name, method_name)) \
                    .with_argument("serializer", self._serializer.get_name()) \
                    .with_argument("max_buffer_size", str(self._max_buffer_size)) \
                    .build(quote_url=True)
            res.with_entry(register_url, '{"pid": %d}' % os.getpid())
        self._registry.register(res, True)
        LOGGER.info("register end")

    def can_start(self):
        if self._starting:
            LOGGER.info("starting")
            return False
        elif self._started:
            LOGGER.info("started")
            return False
        elif self._closing:
            LOGGER.info("closing")
            return False
        else:
            return True

    def start(self):
        if not self.can_start():
            return

        with self._start_stop_lock:
            if not self.can_start():
                return
            self._starting = True
            self._started = False
            self._closed = False

        # 初始化工作线程池
        if self._thread_pool_size is not None and self._thread_pool is None:
            self._thread_pool = ThreadPoolExecutor(
                    max_workers=self._thread_pool_size)

        # 初始化工作进程池
        if self._process_pool_size is not None and self._process_pool is None:
            self._process_pool = ProcessPoolExecutor(
                    max_workers=self._process_pool_size)

        # 关注server_socket上的读事件
        self._ioloop.add_handler(self._server_socket,
                                 partial(self._accept_connection, self._server_socket),
                                 IOLoop.READ)

        # 不定期的检查连接是否活跃，关闭不活跃连接
        self._ioloop.call_later(self._max_idle_time, self._close_inactive_connections)

        # 注册服务
        self._register_if_necessary()

        def change_status():
            LOGGER.info("change status")
            self._started = True
            self._starting = False
        self._ioloop.add_callback(change_status)

        try:
            self._ioloop.start()
        finally:
            # 清理资源
            self._close_if_necessary()
            # 关闭所有文件描述符
            LOGGER.info("close all fds")
            self._ioloop.close(all_fds=True)

    def close(self):
        self._close_if_necessary()

    def can_close(self):
        if not self._started:
            LOGGER.info("not started")
            return False
        if self._starting:
            LOGGER.info("starting")
            return False
        if self._closing:
            LOGGER.info("closing")
            return False
        if self._closed:
            LOGGER.info("closed")
            return False
        return True

    def _close_if_necessary(self):
        if not self.can_close():
            return

        with self._start_stop_lock:
            if not self.can_close():
                return

            self._closing = True
            self._closed = False

            # 关闭服务注册
            if self._registry is not None:
                self._registry.close()
                self._registry = None

            # 关闭事件循环
            self._ioloop.stop()

            # 关闭工作线程池
            thread_pool = self._thread_pool
            self._thread_pool = None
            if thread_pool is not None:
                thread_pool.shutdown()

            # 关闭工作进程池
            process_pool = self._process_pool
            self._process_pool = None
            if process_pool is not None:
                process_pool.shutdown()

            self._closed = True
            self._closing = False
            self._started = False
            self._starting = False


def WRAPPER(obj, method_name, *a, **kw):
    return getattr(obj, method_name)(*a, **kw)


class Runner(object):
    def __init__(self, connection_information, remote_address, transport, serializer,
                 exporter, thread_pool, process_pool,
                 ioloop, concurrent_request_per_connection):
        LOGGER.debug("accept connection from: %s" % str(remote_address))
        self._connection_information = connection_information
        self._stream = self._connection_information.stream
        self._transport = transport
        self._serializer = serializer
        self._exporter = exporter
        self._thread_pool = thread_pool
        self._process_pool = process_pool
        self._ioloop = ioloop
        self._concurrent_request_per_connection = concurrent_request_per_connection
        self._current_concurrency = 0

        self._run()

    @gen.coroutine
    def _run(self):
        while not self._connection_information.stream_closed and \
                    not self._stream.closed():
            # 判断是否达到了单个连接的最大并发数
            if self._current_concurrency >= self._concurrent_request_per_connection:
                # 如果是，那么进入阻塞等待状态，等待被唤醒
                LOGGER.debug("max concurrent request per connection reached")
                yield self._connection_information.read_condition.wait()
                LOGGER.debug("read condition is waken up")
                continue

            try:
                self._connection_information.timestamp = self._ioloop.time()
                # 读取请求
                transaction_id, buff = yield self._transport.read(self._stream)
                # 反序列化
                request = self._serializer.loads(buff)
                if not isinstance(request, Request):
                    LOGGER.error("expect Request, not %s" % type(request).__name__)
                    self._stream.close()
                    break
            except UnsatisfiableReadError:
                LOGGER.error("read operation unsatisfied")
                self._stream.close()
                break
            except StreamClosedError:
                LOGGER.debug("stream was closed while reading")
                break
            except DeserializationError:
                LOGGER.error("deserialization error:")
                LOGGER.error(traceback.format_exc())
                self._stream.close()
                break
            finally:
                self._connection_information.timestamp = self._ioloop.time()

            self._invoke(request, transaction_id)

    def _invoke(self, request, transaction_id):
        class_name = request.class_name
        method_name = request.method_name
        args = request.args
        kwargs = request.kwargs

        method = self._exporter.get_method(class_name, method_name)
        if method is None:
            msg = "the requested method:(%s, %s) is not exported" % (class_name, method_name)
            LOGGER.error(msg)
            future = Future()
            future.set_exception(LookupMethodError(msg))
        else:
            # 如果方法是tornado协程，则直接在IOLoop线程运行它
            if gen.is_coroutine_function(method):
                future = method(*args, **kwargs)
            else:
                run_in_subprocess = get_run_in_subprocess(method)
                # 如果方法具有run_in_subprocess标记，并且指定了进程池，
                # + 那么，在进程中运行它
                if run_in_subprocess is not None and \
                        run_in_subprocess and \
                        self._process_pool is not None:
                    try:
                        future = self._process_pool.submit(
                            WRAPPER,
                            self._exporter.get_object(class_name),
                            method_name,
                            *args,
                            **kwargs)
                    except BaseException as ex:
                        LOGGER.error("submit task to process pool failed, "
                                     "because %s: %s" % (ex.__class__.__name__, str(ex)))
                        future = Future()
                        future.set_exception(SubmitTaskToProcessPoolError(str(ex)))
                # 否则，如果指定了线程池，那么在线程中运行它
                elif self._thread_pool is not None:
                    future = self._thread_pool.submit(method, *args, **kwargs)
                # 如果没指定线程池，那么抛出异常
                else:
                    future = Future()
                    future.set_exception(ConcurrencyError("no thread pool is specified"))
        self._current_concurrency = self._current_concurrency + 1
        self._ioloop.add_future(future, partial(self._send_response,
                    request.meta, transaction_id))

    @gen.coroutine
    def _send_response(self, meta, transaction_id, future):
        if self._connection_information.stream_closed:
            raise gen.Return

        result = Result()
        result.meta = meta
        try:
            result.result = future.result()
        except BaseException:
            result.exc = MethodExecutionError(future.exception())

        try:
            buff = self._serializer.dumps(result)
            self._connection_information.timestamp = self._ioloop.time()
            yield self._transport.write(self._stream, transaction_id, buff)
        except SerializationError:
            LOGGER.error(traceback.format_exc())
        except StreamClosedError:
            LOGGER.debug("stream was closed while writing")
        except StreamBufferFullError:
            LOGGER.error("stream buffer was full while writing")
        finally:
            self._current_concurrency = max(self._current_concurrency - 1, 0)
            self._connection_information.timestamp = self._ioloop.time()
            self._connection_information.read_condition.notify_all()

