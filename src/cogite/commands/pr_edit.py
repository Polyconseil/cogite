from cogite import errors
from cogite import spinner


def mark_pull_request_as_ready(context):
    client = context.client

    with spinner.get_for_git_host_call():
        pull_request = client.get_pull_request()
    if not pull_request:
        raise errors.FatalError(
            f"There is no open pull request on the current branch {context.branch}"
        )

    client = context.client
    success_message = f"The pull request is now ready for review at {pull_request.url}."
    with spinner.Spinner(
        progress="Marking pull request as ready for review...",
        on_success=success_message,
        on_failure="Could not mark the pull request as ready for review.",
    ) as sp:
        client.mark_pull_request_as_ready()
        sp.success()
