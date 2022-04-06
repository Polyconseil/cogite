import dataclasses
import re
import urllib.parse

from cogite import backends
from cogite import config
from cogite import errors
from cogite import git


SSH_GIT_URL = re.compile('(?P<user>.+)@(?P<host>.+):(?P<path>.+)')


@dataclasses.dataclass
class Context:
    remote_url: str
    host_domain: str
    owner: str
    repository: str
    branch: str

    # Injected from `cli._main()`
    client: backends.BaseClient
    configuration: config.Configuration

    def as_dict(self):
        return dict(self.__dict__)  # copy, except for `client` and `configuration`


def _extract_domain_and_path(remote_url: str):
    parsed = urllib.parse.urlparse(remote_url)
    if parsed.scheme in ('http', 'https'):
        return parsed.netloc, parsed.path.lstrip('/')
    ssh_match = SSH_GIT_URL.match(remote_url)
    if ssh_match:
        return ssh_match.group('host'), ssh_match.group('path')
    raise errors.ContextError(
        f"Could not parse remote origin and determine the Git host: '{remote_url}'"
    )


def get_context() -> Context:
    """Return a set of basic information that nearly all commands need.

    This is easier than passing each of them around, and avoid calling
    them more than once.
    """
    remote_url = git.get_remote_origin_url()
    domain, path = _extract_domain_and_path(remote_url)
    if path.endswith('.git'):
        path = path[:-4]
    owner, repository = path.split('/')
    return Context(
        remote_url=remote_url,
        host_domain=domain,
        owner=owner,
        repository=repository,
        branch=git.get_current_branch(),
        # `client` and `configuration` will be overriden with proper
        # values in `cli._main()`. We provide dummy values to avoid
        # having to set `Context.client` and `Context.configuration`
        # as Optional, because they are not.
        client="dummy",  # type: ignore[arg-type]
        configuration="dummy",  # type: ignore[arg-type]
    )
