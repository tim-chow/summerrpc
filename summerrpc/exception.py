# coding: utf8

# 所有异常类的基类
# + 异常对象会包含一个消息或封装一个异常对象
class BaseError(Exception):
    def __init__(self, msg=None):
        Exception.__init__(self)
        self._msg = msg

    @property
    def msg(self):
        return self._msg

    def __getstate__(self):
        return (self._msg, )

    def __setstate__(self, msg):
        self._msg = msg

    def __str__(self):
        return "%s: %s" % (type(self._msg).__name__, str(self._msg))

    __repr__ = __str__


##### StubSideError #####
# Stub端的异常
class StubSideError(BaseError):
    pass


class FilteredError(StubSideError):
    pass
##### StubSideError #####


##### TransportError #####
class TransportError(BaseError):
    pass


# 非阻塞的Transport抛出的异常直接使用tornado中的


# 阻塞的Transport相关的异常，
# + socket相关的异常直接使用socket模块的
class BlockingTransportError(TransportError):
    pass


# socket已经被关闭
class SocketAlreadyClosedError(BlockingTransportError):
    pass


# 非法的数据包
class InvalidPacketError(TransportError):
    pass
##### TransportError #####


##### SerializerError #####
# 序列化相关的异常
class SerializerError(BaseError):
    pass


# 序列化错误
class SerializationError(SerializerError):
    pass


# 反序列化错误
class DeserializationError(SerializerError):
    pass
##### SerializerError #####


##### RemoteError #####
# 与远程服务相关的错误
class RemoteError(BaseError):
    pass


# 没有提供服务的远程服务器
class NoRemoteServerError(RemoteError):
    pass


# 服务端没有指定线程池
class ConcurrencyError(RemoteError):
    pass


# 寻找导出方法失败
class LookupMethodError(RemoteError):
    pass


# 向进程池提交任务失败
class SubmitTaskToProcessPoolError(RemoteError):
    pass


# 方法执行失败
class MethodExecutionError(RemoteError):
    pass


# 请求结构体中缺少必要字段
class RequestValidateError(RemoteError):
    pass


# 错误的响应对象
class InvalidResponseError(RemoteError):
    pass
##### RemoteError #####


##### ConnectionError #####
# Connection相关的错误
class ConnectionError(BaseError):
    pass


# 写超时
class ConnectionWriteTimeout(ConnectionError):
    pass


# 连接已经断开
class ConnectionAbortError(ConnectionError):
    pass


# 读超时
class ConnectionReadTimeout(ConnectionError):
    pass


# 达到了最大并发写请求的数量
class MaxPendingWritesReachedError(ConnectionError):
    pass


# 达到了最大并发读请求的数量
class MaxPendingReadsReachedError(ConnectionError):
    pass
##### ConnectionError #####


##### ConnectionPoolError #####
# 连接池相关的异常
class ConnectionPoolError(BaseError):
    pass


# 连接池中无可用连接
class NoAvailableConnectionError(ConnectionPoolError):
    pass


# 连接池已经关闭了
class ConnectionPoolAlreadyClosedError(ConnectionPoolError):
    pass


# 创建连接失败
class CreateConnectionError(ConnectionPoolError):
    pass
##### ConnectionPoolError #####

