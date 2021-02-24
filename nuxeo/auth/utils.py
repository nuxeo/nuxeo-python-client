# coding: utf-8
from __future__ import unicode_literals

from base64 import b64encode

from ..compat import get_bytes, get_text
from ..utils import get_digest_hash

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import Text, Optional
except ImportError:
    pass


def make_portal_sso_token(timestamp, random, secret, username, digest_algorithm="md5"):
    # type: (int, Text, Text, Text, Optional[Text]) -> Text
    """Generate a token for SSO with Portals."""
    clear_token = ":".join([str(timestamp), random, secret, username])
    digester = get_digest_hash(digest_algorithm)
    digester.update(get_bytes(clear_token))
    hashed_token = digester.digest()
    return get_text(b64encode(hashed_token))
