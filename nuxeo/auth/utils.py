# coding: utf-8
from base64 import b64encode
from typing import Optional
from ..exceptions import NuxeoError
from ..utils import get_bytes, get_digest_hash, get_text


def make_portal_sso_token(timestamp, random, secret, username, digest_algorithm="md5"):
    # type: (int, str, str, str, Optional[str]) -> str
    """Generate a token for SSO with Portals."""
    digester = get_digest_hash(digest_algorithm)
    if not digester:
        err = f"Cannot compute token because of unknown digest algorithm: {digest_algorithm!r}"
        raise NuxeoError(err)

    clear_token = ":".join([str(timestamp), random, secret, username])
    digester.update(get_bytes(clear_token))
    hashed_token = digester.digest()
    return get_text(b64encode(hashed_token))
