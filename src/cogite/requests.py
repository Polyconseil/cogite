import dataclasses
from json import JSONDecodeError
from json import dumps as json_dumps
from json import loads as json_loads
from typing import Optional
import urllib.error
import urllib.parse
import urllib.request

from cogite import errors
from cogite.version import VERSION


TIMEOUT = 2  # seconds


@dataclasses.dataclass
class Response:
    status_code: int
    content: str
    data: Optional[dict]


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
        # pylint: disable=consider-using-with
        return urllib.request.urlopen(request, timeout=TIMEOUT)
    except urllib.error.HTTPError as exc:
        content = exc.file.read().decode('utf-8')
        try:
            json = json_loads(content)
        except (TypeError, JSONDecodeError):
            json = None
        error = (
            f"Got non-OK status code {exc.code} when sending {method} "
            f"request to {url}.\n"
            f"Here is the response body: {json or content}"
        )
        raise errors.FatalError(error)
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

    def request(self, method, url, query=None, data=None, json=None) -> Response:
        response = send(
            method,
            url,
            query=query,
            data=data,
            json=json,
            headers=self.headers,
        )
        res = Response(
            status_code=response.status,
            content=response.read().decode('utf-8'),
            data=None,
        )
        if json:
            res.data = json_loads(res.content)
        return res

    def get(self, url, query=None):
        return self.request('GET', url, query=query)

    def post(self, url, data=None, json=None):
        return self.request('POST', url, data=data, json=json)
