# coding: utf-8
from urllib2 import HTTPError

from nuxeo.nuxeo import Nuxeo
from nuxeo.users import User
from .common import NuxeoTest


class UsersTest(NuxeoTest):

    def tearDown(self):
        try:
            user = self.nuxeo.users().fetch('georges')
            user.delete()
        except Exception:
            pass

    def _create_georges(self):
        opts = {'lastName': 'Abitbol', 'firstName': 'Georges', 'username': 'georges', 'company': 'Pom Pom Gali resort', 'password': 'Test'}
        return self.nuxeo.users().create(opts)

    def test_fetch(self):
        user = self.nuxeo.users().fetch('Administrator')
        self.assertIsNotNone(user)
        self.assertIn('administrators', user.properties['groups'])

    def test_fetch_unknown_user(self):
        with self.assertRaises(HTTPError) as ex:
            user = self.nuxeo.users().fetch('Administrator2')
        self.assertEqual(ex.exception.code, 404)

    def test_create_delete_user_dict(self):
        opts = {'lastName': 'Abitbol', 'firstName': 'Georges', 'username': 'georges', 'company': 'Pom Pom Gali resort'}
        user = self.nuxeo.users().create(opts)
        self.assertEqual(user.properties['firstName'], 'Georges')
        self.assertEqual(user.properties['lastName'], 'Abitbol')
        self.assertEqual(user.properties['company'], 'Pom Pom Gali resort')
        user.delete()
        with self.assertRaises(HTTPError) as ex:
            user = self.nuxeo.users().fetch('georges')
        self.assertEqual(ex.exception.code, 404)

    def test_update_user(self):
        import time
        company = str(int(round(time.time() * 1000)))
        user = self._create_georges()
        user.properties['company'] = company
        user.save()
        user = self.nuxeo.users().fetch('georges')
        self.assertEqual(user.properties['company'], company)
        nuxeo = Nuxeo(self.base_url, auth={'username': 'georges', 'password': 'Test'})
        georges = nuxeo.login()
        self.assertIsNotNone(georges)

    def test_update_user_autoset_change_password(self):
        user = self._create_georges()
        user.password = 'Test2'
        user.save()
        self.nuxeo.users().fetch('georges')
        nuxeo = Nuxeo(self.base_url, auth={'username': 'georges', 'password': 'Test2'})
        georges = nuxeo.login()
        self.assertIsNotNone(georges)

    def test_update_user_autoset_change_password_2(self):
        user = self._create_georges()
        user.change_password('Test3')
        nuxeo = Nuxeo(self.base_url, auth={'username': 'georges', 'password': 'Test3'})
        georges = nuxeo.login()
        self.assertIsNotNone(georges)

    def test_lazy_loading(self):
        self._create_georges()
        user = User(service=self.nuxeo.users(), id='georges')
        # TODO Remove when lazy loading is working
        with self.assertRaises(Exception):
            self.assertEqual(user.firstName, 'Georges')
        user.load()
        self.assertEqual(user.properties['firstName'], 'Georges')
        self.assertEqual(user.properties['lastName'], 'Abitbol')
        self.assertEqual(user.properties['company'], 'Pom Pom Gali resort')