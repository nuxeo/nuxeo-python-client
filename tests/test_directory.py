__author__ = 'loopingz'


from test_nuxeo import NuxeoTest
from nuxeo.document import Document
from urllib2 import HTTPError


class DirectoryTest(NuxeoTest):

    def setUp(self):
        super(DirectoryTest, self).setUp()
        self._directory = self._nuxeo.directory('nature')
        try:
            entry = self._directory.fetch('foo')
            entry.delete()
        except Exception:
            pass

    def test_fetch_all(self):
        entries = self._directory.fetchAll()
        self.assertIsNotNone(entries)
        self.assertTrue(isinstance(entries, list))
        self.assertTrue(len(entries) > 0)

    def test_fetch(self):
        entry = self._directory.fetch('article')
        self.assertEqual(entry.entity_type, 'directoryEntry')
        self.assertEqual(entry.directoryName, 'nature')
        self.assertEqual(entry.properties['id'], 'article')
        self.assertEqual(entry.get_id(), 'article')
        self.assertEqual(entry.properties['label'], 'label.directories.nature.article')

    def test_fetch_unknown(self):
        with self.assertRaises(HTTPError) as ex:
            entry = self._directory.fetch('Abitbol')
        self.assertEqual(ex.exception.code, 404)

    def test_crud(self):
        newEntry = {'id': 'foo', 'label': 'Foo'}
        entry = self._directory.create(newEntry)
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
