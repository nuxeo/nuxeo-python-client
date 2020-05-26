# coding: utf-8
from __future__ import unicode_literals

import os

import nuxeo.constants


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

# Speed-up testing by drastically reducing the backoff factor for retries
nuxeo.constants.RETRY_BACKOFF_FACTOR = 0.01


# Taken from https://github.com/nuxeo/nuxeo-drive/blob/master/nxdrive/utils.py
# Those are used to skip tests or part of a test based on the current server version.

def cmp(a, b):
    """ cmp() does not exist anymore in Python 3. """
    if a is None:
        if b is None:
            return 0
        return -1
    if b is None:
        return 1
    return (a > b) - (a < b)


def version_compare(x, y):
    """ Compare server versions (including snapshots and hotfixes). """

    # Handle None values
    if not all((x, y)):
        return cmp(x, y)

    ret = (-1, 1)

    x_numbers = x.split(".")
    y_numbers = y.split(".")
    while x_numbers and y_numbers:
        x_part = x_numbers.pop(0)
        y_part = y_numbers.pop(0)

        # Handle hotfixes
        if "HF" in x_part:
            hf = x_part.replace("-HF", ".").split(".", 1)
            x_part = hf[0]
            x_numbers.append(hf[1])
        if "HF" in y_part:
            hf = y_part.replace("-HF", ".").split(".", 1)
            y_part = hf[0]
            y_numbers.append(hf[1])

        # Handle snapshots
        x_snapshot = "SNAPSHOT" in x_part
        y_snapshot = "SNAPSHOT" in y_part
        if not x_snapshot and y_snapshot:
            # y is snapshot, x is not
            x_number = int(x_part)
            y_number = int(y_part.replace("-SNAPSHOT", ""))
            return ret[y_number <= x_number]
        elif not y_snapshot and x_snapshot:
            # x is snapshot, y is not
            x_number = int(x_part.replace("-SNAPSHOT", ""))
            y_number = int(y_part)
            return ret[x_number > y_number]

        x_number = int(x_part.replace("-SNAPSHOT", ""))
        y_number = int(y_part.replace("-SNAPSHOT", ""))
        if x_number != y_number:
            return ret[x_number - y_number > 0]

    if x_numbers:
        return 1
    if y_numbers:
        return -1

    return 0


def version_lt(x, y):
    """ x < y """
    return version_compare(x, y) < 0
