#
#   ipmi.py (C) 2025, Peter Sulyok
#   ipmiexp package: ModalWindow() class implementation.
#
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Horizontal
from textual.widgets import Label, Button, RadioButton, RadioSet
from ipmiexp import Ipmi

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


class SetFanModeWindow(ModalScreen):
    """A modal pop-up window for setting new fan mode."""

    DEFAULT_CSS = """
    SetFanModeWindow {
        align: center middle;
    }

    SetFanModeWindow > Container {
        width: auto;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }

    SetFanModeWindow > Container > Label {
        width: 100%;
        content-align-horizontal: center;
        margin-top: 1;
    }

    SetFanModeWindow > Container > RadioSet {
        width: 100%;
        content-align-horizontal: center;
        margin-top: 1;
    }

    SetFanModeWindow > Container > Horizontal {
        width: auto;
        height: auto;
    }

    SetFanModeWindow > Container > Horizontal > Button {
        margin: 2 4;
    }
    """
    mode: int

    def __init__(self, mode: int):
        self.mode = mode
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Select new fan mode:")
            with RadioSet(id="fan_modes", ):
                yield RadioButton("Standard mode", value=bool(self.mode == Ipmi.STANDARD_MODE))
                yield RadioButton("Full mode", value=bool(self.mode == Ipmi.FULL_MODE))
                yield RadioButton("Optimal mode", value=bool(self.mode == Ipmi.OPTIMAL_MODE))
                yield RadioButton("PUE mode", value=bool(self.mode == Ipmi.PUE_MODE))
                yield RadioButton("Heavy IO mode", value=bool(self.mode == Ipmi.HEAVY_IO_MODE))
            with Horizontal():
                yield Button("Set mode", id="set_mode", variant="success")
                yield Button("Cancel", id="_cancel", variant="error")

    def on_button_pressed(self, event):
        result = -1
        if event.button.id == "set_mode":
            buttons = list(self.query(RadioButton))
            result = 0
            for b in buttons:
                if b.value:
                    break
                result += 1
        self.dismiss(result)

    def on_mount(self) -> None:
        rs = self.query_one(RadioSet)
        rs._selected = self.mode
        rs.focus()

# End.
