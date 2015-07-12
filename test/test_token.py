from unittest import TestCase
from unittest.mock import patch
import datetime

from pgsheets import Client, Token
from pgsheets.exceptions import PGSheetsHTTPException


class TestClient(TestCase):

    @patch("pgsheets.token.requests.get")
    @patch("pgsheets.token.requests.post")
    def test_initialization(self, post, get):
        # Initializing a Client object does not cause any API calls
        Client("client_id", "client_secret")
        self.assertFalse(get.called,
                         "intialization should not cause any API calls")
        self.assertFalse(post.called,
                         "intialization should not cause any API calls")

    @patch("pgsheets.token.requests.get")
    @patch("pgsheets.token.requests.post")
    def test_get_refresh_token(self, post, get):
        # feed data from:
        # https://developers.google.com/google-apps/spreadsheets/authorize
        # Example url from:
        # https://developers.google.com/identity/protocols/OAuth2InstalledApp
        client_id = ("812741506391-h38jh0j4fv0ce1krdkiq0hfvt6n5amrf.apps."
                     "googleusercontent.com")
        client_secret = "client_secret"
        redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

        # 1) A user gets the permission URL from the getOauthUrl() method

        c = Client(client_id, client_secret)

        expected = (
            "https://accounts.google.com/o/oauth2/auth?"
            "scope={}&"
            "redirect_uri={}&"
            "response_type=code&"
            "client_id={}"
            .format(
                "https%3A//spreadsheets.google.com/feeds",
                redirect_uri,
                client_id
                ))

        self.assertEqual(c.getOauthUrl(), expected)
        self.assertFalse(get.called, "No API calls are made")
        self.assertFalse(post.called, "No API calls are made")

        # 2) The user then supplies the value from Google to getRefreshToken()

        post.return_value.status_code = 200
        post.return_value.content = """
        {
          "access_token":"1/fFAGRNJru1FTz70BzhT3Zg",
          "expires_in":3920,
          "token_type":"Bearer",
          "refresh_token":"1/xEoDL4iW3cxlI7yDbSRFYNG01kVKM2C-259HOF2aQbI"
        }
        """.encode()

        token = c.getRefreshToken("fake_code")

        self.assertFalse(get.called, "No GET API calls are made")
        self.assertTrue(post.called)
        self.assertEqual(token,
                         "1/xEoDL4iW3cxlI7yDbSRFYNG01kVKM2C-259HOF2aQbI")

    @patch("pgsheets.token.requests.get")
    @patch("pgsheets.token.requests.post")
    def test_bad_call(self, post, get):
        # a bad HTTP status code causes a PGSheetsHTTPException exception
        post.return_value.status = 501
        post.return_value.content = b''
        c = Client("client_id", "client_secret")
        with self.assertRaises(PGSheetsHTTPException):
            c.getRefreshToken("fake_code")


class TestToken(TestCase):

    @patch("pgsheets.token.requests.get")
    @patch("pgsheets.token.requests.post")
    def test_get_header(self, post, get):
        refresh_token = 'refresh'
        client_id = "client_id"
        client_secret = "client_secret"

        c = Client(client_id, client_secret)
        t = Token(c, refresh_token)

        post.return_value.status_code = 200
        post.return_value.content = b"""
        {
          "access_token":"1/fFBGRNJru1FQd44AzqT3Zg",
          "expires_in":3920,
          "token_type":"Bearer"
        }"""

        h = t.getAuthorizationHeader()

        # https://www.googleapis.com/oauth2/v3/token was called
        pos, kwargs = post.call_args
        self.assertEqual(pos[0], "https://www.googleapis.com/oauth2/v3/token")
        self.assertIn('data', kwargs)
        self.assertEqual(set(kwargs['data'].keys()),
                         {'refresh_token', 'client_id', 'client_secret',
                          'grant_type'})
        self.assertEqual(kwargs['data']['refresh_token'], refresh_token)
        self.assertEqual(kwargs['data']['client_id'], client_id)
        self.assertEqual(kwargs['data']['client_secret'], client_secret)
        self.assertEqual(kwargs['data']['grant_type'], "refresh_token")

        # h is a simple dictionary
        self.assertEqual(h,
                         {'Authorization': 'Bearer 1/fFBGRNJru1FQd44AzqT3Zg'})

        # Another call should get the same header without another API call
        post.reset_mock()
        h = t.getAuthorizationHeader({'test': 1})
        self.assertEqual(h,
                         {'Authorization': 'Bearer 1/fFBGRNJru1FQd44AzqT3Zg',
                          'test': 1})
        self.assertFalse(post.called)

        # Once the timeout has passed we get a new token
        post.status_code = 200
        post.return_value.content = b"""
        {
          "access_token":"new_token",
          "expires_in":3920,
          "token_type":"Bearer"
        }"""
        t._expires = datetime.datetime.utcnow()
        h = t.getAuthorizationHeader()
        self.assertEqual(h, {'Authorization': 'Bearer new_token'})

        # We never make any get requests
        self.assertFalse(get.called)

    @patch("pgsheets.token.requests.get")
    @patch("pgsheets.token.requests.post")
    def test_exception(self, post, get):
        # A bad HTTP code causes a PGSheetsHTTPException
        post.return_value.content = b''
        post.return_value.status = 500
        c = Client("client_id", "client_secret")
        t = Token(c, "refresh_token")
        with self.assertRaises(PGSheetsHTTPException):
            t.getAuthorizationHeader()
        self.assertFalse(get.called)
