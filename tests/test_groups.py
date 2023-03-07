# coding: utf-8
import time

import pytest
from nuxeo.exceptions import BadQuery
from nuxeo.models import Group

from .constants import SSL_VERIFY


def get_group(server):
    existed_group = None
    try:
        existed_group = server.groups.get("plops", ssl_verify=SSL_VERIFY)
        existed_group.delete(ssl_verify=SSL_VERIFY)
    except Exception as e:
        print("Exception in get_group: ", e)

    group = Group(
        groupname="plops",
        grouplabel="Group Test",
        memberUsers=["Administrator"],
        memberGroups=["Administrators"],
    )
    assert repr(group)
    return server.groups.create(group, ssl_verify=SSL_VERIFY)


def test_create_delete_group_dict(server):
    get_group(server)
    try:
        group = server.groups.get("plops", ssl_verify=SSL_VERIFY)
        assert group.groupname == "plops"
        assert group.grouplabel == "Group Test"
        assert group.memberUsers == ["Administrator"]
        assert group.memberGroups == ["Administrators"]
    finally:
        group.delete(ssl_verify=SSL_VERIFY)

        assert not server.groups.exists("plops", ssl_verify=SSL_VERIFY)


def test_create_delete_subgroup(server):

    # cerate first group
    group_1 = Group(groupname="ParentGroup", grouplabel="ParentGroup Test")
    try:
        if server.groups.exists("ParentGroup", ssl_verify=SSL_VERIFY):
            group1 = server.groups.get("ParentGroup", ssl_verify=SSL_VERIFY)
            group1.delete(ssl_verify=SSL_VERIFY)
            print("Existing ParentGroup deleted")
    finally:
        group1 = server.groups.create(group_1, ssl_verify=SSL_VERIFY)
        print("ParentGroup created")

    # Create second group
    group_2 = Group(groupname="SubGroup", grouplabel="SubGroup Test")
    try:
        if server.groups.exists("SubGroup", ssl_verify=SSL_VERIFY):
            group2 = server.groups.get("SubGroup", ssl_verify=SSL_VERIFY)
            group2.delete(ssl_verify=SSL_VERIFY)
            print("Existing SubGroup deleted")
    finally:
        group2 = server.groups.create(group_2, ssl_verify=SSL_VERIFY)
        print("SubGroup created")

    # Add group2 to subgroups of group1
    group1.memberGroups = [group2.groupname]
    group1.save()

    group2.delete(ssl_verify=SSL_VERIFY)
    print("ParentGroup deleted finally")
    group1.delete(ssl_verify=SSL_VERIFY)
    print("ubGroup deleted finally")


def test_create_wrong_arguments(server):
    with pytest.raises(BadQuery):
        server.groups.create(1, ssl_verify=SSL_VERIFY)


def test_fetch(server):
    assert server.groups.get("administrators", ssl_verify=SSL_VERIFY)


def test_fetch_unknown_group(server):
    assert not server.groups.exists("admins", ssl_verify=SSL_VERIFY)


def test_update_group(server):
    group = get_group(server)
    try:
        grouplabel = str(int(round(time.time() * 1000)))
        group.grouplabel = grouplabel
        group.save()
        group = server.groups.get("plops", ssl_verify=SSL_VERIFY)
        assert group.grouplabel == grouplabel
    finally:
        group.delete(ssl_verify=SSL_VERIFY)
