# coding: utf-8
from __future__ import unicode_literals

import pytest

from nuxeo.models import DirectoryEntry


def test_create_wrong_arguments(directory):
    with pytest.raises(ValueError):
        directory.create(1)


def test_crud(directory):
    new_entry = DirectoryEntry(properties={'id': 'foo', 'label': 'Foo'})
    entry = directory.create(new_entry)
    try:
        assert entry.entity_type == 'directoryEntry'
        assert entry.directoryName == 'nature'
        assert entry.properties['id'] == 'foo'
        assert entry.uid == 'foo'
        assert entry.properties['label'] == 'Foo'
        assert repr(entry)

        entry.properties['label'] = 'Test'
        entry.save()
        entry = directory.get('foo')
        assert entry.properties['label'] == 'Test'

        entry.properties['label'] = 'Foo'
        directory.save(entry)
        entry = directory.get('foo')
        assert entry.properties['label'] == 'Foo'
    finally:
        entry.delete()


def test_fetch(directory):
    entry = directory.get('article')
    assert entry.entity_type == 'directoryEntry'
    assert entry.directoryName == 'nature'
    assert entry.properties['id'] == 'article'
    assert entry.uid == 'article'
    assert entry.properties['label'] == 'label.directories.nature.article'


def test_fetch_all(directory):
    entries = directory.entries
    assert isinstance(entries, list)
    assert entries


def test_fetch_unknown(directory):
    assert not directory.exists('Abitbol')
