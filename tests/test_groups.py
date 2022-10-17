# coding: utf-8
import time

import pytest
from nuxeo.exceptions import BadQuery
from nuxeo.models import Group

from .constants import SSL_VERIFY


def get_group(server):
    existed_group = None
    try:
        if SSL_VERIFY is False:
            existed_group = server.groups.get("plops", ssl_verify=False)
            existed_group.delete(ssl_verify=False)
        else:
            existed_group = server.groups.get("plops")
            existed_group.delete()
    except Exception as e:
        print("Exception in get_group: ", e)

    group = Group(
        groupname="plops",
        grouplabel="Group Test",
        memberUsers=["Administrator"],
        memberGroups=["Administrators"],
    )
    assert repr(group)
    if SSL_VERIFY is False:
        return server.groups.create(group, ssl_verify=False)
    else:
        return server.groups.create(group)


def test_create_delete_group_dict(server):
    get_group(server)
    try:
        if SSL_VERIFY is False:
            group = server.groups.get("plops", ssl_verify=False)
        else:
            group = server.groups.get("plops")
        assert group.groupname == "plops"
        assert group.grouplabel == "Group Test"
        assert group.memberUsers == ["Administrator"]
        assert group.memberGroups == ["Administrators"]
    finally:
        if SSL_VERIFY is False:
            group.delete(ssl_verify=False)
        else:
            group.delete()

        if SSL_VERIFY is False:
            assert not server.groups.exists("plops", ssl_verify=False)
        else:
            assert not server.groups.exists("plops")


def test_create_delete_subgroup(server):

    # cerate first group
    group_1 = Group(groupname="ParentGroup", grouplabel="ParentGroup Test")
    if SSL_VERIFY is False:
        try:
            if server.groups.exists("ParentGroup", ssl_verify=False):
                group1 = server.groups.get("ParentGroup", ssl_verify=False)
                group1.delete(ssl_verify=False)
        finally:
            group1 = server.groups.create(group_1, ssl_verify=False)
    else:
        try:
            if server.groups.exists("ParentGroup"):
                group1 = server.groups.get("ParentGroup")
                group1.delete()
        finally:
            group1 = server.groups.create(group_1)

    # Create second group
    group_2 = Group(groupname="SubGroup", grouplabel="SubGroup Test")
    if SSL_VERIFY is False:
        try:
            group2 = server.groups.get("SubGroup", ssl_verify=False)
            group2.delete(ssl_verify=False)
        finally:
            group2 = server.groups.create(group_2, ssl_verify=False)
    else:
        try:
            group2 = server.groups.get("SubGroup")
            group2.delete()
        finally:
            group2 = server.groups.create(group_2)

    # Add group2 to subgroups of group1
    group1.memberGroups = [group2.groupname]
    group1.save()

    if SSL_VERIFY is False:
        group2.delete(ssl_verify=False)
        group1.delete(ssl_verify=False)
    else:
        group2.delete()
        group1.delete()


def test_create_wrong_arguments(server):
    if SSL_VERIFY is False:
        with pytest.raises(BadQuery):
            server.groups.create(1, ssl_verify=False)
    else:
        with pytest.raises(BadQuery):
            server.groups.create(1)


def test_fetch(server):
    if SSL_VERIFY is False:
        assert server.groups.get("administrators", ssl_verify=False)
    else:
        assert server.groups.get("administrators")


def test_fetch_unknown_group(server):
    if SSL_VERIFY is False:
        assert not server.groups.exists("admins", ssl_verify=False)
    else:
        assert not server.groups.exists("admins")


def test_update_group(server):
    group = get_group(server)
    try:
        grouplabel = str(int(round(time.time() * 1000)))
        group.grouplabel = grouplabel
        group.save()
        if SSL_VERIFY is False:
            group = server.groups.get("plops", ssl_verify=False)
        else:
            group = server.groups.get("plops")
        assert group.grouplabel == grouplabel
    finally:
        if SSL_VERIFY is False:
            group.delete(ssl_verify=False)
        else:
            group.delete()
