from functools import lru_cache
from typing import Any

import questionary
from prompt_toolkit import HTML, print_formatted_text
from prompt_toolkit.formatted_text import to_formatted_text
from prompt_toolkit.styles import BaseStyle, Style
from yaspin import Spinner as YaspinSpinner
from yaspin.core import Yaspin

BOLD = "\033[1m"

# Styles for texts
STYLE = questionary.Style(
    [
        ("qmark", "fg:#5f819d"),
        ("work", "fg:#5f819d"),
        ("failure", "fg:#ff726f"),
        ("success", "fg:#4BCA81"),
        ("question", "bold"),
        ("answer", "fg:#FF9D00 bold"),
        ("pointer", ""),
        ("selected", ""),
        ("separator", ""),
        ("instruction", ""),
        ("text", ""),
        ("instruction", ""),
    ]
)
questionary.constants.DEFAULT_STYLE = STYLE

# Styles for HTML
GREEN = Style.from_dict({"msg": "#4caf50 bold", "sub-msg": "#616161"})
RED = Style.from_dict({"msg": "#f44336 bold", "sub-msg": "#616161"})
BLUE = Style.from_dict({"msg": "#2196f3 bold", "sub-msg": "#616161"})
ORANGE = Style.from_dict({"msg": "#ff9800 bold", "sub-msg": "#616161"})


def fprint(msg: Any, sub_msg: str | None = None, style: BaseStyle = STYLE, **kwargs):
    if sub_msg:
        msg = HTML(
            "<b>></b> <msg>{msg}</msg> <sub-msg>{sub_msg}</sub-msg>".format(
                msg=msg, sub_msg=sub_msg
            )
        )
    elif isinstance(msg, str):
        msg = [("class:text", msg)]
    print_formatted_text(to_formatted_text(msg), style=style, **kwargs)


def print_work(text: str):
    fprint([("class:work", "*"), ("class:question", " " + text)])


def print_failure(text: str):
    fprint([("class:failure", "✘ "), ("class:question", text)])


def print_success(text: str):
    fprint([("class:success", "✔ "), ("class:question", text)])


@lru_cache(None)
def text_spinner(text: str = "CRYPTO MINER", left: str = "[", right: str = "]", interval: int = 80):
    fullstr = text + " " * (len(text) // 2) + text[:-1]
    win_size = len(text)
    return YaspinSpinner(
        [left + fullstr[i : i + win_size] + right for i in range(len(fullstr) - win_size, 0, -1)],
        interval,
    )


def show_spinner(text: str):
    return Spinner(text_spinner(), text=BOLD + text)


class Spinner(Yaspin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcome = None
        self.outcome_text = ""

    def fail(self, text: str):
        self.outcome = False
        self.outcome_text = text

    def ok(self, text: str):
        self.outcome = True
        self.outcome_text = text

    def stop(self):
        super().stop()
        if self.outcome is None:
            return
        if self.outcome:
            print_success(self.outcome_text)
        else:
            print_failure(self.outcome_text)
