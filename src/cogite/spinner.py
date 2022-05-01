import yaspin

from cogite import interaction


class Spinner:
    def __init__(self, progress, on_success, on_failure):
        self.progress = progress
        self.on_success = on_success
        self.on_failure = on_failure

    def success(self):
        self._spinner.text = self.on_success
        self._spinner.ok(interaction.interpret_rich_text('[[success]]'))

    def failure(self):
        self._spinner.text = self.on_failure
        self._spinner.fail(interaction.interpret_rich_text('[[error]]'))

    def __enter__(self):
        self._spinner = yaspin.yaspin(text=self.progress).__enter__()
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        if exc:
            self.failure()
        return self._spinner.__exit__(exc_type, exc, exc_tb)


def get_for_git_host_call():
    return Spinner(
        progress='Requesting Git host API...',
        on_success='Got response from Git host API',
        on_failure='Got error from Git host API',
    )
