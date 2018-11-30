# coding: utf8

__all__ = ["MsgpackSerializer"]
__authors__ = ["Tim Chow"]

import datetime
import msgpack

from .base_serializer import BaseSerializer


class MsgpackSerializer(BaseSerializer):
    def __msgpack_default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%F %T")
        if isinstance(obj, datetime.date):
            return obj.strftime("%F")
        if isinstance(obj, datetime.time):
            return obj.strftime("%T")
        raise TypeError

    def _loads(self, buff):
        return msgpack.unpackb(buff)

    def _dumps(self, d):
        return msgpack.packb(d, default=self.__msgpack_default)

    def get_name(self):
        return "msgpack"

