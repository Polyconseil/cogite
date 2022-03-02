from cogite import errors
from cogite import git
from cogite import interaction
from cogite import shell
from cogite import spinner
import cogite.checks.pre_merge

from . import pr_rebase


def merge_pull_request(context):
    """Rebase a pull request, push to upstream and clean.

    More precisely, it:

    - rebases the commits of the current branch wrt an up-to-date upstream;
    - push to upstream;
    - remove the local branch;
    - remove the upstream branch (if necessary).

    If any action fails, we stop right away and the user can fix
    things (usually by fixing merge conflicts) and try again.
    """
    client = context.client
    configuration = context.configuration

    with spinner.get_for_git_host_call():
        pull_request = client.get_pull_request()
    if not pull_request:
        raise errors.FatalError(
            f"There is no open pull request on the current branch {context.branch}"
        )

    branch = context.branch
    destination_branch = pull_request.destination_branch

    interaction.display(
        f"You are about to rebase {branch} on {destination_branch} and "
        f"[[caution]]push {destination_branch} upstream[[/]]"
    )
    if not interaction.confirm(defaults_to_yes=False):
        return

    if configuration.merge_auto_rebase != 'always':
        with spinner.Spinner(
            "Checking whether the local branch is up-to-date with respect "
            "to the remote destination branch...",
            on_success="",
            on_failure="",
        ):
            upstream_head = git.get_upstream_remote_sha(pull_request.destination_branch)
        if not git.current_branch_has_commit(upstream_head):
            if configuration.merge_auto_rebase == 'never':
                interaction.display(
                    f"[[error]] Latest commit upstream is {upstream_head}, "
                    f"which you do not have locally. Merge has been cancelled. "
                    f"You may rebase manually with `cogite pr rebase`."
                )
                return
            interaction.display(
                f"[[warning]] Latest commit upstream is {upstream_head}, which you "
                f"do not have locally. Do you want to automatically rebase and merge?"
            )
            if not interaction.confirm(defaults_to_yes=False):
                interaction.display(
                    "[[error]] Merge has been cancelled. "
                    "You may rebase manually with `cogite pr rebase`"
                )
                return

    # We'll stop at the first command that fails.
    pr_rebase.rebase_branch(
        context,
        print_success=False,
        rebase_from=destination_branch,
    )
    run_with_progress = lambda command: shell.run(command, progress=command)
    # Pushing again to the branch lets GitHub automatically mark the
    # PR as merged when we push to the master afterwards. (And GitHub
    # will display a link to the PR on the commit(s).)
    run_with_progress('git push --force-with-lease')
    run_with_progress(f'git checkout {destination_branch}')
    run_with_progress(f'git rebase {branch}')  # this rebase should not fail

    if configuration.merge_enable_pre_checks and not cogite.checks.pre_merge.check_commits(
        git.get_current_sha(), git.get_remote_branch(), git.get_remote_sha()
    ):
        current_branch = git.get_current_branch()  # get it again (safety belt)
        if current_branch != destination_branch:
            raise RuntimeError(
                f"We are in {current_branch} but should be in {destination_branch}"
            )
        interaction.display("[[error]] You cancelled the push.")
        n_ahead = git.get_n_commits_ahead_of_remote()
        if not n_ahead:
            # I don't think this should happen: we added commits from
            # the feature branch, so the destination branch should be
            # ahead of its remote.
            raise errors.FatalError(
                f"[[error]] Cogite could not determine the status of the "
                f"local {destination_branch}, which is where you now are. "
                f"[[caution]]You are NOT on your feature branch. Caution![[/]]"
            )
        shell.run(f"git reset --hard @~{n_ahead}")
        shell.run(f"git checkout {branch}")
        interaction.display(
            f"Destination branch ({destination_branch}) has been rollbacked, "
            f"you are back in {branch}"
        )
        return

    run_with_progress('git push')  # may fail if someone pushed since our last pull.
    run_with_progress(f'git branch --delete {branch}')

    if not pull_request.host_autodeletes_branch_on_merge:
        run_with_progress(f'git push --delete origin {branch}')

    interaction.display(
        f"[[success]] Your pull request has been merged to {destination_branch} "
        f"and the corresponding branches (local and upstream) have been deleted."
    )
