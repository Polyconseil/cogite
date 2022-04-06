import contextlib
import json
import re

from cogite import config
from cogite import context
from cogite import models
from cogite.backends import github

from . import base
from . import requests_mocker


GRAPHQL_RESPONSES_DIR = base.TEST_DATA_PATH / "graphql_responses" / "github"
GRAPHQL_RESPONSE_MAPPING = {
    "query pullRequest": "query_pull_request.json",
    "query pullRequestStatus": "query_pull_request_status.json",
    "query repository": "query_repository.json",
    "query repositoryContributors": "query_repository_contributors.json",
    "mutation createPullRequest": "mutation_create_pull_request.json",
    "mutation markAsReady": "mutation_mark_as_ready.json",
    "mutation requestReviews": "mutation_request_reviews.json",
}

def _make_client():
    configuration = config.Configuration(host_api_url="https://api.example.com")
    ctx = context.Context(
        remote_url="dummy",
        host_domain="dummy",
        owner="dummy_owner",
        repository="dummy_repository",
        branch="dummy_branch",
        client="dummy",
        configuration="dummy",
    )
    return github.GitHubApiClient(configuration, ctx)


@contextlib.contextmanager
def install_github_api_mock():
    with requests_mocker.get_mock() as mock:
        mock.register_callback(get_mock_response)
        yield mock


def get_mock_response(request):
    assert request.method == "POST"
    assert request.full_url == "https://api.example.com/graphql"
    content = json.loads(request.data)["query"]
    type_and_name = re.match("(query|mutation) [^ ]+", content).group(0)
    # The following will raise a KeyError, which will help in case one
    # forgets to list a mock response in `GRAPHQL_RESPONSE_MAPPING`
    # above.
    filename = GRAPHQL_RESPONSE_MAPPING[type_and_name]
    content = (GRAPHQL_RESPONSES_DIR / filename).read_bytes()
    return requests_mocker.Response(content=content, status=200)


@base.disable_disk_cache
@base.mock_authentication
def test_repository():
    client = _make_client()
    expected = {
        "id": "MDEwOlJlcG9zaXRvcnkzMTM0MzAwMDg=",
        "host_autodeletes_branch_on_merge": False,
    }
    with install_github_api_mock():
        assert client.repository == expected
    # Get it again, this time from the object (memory) cache.
    assert client.repository == expected


@base.mock_authentication
def test_get_pull_request():
    client = _make_client()
    expected = models.PullRequest(
        destination_branch="master",
        host_autodeletes_branch_on_merge=False,
        id="PR_kwDOEq6P-M4vaHRu",
        number=30,
        url="https://github.com/dbaty/sandbox/pull/30",
    )
    with install_github_api_mock():
        assert client.pull_request == expected
    # Get it again, this time from the object (memory) cache.
    assert client.pull_request == expected


@base.mock_authentication
def test_create_pull_request():
    client = _make_client()
    expected = models.PullRequest(
        destination_branch="master",
        host_autodeletes_branch_on_merge=False,
        id="PR_kwDOEq6P-M4vaHRu",
        number=30,
        url="https://github.com/dbaty/sandbox/pull/30",
    )
    with install_github_api_mock():
        pull_request = client.create_pull_request(
            head="dbaty/eternal-branch-for-cogite-development",
            base="master",
            title="Update README",
            body="",
            draft=False,
        )
        assert pull_request == expected


@base.mock_authentication
def test_request_reviews():
    client = _make_client()
    with install_github_api_mock():
        client.request_reviews([models.User(id="1", login="jdoe", name="Jane Doe")])


@base.mock_authentication
def test_get_collaborators():
    client = _make_client()
    expected = [
        models.User(id='MDQ6VXNlcjQ3MTMyMQ==', login='dbaty', name='Damien Baty'),
    ]
    with install_github_api_mock():
        assert client.get_collaborators() == expected


@base.mock_authentication
def test_mark_pull_request_as_ready():
    client = _make_client()
    with install_github_api_mock():
        client.mark_pull_request_as_ready()


@base.mock_authentication
def test_get_pull_request_status():
    client = _make_client()
    expected = models.PullRequestStatus(
        sha='b04e404e1715fe9ac60bd53643264df3f0dfcb67',
        checks=[
            models.PullRequestCheck(
                name='test',
                state=models.CommitState.SUCCESS,
                url='https://github.com/dbaty/sandbox/runs/4424135611?check_suite_focus=true',
            ),
        ],
        reviews=[],
    )
    with install_github_api_mock():
        assert client.get_pull_request_status() == expected


class TestGetPullRequestStatus:
    def test_status_with_checks(self):
        response = base.get_json_test_data('github', 'pull_request_status_checks.json')
        status = github._get_pull_request_status(response)
        assert status.sha == '7c38f8108e9aee12470d4874c0cf2b14b92db33e'
        assert len(status.checks) == 5
        assert status.checks[0].name == 'quality'
        assert status.checks[0].state == models.CommitState.SUCCESS
        assert status.checks[0].url == 'https://github.com/Polyconseil/cogite/runs/1906337703'

    def test_status_with_commit_status(self):
        response = base.get_json_test_data('github', 'pull_request_status_commit_states.json')
        status = github._get_pull_request_status(response)
        assert status.sha == 'sha-sha-sha'
        assert len(status.checks) == 2
        assert status.checks[0].name == 'ci/circleci: Run quality checks after commit'
        assert status.checks[0].state == models.CommitState.PENDING
        assert status.checks[0].url == 'https://example.com/ci/1234'

    def test_reviews(self):
        response = base.get_json_test_data('github', 'pull_request_status_commit_states.json')
        status = github._get_pull_request_status(response)
        assert len(status.reviews) == 3
        assert status.reviews[0].state == models.ReviewState.PENDING
        assert status.reviews[0].author_login == 'reviewer1'
        assert status.reviews[1].state == models.ReviewState.APPROVED
        assert status.reviews[1].author_login == 'reviewer2'
        assert status.reviews[2].state == models.ReviewState.APPROVED
        assert status.reviews[2].author_login == 'reviewer3'
