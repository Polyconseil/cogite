"""Call a GraphQL API and store responses.

These responses can then be used in tests to mock calls to the API.

First you need to create an input file: "recorders.toml". For each
GraphQL request, it may define variables that are sent in the
request. It may also define what is extracted from the response and
stored to be used as variables in other requests. For example::

    ["github/query_repository"]
    variables = { owner = "dbaty", repositoryName = "sandbox" }
    extract = { repositoryId = "data.repository.id" }

Here we extract `data["repository"]["id"]` from the response and store
it as `repositoryId`. We can then use it in a further request:

    ["github/mutation_create_pull_request"]
    variables =  { repositoryId = "$repositoryId" }
"""

import json
import os
import pathlib
import string

import toml

from cogite import auth
from cogite import requests


_THIS_DIR = pathlib.Path(__file__).parent
RECORDERS_FILE = _THIS_DIR / "recorders.toml"
OUTPUT_BASE_DIRECTORY = _THIS_DIR
BASE_GRAPHQL_DIRECTORY = _THIS_DIR.parent.parent.parent / "src" / "cogite" / "backends" / "graphql"

PLATFORM_URLS = {
    "github": {"api_url": "https://api.github.com/graphql", "auth_domain": "github.com"},
    "gitlab": {"api_url": "https://gitlab.com/api/v4/projects", "auth_domain": "gitlab.com"},
}


def main():
    recorders = toml.loads(RECORDERS_FILE.read_text())
    extracted = {}
    for name, config in recorders.items():
        generate_response(name, config, extracted)


def generate_response(name: str, config: dict, extracted: dict):
    platform = name.split("/")[0]
    url, session = _get_url_and_session(platform)
    query = (BASE_GRAPHQL_DIRECTORY / (name.replace("/", os.path.sep) + ".graphql")).read_text()
    variables = config.get("variables", {})
    _interpolate(variables, extracted)
    response = session.post(url, json={"query": query, "variables": variables})
    extracted.update(_extract(response.content, config.get("extract", {})))
    output_path = OUTPUT_BASE_DIRECTORY / platform / (name.split("/")[1] + ".json")
    output_path.write_text(response.content)
    cwd = os.getcwd()
    print(f"Wrote response in {output_path.relative_to(cwd)}")


def _get_url_and_session(platform: str):
    platform_info = PLATFORM_URLS[platform]
    url = platform_info["api_url"]
    auth_token = auth.get_token(platform_info["auth_domain"])
    session = requests.Session(auth_token=auth_token)
    return url, session


def _interpolate(variables: dict, extracted: dict):
    """Interpolate `variables` with data extracted from previous responses."""
    for name, variable in variables.items():
        if not isinstance(variable, str):
            continue
        variables[name] = string.Template(variable).substitute(extracted)


def _extract(response: str, to_extract: dict):
    json_response = json.loads(response)
    extracted = {}
    for var_name, path in to_extract.items():
        pointer = json_response
        for part in path.split("."):
            pointer = pointer[part]
        extracted[var_name] = pointer
    return extracted



if __name__ == '__main__':
    main()
