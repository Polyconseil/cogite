import itertools
import os
import typing

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
    configuration = context.configuration
    base_branch = base_branch or configuration.master_branch

    helpers.assert_current_branch_is_feature_branch(context.branch, configuration.master_branch)

    _git_push_to_origin(context.branch)

    commits_text = os.linesep.join(
        itertools.chain.from_iterable(
            (commit, '', '')
            for commit in git.get_commits_logs(base_branch, context.branch)
        )
    )

    pull_request_template = _get_pull_request_template()
    content = os.linesep.join(
        filter(None, [commits_text, pull_request_template])
    ).strip()

    if pull_request_template:
        # If there is a template, the user certainly wants to edit it.
        confirmed = interaction.EDIT
    else:
        interaction.display('Confirm title and body:')
        # Do not use `interaction.display()` below: `content` should
        # be displayed as is.
        print(interaction.quote(content))
        confirmed = interaction.confirm(defaults_to_yes=True, with_edit_choice=True)
        if not confirmed:
            return
    if confirmed is interaction.EDIT:
        content = interaction.input_from_file(starting_text=content) or content

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

    interaction.display(f"[[success]] Created #{pr.number} at {pr.url}")


def _get_pull_request_template() -> typing.Optional[str]:
    """Return the contents of the pull request template, or None if there
    is no template.
    """
    template_file_paths = [
        os.sep.join(path_parts).lstrip(os.path.sep)
        for path_parts in itertools.product(
            ['', '.github'],
            ['PULL_REQUEST_TEMPLATE.md', 'pull_request_template.md'],
        )
    ]

    git_root = git.get_git_root()
    for file_path in template_file_paths:
        path = git_root / file_path
        if path.exists():
            return path.read_text()

    return None


def _git_push_to_origin(current_branch_name):
    result = shell.run(
        'git rev-parse --abbrev-ref --symbolic-full-name @{u}',
        expected_returncodes=(0, 128),
    )
    if result.returncode == 128:  # upstream branch is not configured
        command = f'git push --set-upstream origin {current_branch_name}'
    else:  # result.returncode == 0:  # upstream branch is already configured
        command = 'git push'

    shell.run(
        command,
        progress='Pushing local branch to upstream...',
        on_success='Pushed local branch to upstream.',
        on_failure='Could not push local branch to upstream.',
    )
