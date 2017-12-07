# coding: utf-8
"""
Functions to check for naming duplicates on the Nuxeo Platform with the Nuxeo Python Client module.
To install it:
    pip install nuxeo

Check can be performed either by:
    -  Targeting a folder and check recursively for all duplicates, e.g.:
        python find_duplicates.py --folder /default-domain/workspaces/Foo

    -  Targeting a file by its uid and check if it has a duplicate, e.g.:
        python find_duplicates.py --uid 40d74ed3-5e80-4b4a-91fd-5692d43a136d

    -  Targeting a file by its name and check if it has a duplicate, eg.g:
        python find_duplicates.py --title text.txt

Example output:
    /default-domain/workspaces/Foo/Bar/n appears 3 times with following uids:
    40d74ed3-5e80-4b4a-91fd-5692d43a136d
    3a6c43ef-b8e8-4977-80ad-a086aace680f
    25f3267a-bfa4-4d1b-a50d-8dbe913e54f4
    /default-domain/workspaces/Foo/test1 appears 2 times with following uids:
    707e6ea7-a7c1-49aa-b3bd-764d27e6f3ef
    54969ca5-0be2-4bbf-938a-3e8b4016e420
"""

import argparse
import os
import re
import urllib
from collections import defaultdict
from urllib2 import HTTPError

from nuxeo import Nuxeo


class BColors(object):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


base_url = os.environ.get('NXDRIVE_TEST_SERVER_URL',
                          'http://localhost:8080/nuxeo'),
auth = {
    'username': os.environ.get('NXDRIVE_TEST_USER', 'Administrator'),
    'password': os.environ.get('NXDRIVE_TEST_PASSWORD', 'Administrator'),
}

nuxeo = Nuxeo(base_url=base_url, auth=auth)


def color_print(text, color):
    print('{}{}{}'.format(color, text, BColors.ENDC))


def print_duplicates(path, uids):
    print('{}\'{}\'{} appears {} times with following uids:\n{}'.format(
        BColors.OKBLUE, path, BColors.ENDC, len(uids), unicode_join(uids, '\n')))


def unicode_join(array, spacer=''):
    return spacer.join([x.encode('utf-8') for x in array])


def compute_uid_line(item):
    if item['state'] == 'deleted':
        return unicode_join([item['uid'], ' (deleted)'])
    else:
        return item['uid']


def find_duplicates_in_folder(folder):
    operation = nuxeo.operation('Document.GetChildren')
    operation.input(folder)
    children = operation.execute()
    doc_names = defaultdict(list)

    for doc in children['entries']:
        if 'Folderish' in doc['facets']:
            find_duplicates_in_folder(doc['path'])
        else:
            doc_names[doc['title']].append(compute_uid_line(doc))

    for name, uids in doc_names.iteritems():
        if len(uids) > 1:
            print_duplicates(unicode_join([folder, name]), uids)


def find_duplicates_of_uid(uid):
    if not re.match('^[a-fA-F\d]{8}-[a-fA-F\d]{4}-[a-fA-F\d]{4}-[a-fA-F\d]{4}-[a-fA-F\d]{12}$', uid):
        color_print('Not a valid uid.', BColors.FAIL)
    else:
        try:
            doc = nuxeo.repository().fetch(uid)
            query = "SELECT * FROM Document WHERE ecm:parentId = '" + doc.parentRef + "'"
            query += " AND dc:title = '" + doc.title + "'"
            request = 'query?query=' + urllib.quote(query.encode('utf-8'), safe='!=:')
            entries = nuxeo.request(request).get('entries')
            if len(entries) > 1:
                print_duplicates(unicode_join([doc.path.rsplit('/', 1)[0], doc.title], '/'),
                                 [compute_uid_line(x) for x in entries])
            else:
                color_print('No duplicate for the document with uid={}.'.format(uid), BColors.OKGREEN)
        except HTTPError as e:
            if e.code == 404:
                color_print('No document with uid={}.'.format(uid), BColors.FAIL)


def find_duplicates_with_name(name):
    operation = nuxeo.operation('Document.FetchByProperty')
    operation.params({'property': 'dc:title', 'values': name})
    docs = operation.execute()
    doc_paths = defaultdict(list)
    for doc in docs['entries']:
        doc_paths[doc['path'].rsplit('/', 1)[0]].append(compute_uid_line(doc))

    no_duplicates = True
    for path, uids in doc_paths.iteritems():
        if len(uids) > 1:
            no_duplicates = False
            print_duplicates(unicode_join([path, name]), uids)
    if no_duplicates:
        color_print('No duplicate for {}.'.format(name.encode('utf-8')), BColors.OKGREEN)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--folder')
    p.add_argument('--uid')
    p.add_argument('--title')
    args = p.parse_args()

    if args.folder:
        find_duplicates_in_folder(args.folder)
    if args.uid:
        find_duplicates_of_uid(args.uid)
    if args.title:
        find_duplicates_with_name(args.title)


if __name__ == '__main__':
    exit(main())
