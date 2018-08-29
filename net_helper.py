#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket,os,subprocess

# check if its a valid ipv4 address by using socket
def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True

# check if its a valid ipv6 address by using socket
def is_valid_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # not a valid address
        return False
    return True

# get an ip from a given hostname by using dns
def get_ip_from_hostname(hostname):
    return socket.gethostbyname(hostname)

# ping a host
def ping_host(ip):
    if os.system("ping -c 1 " + str(ip)) == 0:
       return True
    else:
       return False

