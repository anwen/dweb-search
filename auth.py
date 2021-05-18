from tornado.auth import OAuth2Mixin
from tornado.auth import _auth_return_future
from tornado.stack_context import wrap
from tornado.concurrent import future_set_result_unless_cancelled
import functools
from tornado.util import PY3
if PY3:
    import urllib.parse as urllib_parse
    long = int
else:
    import urllib as urllib_parse


class AuthError(Exception):
    pass


class GithubMixin2(OAuth2Mixin):
    _API_BASE_HEADERS = {
        'Accept': 'application/json',
        'User-Agent': 'Tornado OAuth'
    }
    _OAUTH_ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token'

    @_auth_return_future
    def get_authenticated_user(self, code, callback, client_id, client_secret=None):
        http = self.get_auth_http_client()
        body = urllib_parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            'code': code,
        })
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        headers['Accept'] = 'application/json'
        fut = http.fetch(self._OAUTH_ACCESS_TOKEN_URL,
                         method="POST",
                         headers=headers,
                         body=body)
        fut.add_done_callback(wrap(functools.partial(self._on_access_token, callback)))

    def _on_access_token(self, future, response_fut):
        """Callback function for the exchange to the access token."""
        try:
            response = response_fut.result()
        except Exception as e:
            future.set_exception(AuthError('Github auth error: %s' % str(e)))
            return
        args = response.body
        future_set_result_unless_cancelled(future, args)
