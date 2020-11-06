import dataclasses
import enum
from typing import List


class CommitState(enum.Enum):
    ERROR = 'error'
    FAILURE = 'failure'
    PENDING = 'pending'
    SUCCESS = 'success'


class ReviewState(enum.Enum):
    APPROVED = 'approved'
    COMMENTED = 'commented'
    PENDING = 'pending'
    REJECTED = 'rejected'


@dataclasses.dataclass
class PullRequest:
    destination_branch: str
    host_autodeletes_branch_on_merge: bool
    id: str
    number: int
    url: str


@dataclasses.dataclass
class User:
    id: str
    login: str
    name: str


@dataclasses.dataclass
class PullRequestCheck:
    name: str
    state: CommitState
    url: str


@dataclasses.dataclass
class PullRequestReview:
    state: ReviewState
    author_login: str


@dataclasses.dataclass
class PullRequestStatus:
    sha: str
    checks: List[PullRequestCheck] = dataclasses.field(default_factory=list)
    reviews: List[PullRequestReview] = dataclasses.field(default_factory=list)
