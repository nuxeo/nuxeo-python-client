# coding: utf-8
from __future__ import unicode_literals

import operator

import pytest
from requests import HTTPError

from nuxeo.document import Document
from nuxeo.exceptions import UnavailableConvertor


def test_add_remove_permission(doc):
    doc.add_permission({'username': 'members', 'permission': 'Write'})
    acls = doc.fetch_acls()
    assert len(acls) == 2
    assert acls[0]['name'] == 'local'
    assert acls[0]['aces'][0]['id'] == 'members:Write:true:Administrator::'
    doc.remove_permission({'id': 'members:Write:true:Administrator::'})
    acls = doc.fetch_acls()
    assert len(acls) == 1
    assert acls[0]['name'] == 'inherited'


def test_bogus_converter(doc):
    with pytest.raises(ValueError) as e:
        doc.convert({'converter': 'converterthatdoesntexist'})
    assert e.value.message == 'Converter converterthatdoesntexist is not registered'


def test_convert(doc):
    try:
        res = doc.convert({'format': 'html'})
        assert '<html>' in res
        assert 'foo' in res
    except UnavailableConvertor:
        pass
    finally:
        doc.delete()


def test_convert_given_converter(doc):
    try:
        res = doc.convert({'converter': 'office2html'})
        assert '<html>' in res
        assert 'foo' in res
    except UnavailableConvertor:
        pass


def test_convert_xpath(doc):
    try:
        res = doc.convert({'xpath': 'file:content', 'type': 'text/html'})
        assert '<html>' in res
        assert 'foo' in res
    except UnavailableConvertor:
        pass


def test_create_doc_and_delete(repository):
    new_doc = {
        'name': pytest.ws_python_test_name,
        'type': 'Workspace',
        'properties': {
          'dc:title': 'foo',
        }
    }
    doc = repository.create(pytest.ws_root_path, new_doc)
    assert isinstance(doc, Document)
    assert doc.path == pytest.ws_python_tests_path
    assert doc.type == 'Workspace'
    assert doc.properties['dc:title'] == 'foo'
    doc.delete()
    assert not repository.exists(pytest.ws_python_tests_path)


def test_create_doc_with_space_and_delete(repository):
    """ NXPY-14: URLs should be quoted. """

    name = 'my domain'
    new_doc = {
        'name': name,
        'type': 'Workspace',
        'properties': {
            'dc:title': name.title(),
        }
    }
    doc = repository.create(pytest.ws_root_path, new_doc)
    assert isinstance(doc, Document)
    repository.fetch(pytest.ws_root_path + '/' + name)
    doc.delete()


def test_fetch_acls(doc):
    acls = doc.fetch_acls()
    assert len(acls) == 1
    assert acls[0]['name'] == 'inherited'
    aces = list(sorted(acls[0]['aces'], key=operator.itemgetter('id')))
    assert aces[0]['id'] == 'Administrator:Everything:true:::'
    assert aces[1]['id'] == 'members:Read:true:::'


def test_fetch_blob(doc):
    assert doc.fetch_blob() == 'foo'


def test_fetch_non_existing(repository):
    assert not repository.exists('/zone51')


def test_fetch_rendition(doc):
    res = doc.fetch_rendition('xmlExport')
    assert '<?xml version="1.0" encoding="UTF-8"?>' in res
    path = '<path>' + pytest.ws_python_tests_path[1:] + '</path>'
    assert path in res


def test_fetch_renditions(doc):
    res = doc.fetch_renditions()
    assert 'thumbnail' in res
    assert 'xmlExport' in res
    assert 'zipExport' in res


def test_fetch_root(repository):
    root = repository.fetch('/')
    assert isinstance(root, Document)


def test_has_permission(doc):
    assert doc.has_permission('Write')
    assert not doc.has_permission('Foo')


def test_locking(doc):
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


def test_page_provider(repository):
    doc = repository.fetch('/default-domain')
    docs = repository.query({'pageProvider': 'CURRENT_DOC_CHILDREN',
                             'queryParams': [doc.uid]})
    assert docs['numberOfPages'] == 1
    assert docs['resultsCount'] == 3
    assert docs['currentPageSize'] == 3
    assert not docs['currentPageIndex']
    assert len(docs['entries']) == 3


def test_page_provider_pagination(repository):
    doc = repository.fetch('/default-domain')
    docs = repository.query({'pageProvider': 'document_content',
                             'queryParams': [doc.uid],
                             'pageSize': 1,
                             'currentPageIndex': 0,
                             'sortBy': 'dc:title',
                             'sortOrder': 'asc'})
    assert docs['currentPageSize'] == 1
    assert not docs['currentPageIndex']
    assert docs['isNextPageAvailable']
    assert len(docs['entries']) == 1
    assert isinstance(docs['entries'][0], Document)
    assert docs['entries'][0].title
    docs = repository.query({'pageProvider': 'document_content',
                             'queryParams': [doc.uid],
                             'pageSize': 1,
                             'currentPageIndex': 1,
                             'sortBy': 'dc:title',
                             'sortOrder': 'asc'})
    assert docs['currentPageSize'] == 1
    assert docs['currentPageIndex'] == 1
    assert docs['isNextPageAvailable']
    assert len(docs['entries']) == 1
    assert isinstance(docs['entries'][0], Document)
    assert docs['entries'][0].title == 'Templates'
    docs = repository.query({'pageProvider': 'document_content',
                             'queryParams': [doc.uid],
                             'pageSize': 1,
                             'currentPageIndex': 2,
                             'sortBy': 'dc:title',
                             'sortOrder': 'asc'})
    assert docs['currentPageSize'] == 1
    assert docs['currentPageIndex'] == 2
    assert not docs['isNextPageAvailable']
    assert len(docs['entries']) == 1
    assert isinstance(docs['entries'][0], Document)
    assert docs['entries'][0].title


def test_query(repository):
    docs = repository.query({'query': 'SELECT * FROM Document WHERE ecm:primaryType = \'Domain\''})
    assert docs['numberOfPages'] == 1
    assert docs['resultsCount'] == 1
    assert docs['currentPageSize'] == 1
    assert not docs['currentPageIndex']
    assert len(docs['entries']) == 1
    assert isinstance(docs['entries'][0], Document)


def test_update_doc_and_delete(repository):
    new_doc = {
        'name': pytest.ws_python_test_name,
        'type': 'Workspace',
        'properties': {
            'dc:title': 'foo',
        }
    }
    doc = repository.create(pytest.ws_root_path, new_doc)
    assert doc
    uid = doc.uid
    path = doc.path
    doc.set({'dc:title': 'bar'})
    doc.save()
    doc = repository.fetch(pytest.ws_python_tests_path)
    assert isinstance(doc, Document)
    assert doc.uid == uid
    assert doc.path == path
    assert doc.properties['dc:title'] == 'bar'
    doc.delete()
