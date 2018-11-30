# coding: utf8

__all__ = ["URLBuilder", "parse_query"]
__authors__ = ["Tim Chow"]

import urllib


def parse_query(qr, unquote=False):
    query = {}
    for item in qr.split("&"):
        pair = item.split("=", 1)
        if len(pair) == 1:
            continue

        k = pair[0]
        if unquote:
            k = urllib.unquote(k)
        v = pair[1]
        if unquote:
            v = urllib.unquote(v)
        query.setdefault(k, []).append(v)
    return query


class URLBuilder(object):
    def __init__(self):
        self._scheme = None
        self._host = None
        self._port = None
        self._path = ""
        self._query_arguments = {}
        self._fragment = None

    def with_scheme(self, scheme):
        self._scheme = scheme
        return self

    def with_host(self, host):
        self._host = host
        return self

    def with_port(self, port):
        if not isinstance(port, int):
            raise TypeError("expect int, not %s" %
                            type(port).__name__)
        if port < 0:
            raise ValueError("port should not be less than 0")
        self._port = port
        return self

    def with_path(self, path):
        if not isinstance(path, str):
            raise TypeError("expect str, not %s" %
                            type(path).__name__)
        if len(path) > 0 and not path.startswith("/"):
            raise ValueError("path should start with '/' if it is not empty")
        self._path = path
        return self

    def with_argument(self, k, v):
        if not isinstance(k, str) or not isinstance(v, str):
            raise TypeError("both k and v should be str")
        self._query_arguments.setdefault(k, []).append(v)
        return self

    def with_fragment(self, fragment):
        if not isinstance(fragment, str):
            raise TypeError("expect str, not %s" %
                            type(fragment).__name__)
        self._fragment = fragment
        return self

    def build(self, quote_url=False):
        items = []

        if self._scheme is None:
            items.append("//")
        else:
            items.extend([self._scheme, "://"])

        if self._host is not None:
            items.append(self._host)
            if self._port is not None:
                items.append(":%d" % self._port)

        items.append(self._path)
        
        if len(self._query_arguments) > 0:
            items.append("?")

            query_arguments = []
            for k, vl in self._query_arguments.iteritems():
                for v in vl:
                    query_arguments.append("%s=%s" % (k, v))
            items.append("&".join(query_arguments))

        if self._fragment:
            items.extend(["#", self._fragment])

        url = "".join(items)
        if quote_url:
            url = urllib.quote(url, safe="")
        return url
