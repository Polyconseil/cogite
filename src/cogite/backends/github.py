import collections
import dataclasses
import json
import time
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
import urllib.error
import urllib.parse
import webbrowser

from cogite import auth
from cogite import cache
from cogite import errors
from cogite import models
from cogite import requests
from cogite import spinner

from . import base


QUERY_GET_REPOSITORY = """\
query ($owner: String!, $repositoryName: String!) {
  repository(owner: $owner, name: $repositoryName) {
    deleteBranchOnMerge,
    id,
  }
}
"""

QUERY_GET_REPOSITORY_CONTRIBUTORS = """\
query getRepositoryId(
  $owner: String!, $repositoryName: String!, $paginationCursor: String
) {
  repository(owner: $owner, name: $repositoryName) {
    collaborators(first: 100, after: $paginationCursor) {
      nodes {
        id,
        login,
        name,
      }
      pageInfo {
        hasNextPage,
        endCursor,
      }
      totalCount,
    }
  }
}
"""

QUERY_GET_PULL_REQUEST = """\
query getPullRequest(
  $owner: String!, $repositoryName: String!, $headRefName: String!
) {
  repository(owner: $owner, name: $repositoryName) {
    pullRequests(headRefName: $headRefName, states: OPEN, first: 1) {
      nodes {
        baseRefName,
        id,
        number,
        permalink,
      }
      pageInfo {
        hasNextPage,
        endCursor,
      }
      totalCount,
    }
  }
}
"""

QUERY_GET_PULL_REQUEST_STATUS = """\
query getPullRequestStatus(
   $pullRequestId: ID!,
) {
  node(id: $pullRequestId ) {
    ... on PullRequest {
      commits(last: 1) {
        nodes {
          commit {
            oid,
            checkSuites(last: 1) {
              nodes {
                checkRuns(last: 50) {
                  nodes {
                    conclusion,
                    name,
                    permalink,
                    status,
                  }
                }
              }
            },
            status {
              state
              contexts {
                context,
                state,
                targetUrl,
              }
            },
          }
        }
      },
      reviewRequests(first: 20) {
        nodes {
          requestedReviewer {
            ... on User {
              login,
            }
          }
        }
      },
      reviews(first: 20) {
        nodes {
          author {
            login,
          },
          state,
        }
      }
    }
  }
}
"""

MUTATION_CREATE_PULL_REQUEST = """\
mutation (
  $repositoryId: ID!,
  $headRefName: String!,
  $baseRefName: String!,
  $title: String!,
  $body: String!,
  $draft: Boolean!,
) {
  createPullRequest(input: {
    repositoryId: $repositoryId,
    headRefName: $headRefName,
    baseRefName: $baseRefName,
    title: $title,
    body: $body,
    draft: $draft,
  }) {
    pullRequest {
      id,
      number,
      permalink,
    }
  }
}
"""

MUTATION_MARK_PULL_REQUEST_AS_READY = """\
mutation ($pullRequestId: ID!) {
  markPullRequestReadyForReview(input: {pullRequestId: $pullRequestId})
  {
    clientMutationId,
  }
}
"""

MUTATION_REQUEST_REVIEWS = """\
mutation (
  $pullRequestId: String!,
  $userIds: [ID!],
) {
  requestReviews(input: {
    pullRequestId: $pullRequestId,
    union: true,
    userIds: $userIds,
  })
  {
    clientMutationId,
  }
}
"""


