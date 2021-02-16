from cogite import models
from cogite.backends import github

from . import base


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
