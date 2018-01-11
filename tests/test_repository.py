# coding: utf-8
from __future__ import unicode_literals

import operator
import pytest

from nuxeo.compat import get_bytes, get_error_message
from nuxeo.exceptions import HTTPError, UnavailableConvertor
from nuxeo.models import BufferBlob, Document


class Doc:

    def __init__(self, server, with_blob=False):
        self.server = server
        self.blob = with_blob

    def __enter__(self):
        doc = Document(
            name=pytest.ws_python_test_name,
            type='File',
            properties={
                'dc:title': 'bar.txt',
            }
        )
        self.doc = self.server.documents.create(
            doc, parent_path=pytest.ws_root_path)

        if self.blob:
            blob = BufferBlob(
                data='foo',
                name='foo.txt',
                mimetype='text/plain'
            )
            batch = self.server.uploads.batch()
            blob = batch.upload(blob)
            self.doc.properties['file:content'] = blob
            self.doc.save()
        return self.doc

    def __exit__(self, *args):
        self.doc.delete()


def test_add_remove_permission(server):
    with Doc(server) as doc:
        doc.add_permission({'username': 'members', 'permission': 'Write'})
        acls = doc.fetch_acls()
        assert len(acls) == 2
        assert acls[0]['name'] == 'local'
        assert acls[0]['aces'][0]['id'] == 'members:Write:true:Administrator::'
        doc.remove_permission({'id': 'members:Write:true:Administrator::'})
        acls = doc.fetch_acls()
        assert len(acls) == 1
        assert acls[0]['name'] == 'inherited'


def test_bogus_converter(server):
    with Doc(server, with_blob=True) as doc:
        with pytest.raises(ValueError) as e:
            doc.convert({'converter': 'converterthatdoesntexist'})
        msg = get_error_message(e.value)
        assert msg == 'Converter converterthatdoesntexist is not registered'


def test_convert(server):
    with Doc(server, with_blob=True) as doc:
        try:
            res = doc.convert({'format': 'html'})
            assert '<html>' in res
            assert 'foo' in res
        except UnavailableConvertor:
            pass


def test_convert_given_converter(server):
    with Doc(server, with_blob=True) as doc:
        try:
            res = doc.convert({'converter': 'office2html'})
            assert '<html>' in res
            assert 'foo' in res
        except UnavailableConvertor:
            pass


def test_convert_missing_args(server):
    with Doc(server, with_blob=True) as doc:
        with pytest.raises(ValueError):
            doc.convert({})


def test_convert_xpath(server):
    with Doc(server, with_blob=True) as doc:
        try:
            res = doc.convert({'xpath': 'file:content', 'type': 'text/html'})
            assert '<html>' in res
            assert 'foo' in res
        except UnavailableConvertor:
            pass


def test_create_doc_and_delete(server):
    doc = Document(
        name=pytest.ws_python_test_name,
        type='Workspace',
        properties={
          'dc:title': 'foo',
        })
    doc = server.documents.create(doc, parent_path=pytest.ws_root_path)
    try:
        assert isinstance(doc, Document)
        assert doc.path == pytest.ws_python_tests_path
        assert doc.type == 'Workspace'
        assert doc.properties['dc:title'] == 'foo'
        assert server.documents.exists(path=pytest.ws_python_tests_path)
    finally:
        doc.delete()
    assert not server.documents.exists(path=pytest.ws_python_tests_path)


def test_create_doc_with_space_and_delete(server):
    doc = Document(
        name='my domain',
        type='Workspace',
        properties={
          'dc:title': 'My domain',
        })
    doc = server.documents.create(doc, parent_path=pytest.ws_root_path)
    try:
        assert isinstance(doc, Document)
        server.documents.get(path=pytest.ws_root_path + '/my domain')
    finally:
        doc.delete()


def test_fetch_acls(server):
    with Doc(server) as doc:
        acls = doc.fetch_acls()
        assert len(acls) == 1
        assert acls[0]['name'] == 'inherited'
        aces = list(sorted(acls[0]['aces'], key=operator.itemgetter('id')))
        assert aces[0]['id'] == 'Administrator:Everything:true:::'
        assert aces[-1]['id'] == 'members:Read:true:::'


def test_fetch_blob(server):
    with Doc(server, with_blob=True) as doc:
        assert doc.fetch_blob() == b'foo'


def test_fetch_non_existing(server):
    assert not server.documents.exists(path='/zone51')


