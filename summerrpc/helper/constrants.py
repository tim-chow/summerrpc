# coding: utf8

__all__ = ["ERRNO_CONNRESET"]
__authors__ = ["Tim Chow"]

import errno


ERRNO_CONNRESET = (errno.ECONNRESET,
                   errno.ECONNABORTED,
                   errno.EPIPE,
                   errno.ETIMEDOUT)
