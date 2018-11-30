# coding: utf8

__all__ = ["Connection", "SharedBlockingConnection", "SimpleBlockingConnection"]
__authors__ = ["Tim Chow"]

from abc import ABCMeta, abstractmethod, abstractproperty
import threading
import socket
from functools import partial
import time
import logging
import traceback

from concurrent.futures import Future

from .helper import *
from .exception import *

LOGGER = logging.getLogger(__name__)


class Connection(object):
    __metaclass__ = ABCMeta

    # 返回二元组：(TransactionId, Future)
    @abstractmethod
    def write(self, buff, timeout=None):
        """写数据"""
        pass

    # 返回一个Future对象
    @abstractmethod
    def read(self, transaction_id, timeout=None):
        """读响应"""
        pass

    @abstractmethod
    def close(self):
        """关闭Connection以及底层socket"""
        pass

    @abstractproperty
    def closed(self):
        """closed为True标识：Connection以及底层socket已经关闭"""
        pass

    @abstractproperty
    def closing(self):
        """closing为True标识：Connection正在关闭，但尚未完成"""
        pass


class SharedBlockingConnection(Connection):
    def __init__(self,
                 underlying_socket,
                 transport,
                 max_pending_writes=None,
                 max_pending_reads=None,
                 max_pooling_reads=None,
                 write_timeout=60,
                 heartbeat_interval=None,
                 heartbeat_func=None,
                 *a,
                 **kw):
        self._socket = underlying_socket
        self._transport = transport

        self._write_timeout = write_timeout
        self._write_condition = threading.Condition()
        self._pending_writes = StaticList(max_pending_writes or 65535)
        self._async_write_thread = threading.Thread(target=self._async_write)
        self._async_write_thread.setDaemon(False)

        self._read_condition = threading.Condition()
        self._pending_reads = LRUCache(max_pending_reads or 65535)
        self._pooling_reads = LRUCache(max_pooling_reads or 65535)
        self._async_read_thread = threading.Thread(target=self._async_read)
        self._async_read_thread.setDaemon(False)

        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_func = heartbeat_func
        self._heartbeats = LRUCache(4)
        self._heartbeat_lock = threading.Lock()

        self._id_generator = partial(AtomicInteger(0).increase, 1)
        self._close_lock = threading.Lock()
        self._closing = False
        self._closed = False

        # 启动读写线程
        self._async_read_thread.start()
        self._async_write_thread.start()

    def _update_pending_writes(self, buff, timeout):
        f = Future()
        transaction_id = self._id_generator()
        self._pending_writes.insert_left(
                (buff, f, transaction_id, time.time(), timeout))
        return f, transaction_id

    def write(self, buff, timeout=None):
        timeout = timeout or self._write_timeout
        self._write_condition.acquire()
        try:
            if self._closing or self._closed:
                raise ConnectionAbortError("write abort")
            if self._pending_writes.is_full():
                raise MaxPendingWritesReachedError("max pending writes reached")

            f, transaction_id = self._update_pending_writes(buff, timeout)

            # 唤醒写线程
            self._write_condition.notify_all()
            return transaction_id, f
        finally:
            self._write_condition.release()

    def read(self, transaction_id, timeout=None):
        self._read_condition.acquire()
        try:
            if self._closing or self._closed:
                raise ConnectionAbortError("read abort")

            if transaction_id in self._pooling_reads:
                f = self._pooling_reads[transaction_id]
                del self._pooling_reads[transaction_id]
                return f

            if transaction_id in self._pending_reads:
                return self._pending_reads[transaction_id]

            entry = self._pending_reads.will_be_kicked_out()
            if entry is not None:
                entry.value.set_exception(MaxPendingReadsReachedError(
                            "max pending reads reached"))
            f = Future()
            self._pending_reads[transaction_id] = f
            # 唤醒读线程
            self._read_condition.notify_all()
            return f
        finally:
            self._read_condition.release()

    def _precheck_before_writing(self, missing_too_many_heartbeats,
                need_to_wakeup_read_thread):
        # 如果丢失了过多的心跳，则认为连接断开了，会关闭连接
        if missing_too_many_heartbeats:
            self.close()
            missing_too_many_heartbeats = False
            return None

        # 在插入心跳之后，需要唤醒读线程
        if need_to_wakeup_read_thread:
            LOGGER.debug("wake up read thread, because there is new heartbeat")
            with self._read_condition:
                self._read_condition.notify_all()
            need_to_wakeup_read_thread = False

        # 获取底层锁
        self._write_condition.acquire()
        if self._closing or self._closed:
            self._write_condition.release()
            return None

        # 如果没有写操作，那么写线程进入等待状态
        if self._pending_writes.size == 0:
            buff, future, transaction_id, timestamp, timeout = \
                None, None, None, None, None
            time_to_wait = None if self._heartbeat_interval is None \
                        else self._heartbeat_interval / 2.
            with time_used("write condition wait", 0.01):
                self._write_condition.wait(time_to_wait)
            LOGGER.debug("async write thread has been waken up")
            # 在写线程被唤醒或等待到超时之后，
            # + 需要判断是否应该插入心跳
            if not self._closing and \
                    not self._closed and \
                    self._pending_writes.size == 0 and \
                    self._heartbeat_func is not None and \
                    self._heartbeat_interval is not None:
                # 检查是否丢失heartbeat
                with self._heartbeat_lock:
                    # 如果丢失的心跳在可接受范围内，则：
                    if self._heartbeats.current_size < \
                                self._heartbeats.max_size:
                        # + 插入heartbeat
                        f, transaction_id = self._update_pending_writes(
                                self._heartbeat_func(),
                                self._heartbeat_interval)
                        self._heartbeats[transaction_id] = f
                        need_to_wakeup_read_thread = True
                    # 如果丢失了太多的心跳回复，则：
                    else:
                        LOGGER.error("missing too many heartbeats, closing connection")
                        # + 设置missing_too_many_heartbeats标记，之后会关闭连接
                        missing_too_many_heartbeats = True
        else:
            # 如果存在写操作，则弹出一个
            buff, future, transaction_id, timestamp, timeout = \
                self._pending_writes.pop_left()

        self._write_condition.release()
        return missing_too_many_heartbeats, need_to_wakeup_read_thread, \
            buff, future, transaction_id, timestamp, timeout

    # 写线程
    def _async_write(self):
        missing_too_many_heartbeats = False
        need_to_wakeup_read_thread = False
        while True:
            with time_used("Connection._precheck_before_writing", 0.005):
                ret = self._precheck_before_writing(missing_too_many_heartbeats,
                            need_to_wakeup_read_thread)
                if ret is None:
                    break
                missing_too_many_heartbeats, need_to_wakeup_read_thread, \
                    buff, future, transaction_id, timestamp, timeout = ret
                if buff is None:
                    continue

            # 判断是否到达了超时时间
            if timeout is not None and timestamp + timeout <= time.time():
                future.set_exception(ConnectionWriteTimeout(
                    "transaction_id: %s" % transaction_id))
                continue

            try:
                self._transport.write(
                            self._socket,
                            transaction_id,
                            buff)
                future.set_result(transaction_id)
            except socket.timeout:
                future.set_exception(ConnectionWriteTimeout("write timeout"))
                self.close()
                break
            except socket.error:
                future.set_exception(ConnectionAbortError("write abort"))
                self.close()
                break
            time.sleep(0.0)
        LOGGER.info("async write thread exited, thread indent: %s" %
                    threading.currentThread().ident)

    def _async_read(self):
        while True:
            self._read_condition.acquire()
            if self._closing or self._closed:
                self._read_condition.release()
                break

            # 如果没有读操作，
            if self._pending_reads.current_size == 0:
                self._heartbeat_lock.acquire()
                has_heartbeat = self._heartbeats.current_size > 0
                self._heartbeat_lock.release()
                # + 并且没有待接收的心跳回复，
                # 那么，读线程进入到等待状态
                if not has_heartbeat:
                    self._read_condition.wait()
                    LOGGER.debug("async read thread has been waken up")
                    self._read_condition.release()
                    continue
            self._read_condition.release()

            # 否则，通过底层socket，读取响应
            try:
                transaction_id, buff = self._transport.read(self._socket)
            except (TransportError, socket.error):
                LOGGER.error("socket already closed")
                self.close()
                break

            # 如果收到的是心跳回复
            with self._heartbeat_lock:
                if self._closing or self._closed:
                    break
                if transaction_id in self._heartbeats:
                    LOGGER.debug("accept heartbeat response, transaction_id is: %s" % transaction_id)
                    f = self._heartbeats[transaction_id]
                    f.set_result(buff)
                    del self._heartbeats[transaction_id]
                    continue

            # 如果收到的是正常的响应
            with self._read_condition:
                if self._closing or self._closed:
                    break
                if transaction_id in self._pending_reads:
                    f = self._pending_reads[transaction_id]
                    del self._pending_reads[transaction_id]
                    f.set_result(buff)
                    continue
                entry = self._pooling_reads.will_be_kicked_out()
                if entry is not None:
                    LOGGER.error("transaction_id: %s hasn't been consumed" % entry.key)
                f = Future()
                f.set_result(buff)
                self._pooling_reads[transaction_id] = f

        LOGGER.info("async read thread exited, thread ident: %d" %
                    threading.currentThread().ident)

    def close(self):
        if self._closed or self._closing:
            return
        with self._close_lock:
            if self._closed or self._closing:
                return
            self._closing = True

        self._socket.close()
        self._close_write()
        self._close_read()

        self._closed = True
        self._closing = False

    def _close_write(self):
        self._write_condition.acquire()
        while self._pending_writes.size > 0:
            buff, future, transaction_id, timestamp, timeout = \
                    self._pending_writes.pop_left()
            future.set_exception(ConnectionAbortError("write abort"))
        # 唤醒写线程
        self._write_condition.notify_all()
        self._write_condition.release()

    def _close_read(self):
        self._read_condition.acquire()
        for transaction_id, future in self._pending_reads.iteritems():
            future.set_exception(ConnectionAbortError("read abort"))
            LOGGER.info("closing read: transaction_id: %d" % transaction_id)

        self._pooling_reads.clear()
        # 唤醒读线程
        self._read_condition.notify_all()
        self._read_condition.release()

    @property
    def closed(self):
        return self._closed

    @property
    def closing(self):
        return self._closing


