#!/usr/bin/env python
"""Check that the commits that the user is about to push, do not look
like the user has forgotten to squash work-in-progress commits.
"""

import os
import subprocess
import sys

from cogite import interaction


# If the user pushes MAX_COMMITS or more, ask for confirmation.
MAX_COMMITS = 2
DISPLAY_N_COMMITS = 5  # Don't display too much commits (when merging from/into prod).


def run_command(command):
    with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE) as process:
        process.wait()
        return b"".join(process.stdout.readlines()).decode(sys.stdout.encoding)


def check_commits(
    local_sha,
    remote_ref,
    remote_sha,
    max_commits=MAX_COMMITS,
    display_n_commits=DISPLAY_N_COMMITS,
):
    # `remote_ref` looks like 'refs/heads/<branch_name>'
    branch = remote_ref.split("/", 2)[-1]

    commit_range = f"{remote_sha}..{local_sha}"
    n_commits = int(run_command(f"git rev-list {commit_range} | wc -l"))
    if n_commits >= MAX_COMMITS:
        if n_commits > display_n_commits:
            msg = (
                f"[[warning]] You are about to push {n_commits} commits to {branch} "
                f"(only {display_n_commits} are displayed below):"
            )
        else:
            msg = f"[[warning]] You are about to push these {n_commits} commits to {branch}:"
        interaction.display(f"{os.linesep}{msg}")

        n_to_display = min(n_commits, display_n_commits)
        interaction.display(run_command(f'git log --pretty="%h %s" -n {n_to_display} {commit_range}'))
        interaction.display("Perhaps you have forgotten to squash them.")
        if not interaction.confirm(defaults_to_yes=False):
            return False

    # FIXME: make these keywords configurable
    keywords = ["wip", "-w-", "_w_", "fixup", "squash", "review", "revue"]
    command = f"git log --color --pretty=medium --regexp-ignore-case {commit_range}"
    for keyword in keywords:
        command += f" --grep {keyword}"
    squashable_commits = run_command(command)
    if squashable_commits:
        interaction.display(
            f"[[warning]] You are about to push commits to {branch} that look like "
            "squashable or work-in-progress commits:"
        )
        interaction.display(squashable_commits)
        interaction.display(f"{os.linesep}Perhaps you have forgotten to squash them.")
        if not interaction.confirm(defaults_to_yes=False):
            return False

    return True


def main():
    git_args = sys.argv[1:]
    if not git_args:
        # Nothing to push.
        sys.exit(os.ex_OK)

    # Do not remove the `*_`. It would work (because we do receive 4
    # arguments) but pylint reports an `unbalanced-tuple-unpacking`
    # warning. If we disable this message, pylint reports a
    # `useless-suppression` warning. I also tried `= git_args[:4]` to
    # give pylint a clue, but we still get a warning.
    _local_ref, local_sha, remote_ref, remote_sha, *_ = git_args
    if not check_commits(local_sha, remote_ref, remote_sha):
        sys.exit(1)


if __name__ == "__main__":
    main()
