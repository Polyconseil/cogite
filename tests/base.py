import json
import os
import pathlib


TEST_DATA_PATH = pathlib.Path(os.path.dirname(__file__)) / 'data'


def get_json_test_data(*stems):
    path = TEST_DATA_PATH
    for stem in stems:
        path /= stem
    with path.open(encoding='utf-8') as fp:
        return json.load(fp)
