import webbrowser

from cogite import errors
from cogite import spinner


def browse_pull_request(context, *, branch=None):
    client = context.client
    branch = branch or context.branch

    with spinner.get_for_git_host_call():
        pull_request = client.get_pull_request(branch)
    if not pull_request:
        raise errors.FatalError(
            f"There is no open pull request on the current branch {context.branch}"
        )

    webbrowser.open(pull_request.url)
