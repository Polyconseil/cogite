import enum
import os
import pathlib
import re
import subprocess
import sys
import tempfile


NO_COLOR = "NO_COLOR" in os.environ  # see https://no-color.org/

EDIT = object()
CONFIRM_YES_CHOICES = {'y', 'ye', 'yes'}
CONFIRM_NO_CHOICES = {'n', 'no'}
CONFIRM_EDIT_CHOICES = {'e', 'ed', 'edi', 'edit'}


class OutputContext(enum.Enum):
    STANDARD = "standard"
    CURSES = "curses"
    NO_COLOR = "no color"


class StatusSymbol(enum.Enum):
    SUCCESS = "[[green]]✔[[/]]"
    SKIPPED = "[[grey]]✔[[/]]"
    WARNING = "[[red]]⚠[[/]]"
    ERROR = "[[red]]✖[[/]]"
    PENDING = "[[cyan]]…[[/]]"
    QUESTION = "[[yellow]]?[[/]]"
    QUOTATION = "[[grey]]|[[/]]"


class Style(enum.Enum):
    RESET = ""

    CAUTION = "caution"

    CYAN = "cyan"
    GREEN = "green"
    GREY = "grey"
    RED = "red"
    YELLOW = "yellow"


ANSI_ESCAPE_CODES = {
    Style.RESET: "\033[0m",

    Style.CAUTION: "\033[91m",  # red

    Style.CYAN: "\033[96m",
    Style.GREEN: "\033[92m",
    Style.GREY: "\033[90m",
    Style.RED: "\033[91m",
    Style.YELLOW: "\033[93m",
}


def input_from_file(starting_text=''):
    """Ask user for input by opening a file in their preferred editor.

    The file is filled with ``starting_text``. If the user quits the
    editor without saving (or if an error occurrs), ``None`` is
    returned.
    """
    with tempfile.NamedTemporaryFile('w+') as tmp:
        path = pathlib.Path(tmp.name)
        path.write_text(starting_text, encoding="utf-8")

        with subprocess.Popen(f"$EDITOR {path}", shell=True) as process:
            process.wait()

            if process.returncode != os.EX_OK:
                return None

        return path.read_text(encoding="utf-8")


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


RE_STATUS_SYMBOL_FINDER = re.compile(
    r"\[\[({})\]\]".format("|".join(_symbol.name.lower() for _symbol in StatusSymbol))
)
RE_STYLE_FINDER = re.compile(
    r"(\[\[({})\]\](.*?)\[\[/\]\])".format(
        "|".join(_style.name.lower() for _style in Style if _style != Style.RESET)
    )
)


def _status_symbol_replacer(match: re.Match):
    return getattr(StatusSymbol, match.group(1).upper()).value


def _substitute_status_symbol(text: str):
    return RE_STATUS_SYMBOL_FINDER.sub(_status_symbol_replacer, text)


def _standard_style_replacer(match: re.Match):
    tag = match.group(2)
    text = match.group(3)
    style_start = ANSI_ESCAPE_CODES[getattr(Style, tag.upper())]
    style_reset = ANSI_ESCAPE_CODES[Style.RESET]
    return f"{style_start}{text}{style_reset}"


def _substitute_style(text: str, context: OutputContext):
    if context == context.STANDARD:
        replacer = _standard_style_replacer
    elif context in (context.CURSES, context.NO_COLOR):
        replacer = lambda match: match.group(3)
    else:
        raise ValueError(f"Unknown output context: {context}")
    return RE_STYLE_FINDER.sub(replacer, text)


def interpret_rich_text(text: str, context: OutputContext = OutputContext.STANDARD) -> str:
    """Transform text with custom markup into printable characters.

    Markup includes status symbols, such as::

        [[success]] It worked

    ... and style information, such as::

        A [[green]]positive[[/]] outcome, [[caution]]with a warning[[/]].
    """
    if NO_COLOR or not sys.stdout.isatty():
        context = OutputContext.NO_COLOR
    text = _substitute_status_symbol(text)
    text = _substitute_style(text, context)
    return text


def display(rich_text: str):
    """Interpret rich text and print it."""
    print(interpret_rich_text(rich_text))


def quote(content: str, context: OutputContext = OutputContext.STANDARD) -> str:
    """Return **already-interpreted** text that has each line of
    ``content`` quoted.

    The result should be used directly with `print()` (and not
    ``interaction.display()``if you do not wish to interpret what's in
    ``content``.
    """
    return "\n".join(
        interpret_rich_text("[[quotation]] ", context) + line
        for line in content.split("\n")
    )
