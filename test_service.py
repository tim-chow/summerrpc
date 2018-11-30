import time
import threading
import os

import tornado.gen as gen
from summerrpc.decorator import run_in_subprocess


class TestService(object):
    def test(self, ident):
        return "this is test in TestService, thread ident is: %d" % ident

    @gen.coroutine
    def test_async(self, data):
        raise gen.Return("this is test_async in TestService, "
            "data is: %s" % (data, ))

    @gen.coroutine
    def test_raise(self, ident):
        raise RuntimeError("raised in test_raise, thread ident is: %d" % ident)

    def test_sync_sleep(self, t, ident):
        print("in test_sync_sleep, thread ident is: %s" % threading.currentThread().ident)
        time.sleep(t)
        return "test_sync_sleep end, thread ident is: %d" % ident

    @gen.coroutine
    def test_async_sleep(self, t, ident):
        print("in test_async_sleep, thread ident is: %s" %
              threading.currentThread().ident)
        yield gen.sleep(t)
        raise gen.Return("test_async_sleep end, thread ident is: %d" % ident)

    @run_in_subprocess
    def test_run_in_subprocess(self):
        msg = "test_run_in_subprocess, pid is: %d" % os.getpid()
        print(msg)
        return msg

