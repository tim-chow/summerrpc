# coding: utf8

__all__ = ["time_used"]
__authors__ = ["Tim Chow"]

import logging
from contextlib import contextmanager
import time

LOGGER = logging.getLogger(__name__)


@contextmanager
def time_used(note, threshold=0.1):
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        if elapsed >= threshold:
            LOGGER.info("%s used %fs" % (note, elapsed))

