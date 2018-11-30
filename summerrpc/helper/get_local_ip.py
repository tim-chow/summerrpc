# coding: utf8

__all__ = ["get_local_ip"]
__authors__ = ["Tim Chow"]

import netifaces


def get_local_ip(exclude_interfaces=None):
    if exclude_interfaces is None:
        exclude_interfaces = []
    elif isinstance(exclude_interfaces, str):
        exclude_interfaces = [exclude_interfaces]
    elif not isinstance(exclude_interfaces, (list, tuple)):
        raise TypeError("expect None, str, list or tuple, not %s" %
                        type(exclude_interfaces).__name__)

    for interface in netifaces.interfaces():
        if interface in exclude_interfaces:
            continue

        for address in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
            yield address["addr"]
