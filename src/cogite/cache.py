import json
import os
import pathlib


USER_CACHE_HOME = pathlib.Path(
    os.environ.get("XDG_CACHE_HOME", pathlib.Path.home() / ".cache")
)
COGITE_CACHE_DIR = USER_CACHE_HOME / "cogite"
COGITE_CACHE_FILE = COGITE_CACHE_DIR / "cache.json"


_encode = json.dumps
_decode = json.loads

NOT_SET = object()


def get(key):
    try:
        encoded = COGITE_CACHE_FILE.read_text()
    except FileNotFoundError:
        return NOT_SET
    return _decode(encoded).get(key, NOT_SET)


def set(key, value):  # pylint: disable=redefined-builtin
    try:
        current = json.loads(COGITE_CACHE_FILE.read_text())
    except FileNotFoundError:
        COGITE_CACHE_DIR.mkdir(0o700, parents=True)
        current = {}
    current[key] = value
    COGITE_CACHE_FILE.write_text(_encode(current))
