import collections
import contextlib
import dataclasses
import typing
import unittest.mock
import urllib.request


@contextlib.contextmanager
def get_mock():
    """Return an instance of ``Mock`` to be used as a context manager.

    Example::

        with get_mock() as mock:
            mock.register("GET", "https://example.com", content="OK")
            # call code that would make an HTTP request
    """
    m = Mock()
    with unittest.mock.patch("urllib.request.urlopen", m.urlopen):
        yield m

@dataclasses.dataclass
class Request:
    url: str
    data: bytes
    headers: typing.Dict[str, str]


@dataclasses.dataclass
class Response:
    content: bytes
    status: int

    def read(self):
        return self.content


@dataclasses.dataclass
class Call:
    request: Request
    response: Response


class Mock():
    """Intercept HTTP requests and mock their responses.

    An instance of ``Mock`` can be configured via its two methods:

    - ``register(method, url, content, status=200)`` allows you to
       mock a particular request (i.e. an URL and a method, such as
       "GET" or "POST") and provide a specific response content and
       status.

    - ``register_callback(callback)`` lets you register a function to
      be called when a request is intercepted. This function may
      return a ``Response`` object, or ``None`` if it does not know
      what to do with the request. For an example, see
      ``get_mock_response()`` in ``test_github.py``.
    """
    def __init__(self):
        self.callbacks = []
        self.mocks = collections.defaultdict(dict)
        self.calls = []

    def register(self, method, url, content, status=200):
        method = method.lower()
        self.mocks[url][method] = Response(content=content, status=status)

    def register_callback(self, callback: typing.Callable[[urllib.request.Request], Response]):
        self.callbacks.append(callback)

    def urlopen(self, request: urllib.request.Request, **kwargs):
        url = request.full_url
        method = (request.method or "get").lower()
        response = self.mocks.get(url, {}).get(method)
        if not response:
            for callback in self.callbacks:
                response = callback(request)
                if response:
                    break
        if not response:
            raise ValueError(f"No mock for method={method} and url={url}")
        call = Call(
            request=Request(
                url=url,
                data=request.data or b'',
                headers=request.headers,
            ),
            response=response,
        )
        self.calls.append(call)
        return response
