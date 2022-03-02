from cogite import interaction
from cogite import shell

from . import helpers


MASTER_BRANCH = object()


def rebase_branch(context, *, print_success=True, rebase_from=MASTER_BRANCH):
    """Rebase a branch off of upstream master (or any other branch).

    This changes the local current and master branch (not upstream).
    """
    configuration = context.configuration
    branch = context.branch
    if rebase_from is MASTER_BRANCH:
        rebase_from = configuration.master_branch
    helpers.assert_current_branch_is_feature_branch(branch, configuration.master_branch)

    for command in (
        f'git checkout {rebase_from}',
        'git pull --rebase',
        f'git checkout {branch}',
        f'git rebase {rebase_from}',  # may fail if there are conflicts
    ):
        shell.run(command=command, progress=command)

    if print_success:
        interaction.display(
            f"[[success]] Your branch has been rebased wrt upstream {rebase_from}."
        )
