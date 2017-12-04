# coding: utf-8
"""
Nuxeo REST API Python client.
https://doc.nuxeo.com/nxdoc/rest-api/

You can always get the latest version of this module at:
    https://github.com/nuxeo/nuxeo-python-client
If that URL should fail, try contacting the author.

Contributors:
    Antoine Taillefer <ataillefer@nuxeo.com>
    Rémi Cattiau <rcattiau@nuxeo.com>
    Mickaël Schoentgen <mschoentgen@nuxeo.com>
    Léa Klein <lklein@nuxeo.com>
    https://github.com/nuxeo/nuxeo-python-client/graphs/contributors
"""
from __future__ import unicode_literals

from .nuxeo import Nuxeo
from os import path
from setuptools.config import read_configuration

_conf = read_configuration(path.join(path.dirname(path.dirname(__file__)), 'setup.cfg'))

__author__ = _conf['metadata']['author']
__version__ = _conf['metadata']['version']
__copyright__ = """
    Copyright Nuxeo (https://www.nuxeo.com) and others.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
__all__ = ('Nuxeo',)
