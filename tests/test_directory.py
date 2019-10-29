# coding: utf-8
from __future__ import unicode_literals
from functools import partial

import pytest
from nuxeo.exceptions import BadQuery
from nuxeo.models import DirectoryEntry


def test_create_wrong_arguments(directory):
    with pytest.raises(BadQuery):
        directory.create(1)


def test_crud(directory):
    new_entry = DirectoryEntry(properties={"id": "foo", "label": "Foo"})
    entry = directory.create(new_entry)
    try:
        assert entry.entity_type == "directoryEntry"
        assert entry.directoryName == "nature"
        assert entry.properties["id"] == "foo"
        assert entry.uid == "foo"
        assert entry.properties["label"] == "Foo"
        assert repr(entry)

        entry.properties["label"] = "Test"
        entry.save()
        entry = directory.get("foo")
        assert entry.properties["label"] == "Test"

        entry.properties["label"] = "Foo"
        directory.save(entry)
        entry = directory.get("foo")
        assert entry.properties["label"] == "Foo"
    finally:
        entry.delete()


def test_fetch(directory):
    entry = directory.get("article")
    assert entry.entity_type == "directoryEntry"
    assert entry.directoryName == "nature"
    assert entry.properties["id"] == "article"
    assert entry.uid == "article"
    assert entry.properties["label"] == "label.directories.nature.article"


def test_fetch_all(directory):
    entries = directory.entries
    assert directory.as_dict()
    assert isinstance(entries, list)
    assert entries


def test_fetch_unknown(directory):
    assert not directory.exists("Abitbol")


def test_additionnal_params(server):
    func = partial(server.directories.get, "nature")

    # The number of returned entries is configured by the querySizeLimit parameters on the server (50 by default)
    # https://github.com/nuxeo/nuxeo/blob/82d0328/nuxeo-distribution/nuxeo-nxr-server/src/main/resources/templates/common/config/default-directories-bundle.xml#L23
    total = len(func().entries)

    # Get only 10 entries
    assert len(func(pageSize=10).entries) == 10

    # Get all entries
    assert len(func(pageSize=total).entries) == total

    # Get the last page of entries
    page_number, count = divmod(total, 10)
    assert len(func(pageSize=10, currentPageIndex=page_number).entries) == count

    # Set an invalid/unknown parameter does not raise
    assert len(func(pageSizesssssssss=10).entries) == total