def _get_pull_request_status(response: dict) -> models.PullRequestStatus:
    pr_info = response['data']['node']
    commit_info = pr_info['commits']['nodes'][0]['commit']
    status = models.PullRequestStatus(sha=commit_info['oid'])

    # Depending on the CI configuration, we end up with either commit
    # statuses or checks. Look at both.
    if commit_info['status']:
        status.checks = [
            models.PullRequestCheck(
                name=context['context'],
                state=_gh_commit_status_to_cogite_commit_state(context['state']),
                url=context['targetUrl'],
            )
            for context in commit_info['status']['contexts']
        ]
    elif commit_info['checkSuites']:
        status.checks = [
            models.PullRequestCheck(
                name=run['name'],
                state=_gh_check_run_status_to_cogite_commit_state(
                    run['status'], run['conclusion']
                ),
                url=run['permalink'],
            )
            for run in commit_info['checkSuites']['nodes'][0]['checkRuns']['nodes']
        ]

    # The 'reviews' nodes in the response only contain reviews
    # that have been performed. Pending reviews are only available
    # through the 'reviewRequests' nodes.
    reviews: Dict[str, List[models.ReviewState]] = collections.defaultdict(list)
    # GitHub returns a full User object in 'reviewRequests', but
    # an Author object (with only the login) in 'reviews'. We'll
    # use the lowest common denominator, i.e. login only.
    for request in pr_info['reviewRequests']['nodes']:
        user_reviews = reviews[request['requestedReviewer']['login']]
        user_reviews.append(models.ReviewState.PENDING)
    for review in pr_info['reviews']['nodes']:
        user_reviews = reviews[review['author']['login']]
        user_reviews.append(_gh_review_state_to_cogite_review_state(review['state']))
    # If a user commented on the pull request and then approved
    # it, we'll have two reviews. Merge them by keeping the most
    # relevant state.
    for login, review_states in reviews.items():
        if models.ReviewState.REJECTED in review_states:
            state = models.ReviewState.REJECTED
        elif models.ReviewState.APPROVED in review_states:
            state = models.ReviewState.APPROVED
        else:
            state = models.ReviewState.PENDING
        status.reviews.append(
            models.PullRequestReview(author_login=login, state=state)
        )
    status.reviews.sort(key=lambda review: review.author_login)
    # FIXME: we could remove the author's review (which will appear
    # if the author commented on their own pull request).
    return status


def _gh_commit_status_to_cogite_commit_state(github_state):
    # https://docs.github.com/en/graphql/reference/enums#statusstate
    return {
        'ERROR': models.CommitState.ERROR,
        'EXPECTED': models.CommitState.UNKNOWN,
        'FAILURE': models.CommitState.FAILURE,
        'PENDING': models.CommitState.PENDING,
        'SUCCESS': models.CommitState.SUCCESS,
    }.get(github_state, models.CommitState.UNKNOWN)


def _gh_check_run_status_to_cogite_commit_state(status, conclusion):
    # https://docs.github.com/en/graphql/reference/enums#checkstatusstate
    if status != 'COMPLETED':
        return models.CommitState.PENDING
    # https://docs.github.com/en/graphql/reference/enums#checkconclusionstate
    return {
        'ACTION_REQUIRED': models.CommitState.UNKNOWN,
        'CANCELLED': models.CommitState.FAILURE,
        'FAILURE': models.CommitState.FAILURE,
        'NEUTRAL': models.CommitState.UNKNOWN,
        'SKIPPED': models.CommitState.SUCCESS,
        'STALE': models.CommitState.UNKNOWN,
        'STARTUP_FAILURE': models.CommitState.FAILURE,
        'SUCCESS': models.CommitState.SUCCESS,
        'TIMED_OUT': models.CommitState.FAILURE,
    }.get(conclusion, models.CommitState.UNKNOWN)


def _gh_review_state_to_cogite_review_state(github_state):
    # https://docs.github.com/en/graphql/reference/enums#pullrequestreviewstate
    return {
        'APPROVED': models.ReviewState.APPROVED,
        'CHANGES_REQUESTED': models.ReviewState.REJECTED,
        'COMMENTED': models.ReviewState.COMMENTED,
        # I have never used the "dismiss" feature, I don't know what
        # we should do with this state.
        'DISMISSED': models.ReviewState.UNKNOWN,
        'PENDING': models.ReviewState.PENDING,
    }.get(github_state, models.ReviewState.UNKNOWN)


