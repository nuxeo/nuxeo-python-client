# coding: utf-8
from glob import glob
from shutil import rmtree
from subprocess import check_output

from nuxeo import __version__

# We do not need to set-up a server and log the current test
skip_logging = True

CMD = "python setup.py sdist bdist_wheel".split()


def test_packaged_files():
    """Ensure the produced package contains all required files."""
    # Clean-up
    rmtree("build", ignore_errors=True)
    rmtree("dist", ignore_errors=True)
    rmtree("nuxeo.egg-info", ignore_errors=True)

    output = str(check_output(CMD))
    for file in glob("nuxeo/**/*.py"):
        assert str(file) in output


def test_wheel_python_3():
    """Ensure the produced wheel is Python 3."""
    output = str(check_output(CMD))
    text = "nuxeo-{}-py3-none-any.whl".format(__version__)
    assert text in output
