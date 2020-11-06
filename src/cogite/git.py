import os
import re

from . import errors
from . import shell


def get_git_root():
    return shell.run("git rev-parse --show-toplevel").stdout[0]


def get_current_branch():
    return shell.run("git rev-parse --abbrev-ref HEAD").stdout[0]


def get_remote_branch():
    return shell.run("git rev-parse --abbrev-ref --symbolic-full-name @{u}").stdout[0]


def get_current_sha():
    return shell.run("git rev-parse HEAD").stdout[0]


def get_remote_sha():
    # Warning: this supposes that the local branch is up-to-date.
    return shell.run("git rev-parse @{u}").stdout[0]


def get_n_commits_ahead_of_remote():
    # Warning: this supposes that the local branch is up-to-date.
    remote = get_remote_branch()
    current = get_current_branch()
    output = shell.run(f"git rev-list {remote}..{current} --count").stdout[0]
    return int(output)


def get_remote_origin_url():
    # The following command expands insteadOf customizations, if any.
    try:
        return shell.run("git ls-remote --get-url").stdout[0]
    except errors.FatalError as exc:
        raise errors.FatalError(f"{str(exc)}\ncogite must be run from a Git checkout.") from exc


def get_commits_logs(base_branch, branch):
    # FIXME: docstring (+ rename function?)
    log_lines = shell.run(f"git log {base_branch}..{branch} --reverse").stdout

    for commit_block in re.split(r"^commit [\da-f]{20,}", os.linesep.join(log_lines), flags=re.MULTILINE):
        # `git log` indents the commit message with 4 spaces
        current_commit_text = re.findall(r"^    (.*)$", commit_block, re.MULTILINE)

        if current_commit_text:
            yield os.linesep.join(current_commit_text)
