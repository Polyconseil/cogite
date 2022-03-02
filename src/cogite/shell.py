import dataclasses
import os
import re
import subprocess
from typing import Iterable

from . import errors
from . import spinner


@dataclasses.dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def get_lines(bytestring):
    """Decode bytestring and turn into a (possibly empty) list of lines."""
    lines = bytestring.strip().decode('utf-8').split(os.linesep)
    # Remove text if it's followed by "\r". `git rebase` does that to
    # show work in progress, which we are not interested to see.
    lines = [re.sub(r".*\r", "", line) for line in lines]
    return [l for l in lines if l]


def _run(command: str):
    result = subprocess.run(
        command.split(' '),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return CommandResult(
        returncode=result.returncode,
        stdout=get_lines(result.stdout),
        stderr=get_lines(result.stderr),
    )


def run(
    command: str,
    check_ok: bool = True,
    expected_returncodes: Iterable[int] = (0,),
    progress: str = None,
    on_success: str = None,
    on_failure: str = None,
) -> CommandResult:
    """Run a command, possibly showing a spinner."""
    if not progress:
        result = _run(command)
    else:
        on_success = on_success or progress
        on_failure = on_failure or progress
        with spinner.Spinner(progress, on_success, on_failure) as sp:
            result = _run(command)
            if result.returncode in expected_returncodes:
                sp.success()
            else:
                sp.failure()

    if check_ok and result.returncode not in expected_returncodes:
        if result.stderr:
            # XXX: Printing stdout and *then* stderr may not
            # correspond to the order in which the output would have
            # appeared if we had not captured it.
            err = f"[[error]] Got the following output when running `{command}`:{os.linesep}"
            err += os.linesep.join(result.stdout + result.stderr)
        else:
            err = f"[[error]] Got an empty error when running `{command}`."
        raise errors.FatalError(err)

    return result
