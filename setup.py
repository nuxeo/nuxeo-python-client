# coding: utf-8
from __future__ import unicode_literals

import codecs
import re

from setuptools import setup


def get_version(init_file):
    """ Find the current version. """

    with codecs.open(init_file, encoding='utf-8') as handler:
        for line in handler.readlines():
            if line.startswith('__version__'):
                return re.findall(r"'(.+)'", line)[0]


version = get_version('nuxeo/__init__.py')
url = 'https://github.com/nuxeo/nuxeo-python-client'
setup(
    name='nuxeo-python-client',
    packages=['nuxeo'],
    version=version,
    description='Nuxeo REST API Python client',
    long_description=open('README.md').read(),
    author='Nuxeo',
    author_email='mschoentgen@nuxeo.com',  # Current maintainer
    url=url,
    download_url='{}/tarball/{}'.format(url, version),
    license='Apache Software',
    keywords=['api', 'rest', 'automation', 'client', 'nuxeo', 'ecm'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        # 'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
    ],
    install_requires=[
        'poster',
    ],
)
