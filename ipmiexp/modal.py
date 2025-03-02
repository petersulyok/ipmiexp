#
#   ipmi.py (C) 2025, Peter Sulyok
#   ipmiexp package: Ipmi() class implementation.
#
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Horizontal
from textual.widgets import Label, Button

class ModalWindow(ModalScreen):
    """A generic modal screen class."""

    DEFAULT_CSS = """
    ModalWindow {
        align: center middle;
    }

    ModalWindow > Container {
        width: auto;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }

    ModalWindow > Container > Label {
        width: 100%;
        content-align-horizontal: center;
        margin-top: 1;
    }

    ModalWindow > Container > Horizontal {
        width: auto;
        height: auto;
    }

    ModalWindow > Container > Horizontal > Button {
        margin: 2 4;
    }
    """

    window_title: str
    button1_label: str
    button2_label: str
    selected: str

    def __init__(self, title: str, b1_label: str, b2_label: str):
        self.window_title = title
        self.b1_label = b1_label
        self.b2_label = b2_label
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(self.window_title)
            with Horizontal():
                yield Button(self.b1_label, id="b1", variant="success")
                yield Button(self.b2_label, id="b2", variant="error")

    def on_button_pressed(self, event):
        self.selected = event.button.id
        self.app.pop_screen()
