# coding: utf8

__all__ = ["JsonSerializer"]
__authors__ = ["Tim Chow"]

import json
import datetime

from .base_serializer import BaseSerializer


class JsonSerializer(BaseSerializer):
    def _loads(self, buff):
        return json.loads(buff)

    def __json_default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%F %T")
        if isinstance(obj, datetime.date):
            return obj.strftime("F")
        if isinstance(obj, datetime.time):
            return obj.strftime("%T")
        raise TypeError("%r is not json serializable" % obj)

    def _dumps(self, d):
        return json.dumps(d, default=self.__json_default)

    def get_name(self):
        return "json"