class SimpleBlockingConnection(Connection):
    def __init__(self, underlying_socket, transport, *a, **kw):
        self._socket = underlying_socket
        self._transport = transport
        self._id_generator = partial(AtomicInteger(0).increase, 1)
        self._close_lock = threading.Lock()
        self._closed = False
        self._closing = False

    def write(self, buff, timeout=None):
        future = Future()
        transaction_id = self._id_generator()
        try:
            self._transport.write(self._socket, transaction_id, buff)
        except socket.timeout:
            future.set_exception(ConnectionWriteTimeout("write timeout"))
            self.close()
        except socket.error as ex:
            future.set_exception(ConnectionAbortError("write abort"))
            self.close()
        else:
            future.set_result(transaction_id)
        return transaction_id, future

    def read(self, transaction_id, timeout=None):
        future = Future()
        try:
            read_transaction_id, buff = \
                self._transport.read(self._socket, ignore_timeout=False)
        except socket.timeout:
            future.set_exception(ConnectionReadTimeout("read timeout"))
            self.close()
        except (TransportError, socket.error):
            future.set_exception(ConnectionAbortError("read abort"))
            self.close()
        else:
            if read_transaction_id != transaction_id:
                LOGGER.error("write-read must appear in pairs")
                future.set_exception(RuntimeError("read and write is inconsistent"))
                self.close()
            else:
                future.set_result(buff)
        return future

    def close(self):
        if self._closed or self._closing:
            return
        with self._close_lock:
            if self._closed or self._closing:
                return
            self._closing = True

        self._socket.close()
        self._closed = True
        self._closing = False

    @property
    def closed(self):
        return self._closed

    @property
    def closing(self):
        return self._closing

