# coding: utf-8
from __future__ import unicode_literals

import os


def setup_sentry():
    """ Setup Sentry. """

    if os.getenv("SKIP_SENTRY", "0") == "1":
        return

    sentry_dsn = os.getenv("SENTRY_DSN")
    if not sentry_dsn:
        return

    import sentry_sdk
    from nuxeo import __version__

    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=os.getenv("SENTRY_ENV", "testing"),
        release=__version__,
        attach_stacktrace=True,
        ignore_errors=[KeyboardInterrupt],
    )


setup_sentry()
