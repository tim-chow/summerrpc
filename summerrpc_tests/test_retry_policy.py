# coding: utf8

import unittest

from summerrpc.helper import RetryPolicy, MaxRetryCountReached


class TestRetryPolicy(unittest.TestCase):
    def testRetryPolicy(self):
        retry_policy = RetryPolicy.Builder() \
                .with_max_retry_count(3) \
                .add_retry_exception(RuntimeError) \
                .with_retry_interval(1) \
                .build()

        def func():
            raise RuntimeError("just for test")

        try:
            retry_policy.run(func)
        except MaxRetryCountReached as ex:
            print(ex.exc_info)

