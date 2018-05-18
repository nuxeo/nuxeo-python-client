# coding: utf-8
from __future__ import unicode_literals

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Text, Type, Union
        from requests import HTTPError
except ImportError:
    pass

try:
    from urllib.parse import quote, urlencode
except ImportError:
    from urllib2 import quote
    from urllib import urlencode

try:
    long = long
except NameError:
    long = int

try:
    text = unicode  # type: Type[Text]
except NameError:
    text = str      # type: Type[Text]


def get_bytes(data):
    # type: (Union[Text, bytes]) -> bytes
    """
    If data is not bytes, encode it.

    :param data: the input data
    :return: the bytes of data
    """
    if not isinstance(data, bytes):
        data = data.encode('utf-8')
    return data


def get_error_message(exc):
    # type: (HTTPError) -> Text
    """
    Get error message from an HTTPError.

    :param exc: the HTTPError
    :return: The text of the message
    """
    return get_text(getattr(exc, 'message', exc.args[0]))


def get_text(data):
    # type: (Union[Text, bytes]) -> Text
    """
    If data is not text, decode it.

    :param data: the input data
    :return: data in unicode
    """
    if not isinstance(data, text):
        data = data.decode('utf-8')
    return data
