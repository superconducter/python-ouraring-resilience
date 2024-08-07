import requests
from requests_oauthlib import OAuth2Session


class OuraOAuth2Client:
    """
    Use this for authorizing user and obtaining initial access and refresh token.
    Should be one time usage per user.
    """

    AUTHORIZE_BASE_URL = "https://cloud.ouraring.com/oauth/authorize"
    TOKEN_BASE_URL = "https://api.ouraring.com/oauth/token"
    SCOPE = ["email", "personal", "daily", "heartrate", "workout", "tag", "session", "resilience"]

    def __init__(self, client_id, client_secret):
        """
        Initialize the client for oauth flow.

        :param client_id: The client id from oura portal.
        :type client_id: str
        :param client_secret: The client secret from oura portal.
        :type client_secret: str
        """
        self.client_id = client_id
        self.client_secret = client_secret

        self.session = OAuth2Session(
            client_id,
            auto_refresh_url=self.TOKEN_BASE_URL,
        )

    def authorize_endpoint(self, scope=None, redirect_uri=None, **kwargs):
        """
        Build the authorization url for a user to click.

        :param scope: Scopes to request from the user. Defaults to self.SCOPE
        :type scope: str
        :param redirect_uri: Where to redirect after user grants access.
        :type redirect_uri: str
        """
        self.session.scope = scope or self.SCOPE
        if redirect_uri:
            self.session.redirect_uri = redirect_uri
        return self.session.authorization_url(self.AUTHORIZE_BASE_URL, **kwargs)

    def fetch_access_token(self, code):
        """
        Exchange the auth code for an access and refresh token.

        :param code: Authorization code from query string
        :type code: str
        """
        return self.session.fetch_token(
            self.TOKEN_BASE_URL, code=code, client_secret=self.client_secret
        )


class OAuthRequestHandler:
    TOKEN_BASE_URL = "https://api.ouraring.com/oauth/token"
    TOKEN_REVOKE_URL = "https://api.ouraring.com/oauth/revoke"

    def __init__(
        self,
        client_id,
        client_secret=None,
        access_token=None,
        refresh_token=None,
        refresh_callback=None,
    ):

        self.client_id = client_id
        self.client_secret = client_secret

        token = {}
        if access_token:
            token["access_token"] = access_token
        if refresh_token:
            token["refresh_token"] = refresh_token

        self._session = OAuth2Session(
            client_id,
            token=token,
            auto_refresh_url=self.TOKEN_BASE_URL,
            token_updater=refresh_callback,
        )

    def make_request(self, url, method="GET"):
        response = self._session.request(method, url)
        if response.status_code == 401:
            self._refresh_token()
            response = self._session.request(method, url)
        return response

    def make_request_v2(self, url, method="GET"):
        return self.make_request(url, method)

    def _refresh_token(self):
        token = self._session.refresh_token(
            self.TOKEN_BASE_URL,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        if self._session.token_updater:
            self._session.token_updater(token)

        return token

    def revoke_token(self):
        return self._session.request("POST", self.TOKEN_REVOKE_URL)


class PersonalRequestHandler:
    TOKEN_REVOKE_URL = "https://api.ouraring.com/oauth/revoke"

    def __init__(self, personal_access_token):
        self.personal_access_token = personal_access_token

    def make_request(self, url, method="GET"):
        requests_method = requests.post if method == "POST" else requests.get
        return requests_method(url, params={"access_token": self.personal_access_token})

    def make_request_v2(self, url, method="GET"):
        requests_method = requests.post if method == "POST" else requests.get
        headers = {"Authorization": f"Bearer {self.personal_access_token}"}
        return requests_method(url, headers=headers)

    def revoke_token(self):
        return self.make_request_v2(self.TOKEN_REVOKE_URL, "POST")