def test_fetch_rendition(server):
    with Doc(server, with_blob=True) as doc:
        res = doc.fetch_rendition('xmlExport')
        assert b'<?xml version="1.0" encoding="UTF-8"?>' in res
        path = '<path>' + pytest.ws_python_tests_path[1:] + '</path>'
        assert get_bytes(path) in res


def test_fetch_renditions(server):
    with Doc(server, with_blob=True) as doc:
        res = doc.fetch_renditions()
        assert 'thumbnail' in res
        assert 'xmlExport' in res
        assert 'zipExport' in res


def test_fetch_root(server):
    root = server.documents.get(path='/')
    assert isinstance(root, Document)


def test_has_permission(server):
    with Doc(server) as doc:
        assert doc.has_permission('Write')
        assert not doc.has_permission('Foo')


def test_locking(server):
    with Doc(server) as doc:
        assert not doc.fetch_lock_status()
        assert not doc.is_locked()
        doc.lock()
        status = doc.fetch_lock_status()
        assert status['lockOwner'] == 'Administrator'
        assert 'lockCreated' in status
        assert doc.is_locked()
        with pytest.raises(HTTPError):
            doc.lock()
        doc.unlock()
        assert not doc.is_locked()


def test_page_provider(server):
    doc = server.documents.get(path='/default-domain')
    docs = server.documents.query({
        'pageProvider': 'CURRENT_DOC_CHILDREN',
        'queryParams': [doc.uid]
    })
    assert docs['numberOfPages'] == 1
    assert docs['resultsCount'] == 3
    assert docs['currentPageSize'] == 3
    assert not docs['currentPageIndex']
    assert len(docs['entries']) == 3


def test_page_provider_pagination(server):
    doc = server.documents.get(path='/default-domain')
    docs = server.documents.query({
        'pageProvider': 'document_content',
        'queryParams': [doc.uid],
        'pageSize': 1,
        'currentPageIndex': 0,
        'sortBy': 'dc:title',
        'sortOrder': 'asc'
    })
    assert docs['currentPageSize'] == 1
    assert not docs['currentPageIndex']
    assert docs['isNextPageAvailable']
    assert len(docs['entries']) == 1
    assert isinstance(docs['entries'][0], Document)
    assert docs['entries'][0].title
    docs = server.documents.query({
        'pageProvider': 'document_content',
        'queryParams': [doc.uid],
        'pageSize': 1,
        'currentPageIndex': 1,
        'sortBy': 'dc:title',
        'sortOrder': 'asc'
    })
    assert docs['currentPageSize'] == 1
    assert docs['currentPageIndex'] == 1
    assert docs['isNextPageAvailable']
    assert len(docs['entries']) == 1
    assert isinstance(docs['entries'][0], Document)
    assert docs['entries'][0].title == 'Templates'
    docs = server.documents.query({
        'pageProvider': 'document_content',
        'queryParams': [doc.uid],
        'pageSize': 1,
        'currentPageIndex': 2,
        'sortBy': 'dc:title',
        'sortOrder': 'asc'
    })
    assert docs['currentPageSize'] == 1
    assert docs['currentPageIndex'] == 2
    assert not docs['isNextPageAvailable']
    assert len(docs['entries']) == 1
    assert isinstance(docs['entries'][0], Document)
    assert docs['entries'][0].title


def test_query(server):
    docs = server.documents.query({
        'query': 'SELECT * FROM Document WHERE ecm:primaryType = \'Domain\''})
    assert docs['numberOfPages'] == 1
    assert docs['resultsCount'] == 1
    assert docs['currentPageSize'] == 1
    assert not docs['currentPageIndex']
    assert len(docs['entries']) == 1
    assert isinstance(docs['entries'][0], Document)


def test_query_missing_args(server):
    with pytest.raises(ValueError):
        server.documents.query({})


def test_update_doc_and_delete(server):
    doc = Document(
        name=pytest.ws_python_test_name,
        type='Workspace',
        properties={
            'dc:title': 'foo',
        })
    doc = server.documents.create(doc, parent_path=pytest.ws_root_path)
    assert doc
    try:
        uid = doc.uid
        path = doc.path
        doc.set({'dc:title': 'bar'})
        doc.save()
        doc = server.documents.get(path=pytest.ws_python_tests_path)
        assert isinstance(doc, Document)
        assert doc.uid == uid
        assert doc.path == path
        assert doc.properties['dc:title'] == 'bar'
    finally:
        doc.delete()


def test_update_wrong_args(server):
    with pytest.raises(ValueError):
        server.documents.query({})
