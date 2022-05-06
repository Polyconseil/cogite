import curses
import time

from cogite import errors
from cogite import git
from cogite import interaction
from cogite import models
from cogite import spinner


def show_status(context, poll=False):
    client = context.client
    configuration = context.configuration

    with spinner.get_for_git_host_call():
        pull_request = client.pull_request
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
                    line = interaction.interpret_rich_text(
                        f"{_symbol_for_state(check.state)} {check.name} — {check.url}",
                        context=interaction.OutputContext.CURSES,
                    )
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

    # Always print the statuses. When we poll and quit the loop
    # because the CI job is complete, the (curses) screen is
    # reset so the information disappears.
    _show_check_state(status)
    if status.reviews:
        interaction.display("Reviews:")
        for review in status.reviews:
            interaction.display(
                f"  {_symbol_for_state(review.state)} {review.author_login}"
            )
    else:
        interaction.display("[[warning]] Found no request for review.")
    if status.sha != git.get_current_sha():
        interaction.display(
            "[[warning]] Your branch is ahead of upstream. "
            "[[caution]]The status above does not correspond to your latest local commit.[[/]]"
        )


def _show_check_state(status):
    if status.checks:
        interaction.display("Checks:")
        for check in status.checks:
            interaction.display(
                f"  {_symbol_for_state(check.state)} {check.name} — {check.url}"
            )
    else:
        interaction.display("[[error]] Found no check.")


def _symbol_for_state(state) -> str:
    if state in (
        models.CommitState.ERROR,
        models.CommitState.FAILURE,
        models.ReviewState.REJECTED,
    ):
        return interaction.StatusSymbol.ERROR.value
    if state in (models.CommitState.SUCCESS, models.ReviewState.APPROVED):
        return interaction.StatusSymbol.SUCCESS.value
    if state == models.ReviewState.COMMENTED:
        return interaction.StatusSymbol.QUESTION.value
    if state in (models.CommitState.PENDING, models.ReviewState.PENDING):
        return interaction.StatusSymbol.PENDING.value
    raise ValueError(f"Unexpected state: {state}")


def _curses_color(state):
    if state == models.CommitState.SUCCESS:
        return curses.COLOR_GREEN
    if state == models.CommitState.PENDING:
        return curses.COLOR_CYAN
    if state in (models.CommitState.ERROR, models.CommitState.FAILURE):
        return curses.COLOR_RED
    raise ValueError(f"Unexpected state: {state}")