class GitHubApiClient(base.BaseClient):
    """A client for GitHub API v4 (GraphQL)."""

    def __init__(self, configuration, context):
        super().__init__(configuration, context)
        self.url = f'{configuration.host_api_url}/graphql'
        self.repository_name = context.repository
        self.owner = context.owner
        self.branch = context.branch

    @property
    def session(self):
        if hasattr(self, '_session'):
            return self._session  # pylint: disable=access-member-before-definition
        auth_token = auth.get_token(self.context.host_domain)
        if not auth_token:
            raise errors.FatalError(
                f"No authentication token for {self.context.host_domain}. You must "
                f"first configure one with `cogite auth add`."
            )
        self._session = requests.Session(auth_token=auth_token)
        return self._session

    def _post(self, query, variables=None):
        # FIXME: handle errors. At least auth errors.
        data = {'query': query, 'variables': variables or {}}
        try:
            response = self.session.post(self.url, json=data)
        except urllib.error.HTTPError as exc:
            if exc.code == 422:
                # FIXME: not all 422 responses have an 'errors'
                # key. For example, requesting a review of a pull
                # request by its author yields a 422 with the following response:
                # {"message": "Review cannot be requested from pull request author.", ...
                response  = json.loads(exc.fp.read().decode('utf-8'))
                details = response['errors'][0]['message']
                err = f'Got HTTP error code {exc.code}: {exc.reason}. Details: {details}'
                raise errors.FatalError(err) from exc
            raise
        return response

    @property
    def repository(self):
        if hasattr(self, '_repository'):
            return self._repository  # pylint: disable=access-member-before-definition
        cache_key = self.context.remote_url
        cached = cache.get(cache_key)
        if cached is not cache.NOT_SET:
            self._repository = cached
            return self._repository
        repository = self._get_repository_from_host()
        cache.set(cache_key, repository)
        self._repository = repository
        return repository

    def _get_repository_from_host(self):
        query = QUERY_GET_REPOSITORY
        variables = {
            'owner': self.owner,
            'repositoryName': self.repository_name,
        }
        response = self._post(query, variables)
        repo_info = response['data']['repository']
        return {
            'id': repo_info['id'],
            'host_autodeletes_branch_on_merge': repo_info['deleteBranchOnMerge']
        }

    @property
    def pull_request(self):
        if not hasattr(self, '_pull_request'):
            self._pull_request = self.get_pull_request()
        return self._pull_request

    def get_pull_request(self, branch=None) -> Optional[models.PullRequest]:
        branch = branch or self.context.branch
        query = QUERY_GET_PULL_REQUEST
        variables = {
            'owner': self.owner,
            'repositoryName': self.repository_name,
            'headRefName': branch,
        }
        response = self._post(query, variables)
        data = response['data']['repository']['pullRequests']
        if data['totalCount'] == 0:
            return None
        if data['totalCount'] >= 2:
            raise errors.GitHostError(
                f"Unexpected number of open pull requests "
                f"for branch '{branch}': {data['totalCount']}"
            )
        pr_info = data['nodes'][0]
        return models.PullRequest(
            destination_branch=pr_info['baseRefName'],
            host_autodeletes_branch_on_merge=self.repository['host_autodeletes_branch_on_merge'],
            id=pr_info['id'],
            number=pr_info['number'],
            url=pr_info['permalink'],
        )

    def create_pull_request(
        self,
        *,
        head: str,
        base: str,  # pylint: disable=redefined-outer-name
        title: str,
        body: str,
        draft=False,
    ) -> models.PullRequest:
        mutation = MUTATION_CREATE_PULL_REQUEST
        variables = {
            'repositoryId': self.repository['id'],
            'headRefName': head,
            'baseRefName': base,
            'body': body,
            'title': title,
            'draft': draft,
        }
        response = self._post(mutation, variables)
        if 'errors' in response:
            raise errors.GitHostError(response['errors'][0]['message'])
        pr_info = response['data']['createPullRequest']['pullRequest']
        return models.PullRequest(
            destination_branch=base,
            host_autodeletes_branch_on_merge=self.repository['host_autodeletes_branch_on_merge'],
            id=pr_info['id'],
            number=pr_info['number'],
            url=pr_info['permalink'],
        )

    def request_reviews(self, users: Iterable[models.User]):
        mutation = MUTATION_REQUEST_REVIEWS
        variables = {
            'pullRequestId': self.pull_request.id,
            'userIds': [user.id for user in users],
        }
        self._post(mutation, variables)
        # FIXME: check response

    def get_collaborators(self) -> Iterable[models.User]:
        query = QUERY_GET_REPOSITORY_CONTRIBUTORS
        variables = {
            'owner': self.owner,
            'repositoryName': self.repository_name,
            'paginationCursor': None,
        }
        collaborators = []
        # FIXME: handle errors
        while 1:
            response = self._post(query, variables)
            data = response['data']['repository']['collaborators']
            collaborators.extend([
                models.User(
                    id=user_info['id'],
                    login=user_info['login'],
                    name=user_info['name'] or '',
                )
                for user_info in data['nodes']
            ])
            if not data['pageInfo']['hasNextPage']:
                break
            variables['paginationCursor'] = data['pageInfo']['endCursor']
        return collaborators

    def mark_pull_request_as_ready(self):
        mutation = MUTATION_MARK_PULL_REQUEST_AS_READY
        variables = {
            'pullRequestId': self.pull_request.id,
        }
        self._post(mutation, variables)

    def get_pull_request_status(self) -> models.PullRequestStatus:
        query = QUERY_GET_PULL_REQUEST_STATUS
        variables = {
            'pullRequestId': self.pull_request.id,
        }
        response = self._post(query, variables)
        return _get_pull_request_status(response)


