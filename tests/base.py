import contextlib
import json
import os
import pathlib
import sys
from unittest import mock

import cogite.cache


TEST_DATA_PATH = pathlib.Path(os.path.dirname(__file__)) / 'data'


def get_json_test_data(*stems):
    path = TEST_DATA_PATH
    for stem in stems:
        path /= stem
    with path.open(encoding='utf-8') as fp:
        return json.load(fp)


def mock_authentication(test_function):
    def wrapper(*args, **kwargs):
        with mock.patch("cogite.auth.get_token", lambda host_domain: "token"):
            test_function(*args, **kwargs)
    return wrapper


def disable_disk_cache(test_function):
    def wrapper(*args, **kwargs):
        with mock.patch.multiple(
                "cogite.cache",
                get=lambda key: cogite.cache.NOT_SET,
                set=lambda key, value: value,
        ):
            test_function(*args, **kwargs)
    return wrapper


@contextlib.contextmanager
def fake_tty():
    # Temporarily monkey patches stdout to make it look like a tty.
    # This is necessary when running tests under GitHub Actions, where
    # stdout is not a tty (https://github.com/actions/runner/issues/241).
    orig_isatty = sys.stdout.isatty
    sys.stdout.isatty = lambda: True
    try:
        yield
    finally:
        sys.stdout.isatty = orig_isatty
