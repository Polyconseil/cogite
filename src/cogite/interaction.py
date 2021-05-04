import os
import pathlib
import subprocess
import tempfile


EDIT = object()

CONFIRM_YES_CHOICES = {'y', 'ye', 'yes'}
CONFIRM_NO_CHOICES = {'n', 'no'}
CONFIRM_EDIT_CHOICES = {'e', 'ed', 'edi', 'edit'}


def input_from_file(starting_text=''):
    """Ask user for input by opening a file in their preferred editor.

    The file is filled with ``starting_text``. If the user quits the
    editor without saving (or if an error occurrs), ``None`` is
    returned.
    """
    with tempfile.NamedTemporaryFile('w+') as tmp:
        path = pathlib.Path(tmp.name)
        path.write_text(starting_text)

        with subprocess.Popen(f"$EDITOR {path}", shell=True) as process:
            process.wait()

            if process.returncode != os.EX_OK:
                return None

        return path.read_text()


def confirm(defaults_to_yes, with_edit_choice=False):
    if with_edit_choice:
        choices = ['y', 'e', 'n']
    else:
        choices = ['y', 'n']

    yes_values = CONFIRM_YES_CHOICES.copy()
    no_values = CONFIRM_NO_CHOICES.copy()
    if defaults_to_yes:
        yes_values |= {''}
        choices[0] = choices[0].upper()
    else:
        no_values |= {''}
        choices[-1] = choices[-1].upper()
    choices = '/'.join(choices)

    while True:
        confirmation = input(f"Continue [{choices}]? ").lower()
        if confirmation in no_values:
            return False
        if confirmation in yes_values:
            return True
        if with_edit_choice and confirmation in CONFIRM_EDIT_CHOICES:
            return EDIT