class GitHubOAuthDeviceFlowTokenGetter:
    """A class to create a new personal access token, using the device
    flow with the registered "cogite" OAuth app on GitHub.

    https://docs.github.com/en/free-pro-team@latest/developers/apps/authorizing-oauth-apps#device-flow
    """

    # This is the client_id that has been granted by GitHub when the
    # "cogite" OAuth app has been registered.
    CLIENT_ID = '2b46ebae56793d920b69'
    GRANT_TYPE = 'urn:ietf:params:oauth:grant-type:device_code'
    SCOPE = 'repo'

    @dataclasses.dataclass
    class VerificationInfo:
        device_code: str
        user_code: str
        interval: int
        verification_uri: str
        expires_in: int

    def get_token(self):
        verification_info = self._get_verification_info()
        self.interval = verification_info.interval

        print(f"1. Copy your one-time verification code: {verification_info.user_code}")
        input(
            "2. Then press Enter to open github.com in your browser "
            "and fill the form with this code..."
        )
        webbrowser.open(verification_info.verification_uri)

        # Poll GitHub until the code is confirmed and GitHub returns
        # the personal access token.
        expires_at = time.time() + verification_info.expires_in
        while True:
            with spinner.Spinner(
                progress='Waiting for your verification code to be confirmed...',
                on_success='Your verification code has been confirmed by GitHub.',
                on_failure='Your verification code could not be confirmed',
            ) as sp:
                time.sleep(self.interval + 0.5)
                try:
                    access_token = self._get_access_token(verification_info.device_code)
                except Exception:
                    sp.failure()
                    raise
                if access_token:
                    sp.success()
                    return access_token
                if time.time() > expires_at:
                    sp.fail()
                    raise errors.FatalError(
                        "The verification code has expired. Did you enter the code "
                        "on GitHub? Please try again."
                    )

    def _get_verification_info(self):
        """Request a verification code from GitHub."""
        # Get verification code from GitHub.
        response = requests.send(
            'POST',
            'https://github.com/login/device/code',
            data={
                'client_id': self.CLIENT_ID,
                'scope': self.SCOPE,
            }
        )
        if response.status != 200:
            body = response.read().decode('utf-8')
            raise errors.FatalError(f"HTTP error {response.status}: {body}")

        data = urllib.parse.parse_qs(response.read().decode('utf-8'))
        return self.VerificationInfo(
            device_code=data['device_code'][0],
            user_code=data['user_code'][0],
            interval=int(data['interval'][0]),
            verification_uri=data['verification_uri'][0],
            expires_in=int(data['expires_in'][0]),
        )

    def _get_access_token(self, device_code):
        """Poll GitHub and see if the verification code has been entered by the user."""
        response = requests.send(
            'POST',
            'https://github.com/login/oauth/access_token',
            json={
                'client_id': self.CLIENT_ID,
                'device_code': device_code,
                'grant_type': self.GRANT_TYPE,
            }
        )
        if response.status != 200:
            body = response.read().decode('utf-8')
            raise errors.FatalError(f"HTTP error {response.status}: {body}")

        data = urllib.parse.parse_qs(response.read().decode('utf-8'))
        if 'access_token' in data:
            return data['access_token'][0]

        if 'error' not in data:
            raise errors.FatalError(f"Unexpected error response without error code: {data}")

        error_code = data['error'][0]

        if error_code == 'authorization_pending':
            return None

        if error_code == 'slow_down':
            self.interval += 5
            return None

        if error_code == 'expired_token':
            # expiring token is detected in the caller
            return None

        if error_code == 'access_denied':
            raise errors.FatalError(
                "You cancelled the verification of the code. Please try again."
            )

        raise errors.FatalError(
            f"Unexpected error: {error_code}. If you can reproduce this error, please "
            f"report if to the maintainers with the following info: {data}"
        )
