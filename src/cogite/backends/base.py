from typing import Iterable
from typing import Optional

from cogite import models


class BaseClient:
    def __init__(self, configuration, context):
        self.context = context
        self.configuration = configuration

    def create_pull_request(
        self,
        *,
        head: str,
        base: str,
        title: str,
        body: str,
        draft: bool = False,
    ) -> models.PullRequest:
        raise NotImplementedError()

    def get_pull_request(self, branch: Optional[str] = None) -> Optional[models.PullRequest]:
        raise NotImplementedError()

    def mark_pull_request_as_ready(self):
        raise NotImplementedError()

    def get_collaborators(self) -> Iterable[models.User]:
        raise NotImplementedError()

    def request_reviews(self, users: Iterable[models.User]):
        raise NotImplementedError()

    def get_pull_request_status(self) -> models.PullRequestStatus:
        raise NotImplementedError()
