# coding: utf-8
from __future__ import unicode_literals


def test_crud(directory):
    new_entry = {'id': 'foo', 'label': 'Foo'}
    entry = directory.create(new_entry)
    assert entry.entity_type == 'directoryEntry'
    assert entry.directoryName == 'nature'
    assert entry.properties['id'] == 'foo'
    assert entry.get_id() == 'foo'
    assert entry.properties['label'] == 'Foo'

    entry.properties['label'] = 'Test'
    entry.save()
    entry = directory.fetch('foo')
    assert entry.properties['label'] == 'Test'
    entry.delete()


def test_fetch(directory):
    entry = directory.fetch('article')
    assert entry.entity_type == 'directoryEntry'
    assert entry.directoryName == 'nature'
    assert entry.properties['id'] == 'article'
    assert entry.get_id() == 'article'
    assert entry.properties['label'] == 'label.directories.nature.article'


def test_fetch_all(directory):
    entries = directory.fetch_all()
    assert isinstance(entries, list)
    assert entries


def test_fetch_unknown(directory):
    assert not directory.exists('Abitbol')
