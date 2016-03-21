from unittest import TestCase
from unittest.mock import patch

from pgsheets import Spreadsheet
from pgsheets.models import Worksheet
from pgsheets.exceptions import PGSheetsHTTPException

from test.api_content import get_spreadsheet_element, \
    get_worksheets_feed, get_worksheet_entry


class MockToken():
    """Mocks a Token class.

    The authorization header it returns is completely fake and
    non-changing.
    """
    token = "non_changing_token"

    def getAuthorizationHeader(self, headers=None):
        if headers is None:
            headers = {}
        headers['Authorization'] = "Bearer {}".format(self.token)
        return headers


class ApiTest(TestCase):
    """Useful methods and setup for get and post calls
    """

    def setUp(self):
        self.get_patch = patch("requests.get")
        self.get = self.get_patch.start()
        self.post_patch = patch("requests.post")
        self.post = self.post_patch.start()
        self.delete_patch = patch("requests.delete")
        self.delete = self.delete_patch.start()

        self.token = MockToken()

    def tearDown(self):
        self.delete_patch.stop()
        self.post_patch.stop()
        self.get_patch.stop()

    def checkGetCall(self, url=None):
        """Test that a Get request was made with appropriate
        authorization headers.

        Optionally can check the url. Resets the called attribute
        """
        self.assertTrue(self.get.called)
        pos, kwargs = self.get.call_args
        assert len(pos) >= 1
        if url is not None:
            self.assertEqual(pos[0], url)
        self.assertIn('headers', kwargs)
        self.assertIn('Authorization', kwargs['headers'])
        self.assertEqual(kwargs['headers']['Authorization'],
                         "Bearer " + self.token.token)
        self.get.called = False

    def checkPostCall(self, url=None):
        """Test that a Post request was made with appropriate
        authorization headers.

        Optionally can check the url. Resets the called attribute
        """
        self.assertTrue(self.post.called)
        pos, kwargs = self.post.call_args
        assert len(pos) >= 1
        if url is not None:
            self.assertEqual(pos[0], url)
        self.assertIn('headers', kwargs)
        self.assertIn('Authorization', kwargs['headers'])
        self.assertEqual(kwargs['headers']['Authorization'],
                         "Bearer " + self.token.token)
        self.post.called = False

    def checkDeleteCall(self, url=None):
        """Test that a Post request was made with appropriate
        authorization headers.

        Optionally can check the url. Resets the called attribute
        """
        self.assertTrue(self.delete.called)
        pos, kwargs = self.delete.call_args
        assert len(pos) >= 1
        if url is not None:
            self.assertEqual(pos[0], url)
        self.assertIn('headers', kwargs)
        self.assertIn('Authorization', kwargs['headers'])

