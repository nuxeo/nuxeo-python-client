# coding: utf-8
from __future__ import unicode_literals

import pytest

from nuxeo.utils import get_digester


@pytest.mark.parametrize('hash, digester', [
    # Known algos
    ('0' * 32, 'md5'),
    ('0' * 40, 'sha1'),
    ('0' * 56, 'sha224'),
    ('0' * 64, 'sha256'),
    ('0' * 96, 'sha384'),
    ('0' * 128, 'sha512'),
    # Other
    (None, None),
    ('', None),
    ('foo', None),
    ('dead', None),
])
def test_get_digester(hash, digester):
    if not digester:
        assert not get_digester(hash)
    else:
        assert get_digester(hash).name == digester
