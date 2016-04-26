__author__ = 'loopingz'


from test_nuxeo import NuxeoTest
from nuxeo.nuxeo import Nuxeo
from urllib2 import HTTPError


class UsersTest(NuxeoTest):

    def tearDown(self):
        try:
            user = self._nuxeo.users().fetch('georges')
            user.delete()
        except Exception:
            pass

    def test_fetch(self):
        user = self._nuxeo.users().fetch('Administrator')
        self.assertIsNotNone(user)
        self.assertIn('administrators', user.properties['groups'])

    def test_fetch_unknown_user(self):
        with self.assertRaises(HTTPError) as ex:
            user = self._nuxeo.users().fetch('Administrator2')
        self.assertEqual(ex.exception.code, 404)

    def test_create_delete_user_dict(self):
        opts = {'lastName': 'Abitbol', 'firstName': 'Georges', 'username': 'georges', 'company': 'Pom Pom Gali resort'}
        user = self._nuxeo.users().create(opts)
        self.assertEqual(user.firstName, 'Georges')
        self.assertEqual(user.lastName, 'Abitbol')
        self.assertEqual(user.company, 'Pom Pom Gali resort')
        user.delete()
        with self.assertRaises(HTTPError) as ex:
            user = self._nuxeo.users().fetch('georges')
        self.assertEqual(ex.exception.code, 404)

    def test_update_user(self):
        import time
        company = str(int(round(time.time() * 1000)))
        opts = {'lastName': 'Abitbol', 'firstName': 'Georges', 'username': 'georges', 'company': 'Pom Pom Gali resort', 'password': 'Test'}
        user = self._nuxeo.users().create(opts)
        user.properties['company'] = company
        user.save()
        user = self._nuxeo.users().fetch('georges')
        self.assertEqual(user.company, company)
        nuxeo = Nuxeo("http://localhost:8080/nuxeo", auth={'username': 'georges', 'password': 'Test'})
        georges = nuxeo.login()
        self.assertIsNotNone(georges)
