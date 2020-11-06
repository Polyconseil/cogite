import curses
import time

from cogite import errors
from cogite import git
from cogite import models
from cogite import spinner


def show_status(context, poll=False):
    client = context.client
    configuration = context.configuration

    with spinner.get_for_git_host_call():
        pull_request = client.get_pull_request()
    if not pull_request:
        raise errors.FatalError(
            f"There is no open pull request on the current branch {context.branch}"
        )

    if poll:
        try:
            screen = curses.initscr()
            curses.start_color()
            curses.use_default_colors()
            for i in range(0, curses.COLORS):
                curses.init_pair(i, i, -1)
            while True:
                status = client.get_pull_request_status()
                # addstr (for each build below) overwrites only the
                # start of the line. I tried to clean each line first
                # with setsyx and clrtoeol but the last character of
                # the last line remains.
                screen.erase()
                screen.addstr(0, 0, "Waiting for checks...")
                if not status.checks:
                    screen.addstr(2, 0, "No check yet.")
                for i, check in enumerate(status.checks):
                    line = '{} {} {}'.format(_marker(check.state, with_color=False), check.name, check.url)
                    screen.addstr(
                        2 + i, 0, line, curses.color_pair(_curses_color(check.state))
                    )
                screen.refresh()
                if status.checks and not any(
                    check.state == models.CommitState.PENDING
                    for check in status.checks):
                    break
                time.sleep(configuration.status_poll_frequency)
        except KeyboardInterrupt:
            pass
        finally:
            curses.endwin()
    else:
        with spinner.get_for_git_host_call():
            status = client.get_pull_request_status()

    _show_check_state(status)
    # Always print the statuses. When we poll and quit the loop
    # because the Jenkins job is complete, the (curses) screen is
    # reset so the information disappears.
    if status.reviews:
        print("Reviews:")
        for review in status.reviews:
            print(f"  {_marker(review.state)} {review.author_login}")
    else:
        print("\033[91m✖\033[0m Found no request for review.")
    if status.sha != git.get_current_sha():
        # FIXME: print in red
        print(
            "Warning: your branch is ahead of upstream. "
            "The status above does not correspond to your latest local commit."
        )


def _show_check_state(status):
    if status.checks:
        print("Checks:")
        for check in status.checks:
            print(f"  {_marker(check.state)} {check.name} ({check.url})")
    else:
        print("\033[91m✖\033[0m Found no check.")


# FIXME: we should have a more central way of associating states,
# characters ("✔", "✖", etc.), control characters for colors on the
# terminal and curses color. See `_curses_color()` below, too.
def _marker(state, with_color=True):
    if state in (
        models.CommitState.ERROR,
        models.CommitState.FAILURE,
        models.ReviewState.REJECTED,
    ):
        char = "✖"
        colorized = f"\033[91m{char}\033[0m"  # red
    elif state in (models.CommitState.SUCCESS, models.ReviewState.APPROVED):
        char = "✔"
        colorized = f"\033[92m{char}\033[0m"  # green
    elif state == models.ReviewState.COMMENTED:
        char = "?"
        colorized = f"\033[93m{char}\033[0m"  # yellow
    elif state in (models.CommitState.PENDING, models.ReviewState.PENDING):
        char = "…"
        colorized = f"\033[96m{char}\033[0m"  # cyan
    else:
        raise ValueError(f"Unexpected state: {state}")
    if not with_color:
        return char
    return colorized


# FIXME: see comment above about `_marker()`.
def _curses_color(state):
    if state == models.CommitState.SUCCESS:
        return curses.COLOR_GREEN
    if state == models.CommitState.PENDING:
        return curses.COLOR_CYAN
    if state in (models.CommitState.ERROR, models.CommitState.FAILURE):
        return curses.COLOR_RED
    raise ValueError(f"Unexpected state: {state}")
