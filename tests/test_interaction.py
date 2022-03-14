from cogite import interaction

from . import base


def test_rich_text_multiple_substitutions():
    text = "[[success]] It worked [[caution]]in red[[/]]."
    with base.fake_tty():
        out = interaction.interpret_rich_text(text)
    expected = "\033[92m✔\033[0m It worked \033[91min red\033[0m."
    assert out == expected


def test_rich_text_multiple_substitutions_no_color():
    text = "[[success]] It worked, [[caution]]no formatting here[[/]]."
    out = interaction.interpret_rich_text(text, interaction.OutputContext.NO_COLOR)
    expected = "✔ It worked, no formatting here."
    assert out == expected


def test_quote():
    text = "\n".join((
        "I am the first line",
        "",
        "And here is a long explanation",
        "on multiple lines",
        "with [[red]]markup[[/]] that should not be interpreted."
    ))
    with base.fake_tty():
        quoted = interaction.quote(text)
    assert quoted.split("\n") == [
        "\033[90m|\033[0m I am the first line",
        "\033[90m|\033[0m ",
        "\033[90m|\033[0m And here is a long explanation",
        "\033[90m|\033[0m on multiple lines",
        "\033[90m|\033[0m with [[red]]markup[[/]] that should not be interpreted."
    ]