class TestSpreadSheet(ApiTest):

    def test_initialize(self):
        # we should be able to intialize a Spreadsheet with a variety
        # of different URLs
        key = "TESTKEY"
        test_keys = [
            key,  # just using key
            "https://docs.google.com/spreadsheets/d/{}/edit#gid=0"
            .format(key),  # normal url
            "http://docs.google.com/spreadsheets/d/{}/edit#gid=0"
            .format(key),  # not https
            "https://docs.google.com/spreadsheets/d/{}"
            .format(key),  # no trailing slash
            "https://www.docs.google.com/spreadsheets/d/{}"
            .format(key),  # includes www
            "www.docs.google.com/spreadsheets/d/{}"
            .format(key),  # includes www, no http
            "docs.google.com/spreadsheets/d/{}/"
            .format(key),  # no http
            ]

        # check that we call the right URL
        feed_url = ("https://spreadsheets.google.com/feeds/spreadsheets/"
                    "private/full/{}")

        self.get.return_value.status_code = 200
        self.get.return_value.content = get_spreadsheet_element(key=key)
        for k in test_keys:
            s = Spreadsheet(self.token, key)
            self.checkGetCall(url=feed_url.format(key))
            self.assertEqual(s.getKey(), key)

        # a bad key gets an error
        self.get.return_value.status_code = 500
        bad_key = "BAD_KEY"
        with self.assertRaises(PGSheetsHTTPException):
            Spreadsheet(self.token, bad_key)
        self.checkGetCall(url=feed_url.format(bad_key))

        self.assertFalse(self.post.called)

    def getSpreadsheet(self, key="TESTKEY", title="my_title"):
        """Helper method to get a Spreadsheet object by faking an API
        response.
        """
        self.get.return_value.status_code = 200
        self.get.return_value.content = (
            get_spreadsheet_element(key=key, title="my_title"))
        return Spreadsheet(self.token, key)

    def test_getKey_and_getTitle(self):
        s = self.getSpreadsheet("TESTKEY", "my_title")
        self.assertEqual(s.getTitle(), "my_title")
        self.assertEqual(s.getKey(), "TESTKEY")

    def test_repr(self):
        s = self.getSpreadsheet("TESTKEY", "my_title")
        self.assertEqual(repr(s),
                         "<Spreadsheet title='my_title' key='TESTKEY'>")

    def test_getURL(self):
        s = self.getSpreadsheet("TESTKEY", "my_title")
        self.assertEqual(s.getURL(),
                         "https://docs.google.com/spreadsheets/d/{}/edit"
                         .format("TESTKEY"))

    def test_addRemoveWorksheets(self):
        key = "TESTKEY"
        s = self.getSpreadsheet(key, "my_title")

        # get spreadsheets
        self.get.return_value.status_code = 200
        self.get.return_value.content = get_worksheets_feed(
            key=key, sheet_names=["sheet_title"])
        w = s.getWorksheets()
        self.checkGetCall(
            "https://spreadsheets.google.com/feeds/worksheets/{}/private/full"
            .format(key))

        self.assertEqual(type(w), list)
        self.assertEqual(len(w), 1)
        self.assertEqual(type(w[0]), Worksheet)
        w = w[0]

        self.post.return_value.status_code = 201
        self.post.return_value.content = get_worksheet_entry(
            key, "added_sheet_title")
        w = s.addWorksheet("added_sheet_title")
        self.checkPostCall(
            "https://spreadsheets.google.com/feeds/worksheets/{}/private/full"
            .format(key))

        self.assertEqual(type(w), Worksheet)

        self.get.return_value.status_code = 200
        self.get.return_value.content = get_worksheet_entry(
            key, "added_sheet_title")
        title = w.getTitle()
        self.checkGetCall(
            "https://spreadsheets.google.com/feeds/worksheets/{}/private/full/od6"
            .format(key))
        self.assertEqual(title, "added_sheet_title")

        self.delete.return_value.status_code = 200
        self.delete.return_value.content = b''
        s.removeWorksheet(w)
        self.checkDeleteCall(
            "https://spreadsheets.google.com/feeds/worksheets/{}/private/full/od6/CCCC"
            .format(key))

    def test_getWorksheets(self):
        key = "TESTKEY"
        s = self.getSpreadsheet(key, "my_title")

        # get spreadsheets
        self.get.return_value.status_code = 200
        self.get.return_value.content = get_worksheets_feed(
            key=key, sheet_names=["sheet_title"])
        w = s.getWorksheets()
        self.checkGetCall(
            "https://spreadsheets.google.com/feeds/worksheets/{}/private/full"
            .format(key))

        self.assertEqual(type(w), list)
        self.assertEqual(len(w), 1)
        self.assertEqual(type(w[0]), Worksheet)
        w = w[0]

        self.assertEqual(w._getTitle(w._element), "sheet_title")
        self.assertEqual(w._getSheetKey(), s.getKey())

        w = s.getWorksheet('sheet_title')
        self.assertEqual(type(w), Worksheet)
        self.assertEqual(w._getTitle(w._element), "sheet_title")
        self.assertEqual(w._getSheetKey(), s.getKey())

        with self.assertRaises(ValueError):
            s.getWorksheet("fake worksheet")
