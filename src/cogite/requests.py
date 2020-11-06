from json import dumps as json_dumps
from json import loads as json_loads
import urllib.parse
import urllib.request

from cogite import errors
from cogite.version import VERSION


TIMEOUT = 2  # seconds


def send(method, url, query=None, data=None, json=None, headers=None):
    if query:
        url += "?" + urllib.parse.urlencode(query)
    if bool(json) and bool(data):
        raise ValueError("You cannot use both `json` and `data` arguments.")
    if not headers:
        headers = {}
    headers["User-Agent"] = f"cogite {VERSION}"
    if data:
        data = urllib.parse.urlencode(data)
    elif json:
        data = json_dumps(json)
        headers['Content-Type'] = 'application/json'
    if data:
        data = data.encode('utf-8')
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )
    try:
        return urllib.request.urlopen(request, timeout=TIMEOUT)
    except Exception as exc:
        error = f"Got error when sending {method} request to {url}: {exc}"
        # We could perhaps raise a more specific error (such as
        # RequestException), but most of those will be fatal anyway.
        raise errors.FatalError(error) from exc


class Session:
    def __init__(self, auth_token):
        self.headers = {
            "Authorization": f"bearer {auth_token}",
        }

    def request(self, method, url, query=None, data=None, json=None):
        response = send(
            method,
            url,
            query=query,
            data=data,
            json=json,
            headers=self.headers,
        )
        # FIXME: should we return the response itself so that the
        # caller can check the response code? It then should be the
        # caller's duty to JSON-decode the response. Alternative:
        # return a custom Response object:
        # class Response:
        #   status_code: int
        #   content: Optional[str]
        #   data: Optional[dict]
        return json_loads(response.read())

    def get(self, url, query=None):
        return self.request('GET', url, query=query)

    def post(self, url, data=None, json=None):
        return self.request('POST', url, data=data, json=json)
