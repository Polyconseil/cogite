import itertools
import os
import pathlib

from cogite import completion
from cogite import errors
from cogite import git
from cogite import interaction
from cogite import shell
from cogite import spinner

from . import helpers


def add_draft_pull_request(context, **kwargs):
    return add_pull_request(context, draft=True, **kwargs)


def add_pull_request(context, *, base_branch, draft=False):
    client = context.client

    helpers.assert_current_branch_is_not_master(context.branch)

    _git_push_to_origin(context.branch)

    commits_text = os.linesep.join(
        itertools.chain.from_iterable(
            (commit, '', '')
            for commit in git.get_commits_logs(base_branch, context.branch)
        )
    )

    content = os.linesep.join(
        filter(None, [commits_text, _get_pull_request_template()])
    ).strip()

    print(f'Confirm title and body:\n--- 8-> ---\n{content}\n--- 8-> ---')
    confirmed = interaction.confirm(defaults_to_yes=True, with_edit_choice=True)
    if not confirmed:
        return
    if confirmed is interaction.EDIT:
        content = (
            interaction.input_from_file(starting_text=f'{content}\n')
            or content
        )

    iterator = iter(content.splitlines(keepends=True))
    # title is the first line of the file
    title = next(iterator)
    # discard all empty lines between the title and the body then recreate the body
    body = "".join(itertools.dropwhile(lambda line: line.strip() == '', iterator))

    with spinner.Spinner(
        progress='Creating pull request on Git host...',
        on_success='Created pull request on Git host',
        on_failure='Failed to create pull request on Git host',
    ) as sp:
        try:
            pr = client.create_pull_request(
                head=context.branch,
                base=base_branch,
                title=title.strip(),
                body=body.strip(),
                draft=draft,
            )
        except errors.GitHostError as exc:
            raise errors.FatalError(str(exc)) from exc
        sp.success()

    with spinner.get_for_git_host_call():
        try:
            collaborators = client.get_collaborators()
        except errors.GitHostError as exc:
            raise errors.FatalError(str(exc)) from exc
    reviewers = completion.prompt_for_users(collaborators)
    if reviewers:
        with spinner.get_for_git_host_call():
            try:
                client.request_reviews(reviewers)
            except errors.GitHostError as exc:
                raise errors.FatalError(str(exc)) from exc

    print(f"Created #{pr.number} at {pr.url}")


def _get_pull_request_template():
    template_file_paths = [
        os.sep.join(path_parts).lstrip(os.path.sep)
        for path_parts in itertools.product(
            ['', '.github'], ['PULL_REQUEST_TEMPLATE.md']
        )
    ]

    git_root = pathlib.Path(git.get_git_root())
    for file_path in template_file_paths:
        path = git_root / file_path
        if path.exists():
            return path.read_text()

    return None


def _git_push_to_origin(current_branch_name):
    result = shell.run(
        'git rev-parse --abbrev-ref --symbolic-full-name @{u}', check_ok=False
    )
    if result.returncode == 128:  # upstream branch is not configured
        command = f'git push --set-upstream origin {current_branch_name}'
    elif result.returncode == 0:  # upstream branch is already configured
        command = 'git push'
    else:
        error = '\n'.join(result.stderr)
        raise errors.FatalError(
            f"Got the following error when pushing upstream:\n{error}"
        )

    shell.run(
        command,
        progress='Pushing local branch to upstream...',
        on_success='Pushed local branch to upstream.',
        on_failure='Could not push local branch to upstream.',
    )
