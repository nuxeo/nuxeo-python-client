# coding: utf-8
"""
Highly inspired from https://github.com/finbourne/lusid-sdk-python/blob/ef029ec/sdk/lusid/tcp/tcp_keep_alive_probes.py
See NXPY-182 and linked tickets for details.
"""
from __future__ import unicode_literals

import socket

from requests.adapters import HTTPAdapter
from urllib3 import HTTPConnectionPool, HTTPSConnectionPool, PoolManager

from ..constants import (
    LINUX,
    MAC,
    TCP_KEEPALIVE,
    TCP_KEEPALIVE_INTERVAL,
    TCP_KEEP_CNT,
    TCP_KEEP_IDLE,
    WINDOWS,
)


class TCPKeepAliveValidationMethods(object):
    """
    This class contains a single method whose sole purpose is to set up TCP Keep Alive probes on the socket for a
    connection. This is necessary for long running requests which will be silently terminated by the AWS Network Load
    Balancer which kills a connection if it is idle for more then 350 seconds.
    """

    @staticmethod
    def adjust_connection_socket(conn, protocol="https"):
        """
        Adjusts the socket settings so that the client sends a TCP keep alive probe over the connection. This is only
        applied where possible, if the ability to set the socket options is not available, for example using Anaconda,
        then the settings will be left as is.

        :param conn: The connection to update the socket settings for
        :param str protocol: The protocol of the connection

        :return: None
        """

        if protocol == "http":
            # It isn't clear how to set this up over HTTP, it seems to differ from HTTPS.
            # Thus, the issue we are trying to fix here does not happen on HTTP.
            return

        # TCP Keep Alive probes for different platforms
        if (
            LINUX
            and hasattr(socket, "TCP_KEEPCNT")
            and hasattr(socket, "TCP_KEEPIDLE")
            and hasattr(socket, "TCP_KEEPINTVL")
        ):
            conn.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, TCP_KEEP_IDLE)
            conn.sock.setsockopt(
                socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, TCP_KEEPALIVE_INTERVAL
            )
            conn.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, TCP_KEEP_CNT)
        elif MAC and getattr(conn.sock, "setsockopt", None) is not None:
            conn.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            conn.sock.setsockopt(
                socket.IPPROTO_TCP, TCP_KEEPALIVE, TCP_KEEPALIVE_INTERVAL
            )
        elif (
            WINDOWS
            and hasattr(socket, "SIO_KEEPALIVE_VALS")
            and getattr(conn.sock, "ioctl", None) is not None
        ):
            conn.sock.ioctl(
                socket.SIO_KEEPALIVE_VALS,
                (1, TCP_KEEP_IDLE * 1000, TCP_KEEPALIVE_INTERVAL * 1000),
            )


class TCPKeepAliveHTTPSConnectionPool(HTTPSConnectionPool):
    """
    This class overrides the _validate_conn method in the HTTPSConnectionPool class. This is the entry point to use
    for modifying the socket as it is called after the socket is created and before the request is made.
    """

    def _validate_conn(self, conn):
        """Called right before a request is made, after the socket is created."""
        super()._validate_conn(conn)
        TCPKeepAliveValidationMethods.adjust_connection_socket(conn, protocol="https")


class TCPKeepAliveHTTPConnectionPool(HTTPConnectionPool):
    """
    This class overrides the _validate_conn method in the HTTPSConnectionPool class. This is the entry point to use
    for modifying the socket as it is called after the socket is created and before the request is made.

    In the base class this method is passed completely.
    """

    def _validate_conn(self, conn):
        """Called right before a request is made, after the socket is created."""
        super()._validate_conn(conn)
        TCPKeepAliveValidationMethods.adjust_connection_socket(conn, protocol="http")


class TCPKeepAlivePoolManager(PoolManager):
    """
    This Pool Manager has only had the pool_classes_by_scheme variable changed. This now points at the TCPKeepAlive
    connection pools rather than the default connection pools.
    """

    def __init__(self, num_pools=10, headers=None, **connection_pool_kw):
        super().__init__(num_pools=num_pools, headers=headers, **connection_pool_kw)
        self.pool_classes_by_scheme = {
            "http": TCPKeepAliveHTTPConnectionPool,
            "https": TCPKeepAliveHTTPSConnectionPool,
        }


class TcpKeepAliveHttpAdapter(HTTPAdapter):
    """"Transport adapter that allows us to set TCP Keep Alive options."""

    def init_poolmanager(self, connections, maxsize, **pool_kwargs):
        """Override the default pool manager."""
        self.poolmanager = TCPKeepAlivePoolManager(
            num_pools=connections, maxsize=maxsize, **pool_kwargs
        )
