# coding: utf-8
from __future__ import unicode_literals

from urllib2 import HTTPError

from .common import NuxeoTest


class DirectoryTest(NuxeoTest):

    def setUp(self):
        super(DirectoryTest, self).setUp()
        self._directory = self.nuxeo.directory('nature')
        try:
            self._directory.fetch('foo').delete()
        except:
            pass

    def test_fetch_all(self):
        entries = self._directory.fetchAll()
        self.assertIsNotNone(entries)
        self.assertIsInstance(entries, list)
        self.assertGreater(len(entries), 0)

    def test_fetch(self):
        entry = self._directory.fetch('article')
        self.assertEqual(entry.entity_type, 'directoryEntry')
        self.assertEqual(entry.directoryName, 'nature')
        self.assertEqual(entry.properties['id'], 'article')
        self.assertEqual(entry.get_id(), 'article')
        self.assertEqual(entry.properties['label'],
                         'label.directories.nature.article')

    def test_fetch_unknown(self):
        with self.assertRaises(HTTPError) as ex:
            self._directory.fetch('Abitbol')
        self.assertEqual(ex.exception.code, 404)

    def test_crud(self):
        new_entry = {'id': 'foo', 'label': 'Foo'}
        entry = self._directory.create(new_entry)
        self.assertEqual(entry.entity_type, 'directoryEntry')
        self.assertEqual(entry.directoryName, 'nature')
        self.assertEqual(entry.properties['id'], 'foo')
        self.assertEqual(entry.get_id(), 'foo')
        self.assertEqual(entry.properties['label'], 'Foo')
        entry.properties['label'] = 'Test'
        entry.save()
        entry = self._directory.fetch('foo')
        self.assertEqual(entry.properties['label'], 'Test')
        entry.delete()
