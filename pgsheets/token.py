import urllib.parse
import json
import datetime

import requests

from pgsheets.exceptions import _check_status


class Client():
    """Represent an application's Google's client data, along with methods for
    getting a refresh token.

    A refresh token is required to intialize a Token object.
    """

    def __init__(self, client_id, client_secret, **kwargs):
        super().__init__(**kwargs)
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

    def getOauthUrl(self):
        """Returns the oauth url a user can put in their browser.
        This is requried to get Google's authorization code.

        Provide the returned code to the getRefreshToken() method to get a
        token that can be used repeatedly in the future.
        """
        scope = urllib.parse.quote('https://spreadsheets.google.com/feeds')

        return (
            "https://accounts.google.com/o/oauth2/auth?"
            "scope={scope}&"
            "redirect_uri={redirect_uri}&"
            "response_type=code&"
            "client_id={client_id}".format(
                client_id=self._client_id,
                redirect_uri=self._redirect_uri,
                scope=scope)
            )

    def getRefreshToken(self, user_code):
        """Using the user token provided by visiting the url from getOauthUrl()
        returns a refresh token (a string).

        You should persist the token and use it on future Token initializations
        This method calls the Google API
        """
        r = requests.post(
            'https://www.googleapis.com/oauth2/v3/token',
            data={
                'code': user_code,
                'client_id': self._client_id,
                'client_secret': self._client_secret,
                'redirect_uri': self._redirect_uri,
                'grant_type': 'authorization_code',
                })

        _check_status(r)

        # Returns a dictionary with the keys:
        #   access_token
        #   expires_in
        #   refresh_token
        #   'token_type': 'Bearer'
        data = json.loads(r.content.decode())
        return data['refresh_token']


class Token():
    _REFRSH_TOKEN_SLACK = 100

    def __init__(self, client, refresh_token, **kwargs):
        """Initializes a SheetsRequest object.

        The refresh_token should be stored and provided on all
        initializations of any particular client and Google user.
        """
        super().__init__(**kwargs)
        self._client = client
        self._refresh_token = refresh_token
        self._expires = None

    def _setExpiresTime(self, request_time, expires):
        expires = int(expires)

        # we underestimate the estimate time slightly
        assert expires > self._REFRSH_TOKEN_SLACK, (expires,
                                                    self._REFRSH_TOKEN_SLACK)
        expires -= self._REFRSH_TOKEN_SLACK

        self._expires = request_time + datetime.timedelta(seconds=expires)

    def _refreshToken(self):
        """Gets a new access token.
        """
        request_time = datetime.datetime.utcnow()
        r = requests.post(
            'https://www.googleapis.com/oauth2/v3/token',
            data={
                'refresh_token': self._refresh_token,
                'client_id': self._client._client_id,
                'client_secret': self._client._client_secret,
                'grant_type': 'refresh_token',
                })

        _check_status(r)

        # We have a dictionary with the keys
        #   access_token
        #   expires_in
        #   'token_type': 'Bearer'
        data = json.loads(r.content.decode())
        self._access_token = data['access_token']
        self._setExpiresTime(request_time, data['expires_in'])

    def _getValidToken(self):
        """Gets a access token, refreshing as necessary.
        """
        if ((self._expires is None) or (datetime.datetime.utcnow()
                                        >= self._expires)):
            self._refreshToken()
        return self._access_token

    def getAuthorizationHeader(self, headers=None):
        """Returns a dictionary containing a Authorization header.
        If a dictionary is supplied the Authorization header is added.
        """
        if headers is None:
            headers = {}
        headers['Authorization'] = "Bearer " + self._getValidToken()
        return headers
