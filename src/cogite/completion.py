import re
from typing import List

import prompt_toolkit
import prompt_toolkit.completion

from cogite import models


USER_FORMATTER = "{login} ({name})"
USER_REGEXP = re.compile(r" *(?P<login>[^\(]+?) \([^\)]*?\)")


class UserCompleter(prompt_toolkit.completion.Completer):
    def __init__(self, users: List[models.User]):
        self.users = users

    def get_completions(self, document, complete_event):
        # Based on prompt_toolkit's WordCompleter
        word = document.get_word_before_cursor().lower()
        for user in self.users:
            if word in user.login.lower() or word in user.name.lower():
                display = USER_FORMATTER.format(login=user.login, name=user.name or 'unnamed')
                yield prompt_toolkit.completion.Completion(
                    text=display,
                    start_position=-len(word),
                )


def prompt_for_users(users: List[models.User]):
    while True:
        completer = UserCompleter(users)
        response = prompt_toolkit.prompt(
            "Reviewers (leave blank if none, tab to complete, space to select, enter to validate): ",
            completer=completer,
        )
        by_login = {
            user.login: user
            for user in users
        }
        try:
            return [by_login[login] for login in USER_REGEXP.findall(response)]
        except KeyError as exc:
            login = exc.args[0]
            print(
                f"Could not find user '{login}'. "
                f"Make you sure that you use a space to separate reviewers."
            )
