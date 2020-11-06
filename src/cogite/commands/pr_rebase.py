from cogite import shell

from . import helpers


def rebase_branch(context, *, print_success=True, rebase_from='master'):
    """Rebase a branch off of upstream master (or any other branch).

    This changes the local current and master branch (not upstream).
    """
    branch = context.branch
    helpers.assert_current_branch_is_not_master(branch)

    for command in (
        f'git checkout {rebase_from}',
        'git pull --rebase',
        f'git checkout {branch}',
        f'git rebase {rebase_from}',  # may fail if there are conflicts
    ):
        shell.run(command=command, progress=command)

    if print_success:
        print(
            f"\033[92m✔\033[0m Your branch has been rebased wrt upstream {rebase_from}."
        )
