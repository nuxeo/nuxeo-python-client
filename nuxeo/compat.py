# coding: utf-8
from __future__ import unicode_literals

try:
    from typing import Text, Union
    from requests import HTTPError
except ImportError:
    pass

try:
    from urllib.parse import quote
except ImportError:
    from urllib2 import quote

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

try:
    text = unicode
except NameError:
    text = str


def get_bytes(data):
    # type: (Union[Text, bytes]) -> bytes
    """
    If data is not bytes, encode it.

    :param data: the input data
    :return: the bytes of data
    """
    if isinstance(data, text):
        data = data.encode('utf-8')
    return data


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


def get_error_message(e):
    # type: (HTTPError) -> Text
    """
    Get error message from an HTTPError.

    :param e: the HTTPError
    :return: The text of the message
    """
    if hasattr(e, 'message'):
        return get_text(e.message)
    else:
        return get_text(e.args[0])
