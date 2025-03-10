#
#   ipmi.py (C) 2025, Peter Sulyok
#   ipmiexp package: ModalWindow() class implementation.
#
from typing import Union, List
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Horizontal
from textual.widgets import Label, Button, RadioButton, RadioSet, Input
from ipmiexp import Ipmi, IpmiSensor, IpmiZone

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
        padding: 1;
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
                yield Button("Set", id="set", variant="success")
                yield Button("Cancel", id="cancel", variant="error")

    def on_button_pressed(self, event):
        result = -1
        if event.button.id == "set":
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

class SetLevelWindow(ModalScreen):
    """A modal pop-up window for setting new fan level."""

    DEFAULT_CSS = """
    SetLevelWindow {
        align: center middle;
    }

    SetLevelWindow > Container {
        width: auto;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1;
    }

    SetLevelWindow > Container > Label {
        width: 100%;
        content-align-horizontal: center;
        margin-top: 1;
    }

    SetLevelWindow > Container > Input {
        width: 100%;
        content-align-horizontal: center;
        margin-top: 1;
        margin-left: 3;
        margin-right: 3;  
    }

    SetLevelWindow > Container > Horizontal {
        width: auto;
        height: auto;
    }

    SetLevelWindow > Container > Horizontal > Button {
        margin: 1 4;
    }
    """
    zone: IpmiZone

    def __init__(self, zone: IpmiZone):
        self.zone = zone
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container():
            yield Label('Enter a new level for \'' + self.zone.name + '\':')
            yield Input(id="level_input", value=str(self.zone.level), type="integer")
            with Horizontal():
                yield Button("Set", id="set", variant="success")
                yield Button("Cancel", id="cancel", variant="error")

    def on_button_pressed(self, event):
        result = -1
        s = self.query_one(Input).value
        if event.button.id == "set" and s:
            result = int(s)
        self.dismiss(result)

    def on_mount(self) -> None:
        self.query_one('#level_input', Input).focus()

class SetThresholdWindow(ModalScreen):
    """A modal pop-up window for setting new sensor threshold."""

    DEFAULT_CSS = """
    SetThresholdWindow {
        align: center middle;
    }

    SetThresholdWindow > Container {
        width: auto;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }

    SetThresholdWindow > Container > Label {
        width: auto;
        content-align-horizontal: center;
        margin: 1;
        padding: 1;
    }

    SetThresholdWindow > Container > Horizontal {
        width: 100%;
        height: auto;
        align-horizontal: center;        
    }

    SetThresholdWindow > Container > Horizontal > Label {
        width: auto;
        align: left middle;
        padding: 1;
    }

    SetThresholdWindow > Container > Horizontal > Input {
        width: 60%;
        align: right middle;
    }

    #button_block {
        width: auto;
        height: auto;
    }

    #button_block Button {
        margin: 2 4;
    }
    """
    sensor: IpmiSensor

    def __init__(self, sensor:IpmiSensor):
        self.sensor = sensor
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(f'Enter new sensor thresholds for \'{self.sensor.name}\':')
            if self.sensor.has_lnr:
                with Horizontal():
                    yield Label('LNR')
                    yield Input(id="lnr_input",
                                type='number' if self.sensor.type_id == IpmiSensor.TYPE_VOLTAGE else 'integer',
                                value=str(self.sensor.lnr))
            if self.sensor.has_lcr:
                with Horizontal():
                    yield Label('LCR')
                    yield Input(id="lcr_input",
                                type='number' if self.sensor.type_id == IpmiSensor.TYPE_VOLTAGE else 'integer',
                                value=str(self.sensor.lcr))
            if self.sensor.has_lnc:
                with Horizontal():
                    yield Label('LNC')
                    yield Input(id="lnc_input",
                                type='number' if self.sensor.type_id == IpmiSensor.TYPE_VOLTAGE else 'integer',
                                value=str(self.sensor.lnc))
            if self.sensor.has_unc:
                with Horizontal():
                    yield Label('UNC')
                    yield Input(id="unc_input",
                                type='number' if self.sensor.type_id == IpmiSensor.TYPE_VOLTAGE else 'integer',
                                value=str(self.sensor.unc))
            if self.sensor.has_ucr:
                with Horizontal():
                    yield Label('UCR')
                    yield Input(id="ucr_input",
                                type='number' if self.sensor.type_id == IpmiSensor.TYPE_VOLTAGE else 'integer',
                                value=str(self.sensor.ucr))
            if self.sensor.has_unr:
                with Horizontal():
                    yield Label('UNR')
                    yield Input(id="unr_input",
                                type='number' if self.sensor.type_id == IpmiSensor.TYPE_VOLTAGE else 'integer',
                                value=str(self.sensor.unr))

            with Horizontal(id="button_block"):
                yield Button("Set", id="set", variant="success")
                yield Button("Cancel", id="cancel", variant="error")

    def on_button_pressed(self, event:Button.Pressed) -> None:
        result: List[Union[float, int]] = []
        value: Union[float, int]
        input_line: Input

        if event.button.id == "set":
            is_float = bool(self.sensor.type_id == IpmiSensor.TYPE_VOLTAGE)
            if self.sensor.has_lnr:
                input_line = self.query_one('#lnr_input', Input)
                value=float(input_line.value) if is_float else int(input_line.value)
                result.append(value)
            if self.sensor.has_lcr:
                input_line = self.query_one('#lcr_input', Input)
                value=float(input_line.value) if is_float else int(input_line.value)
                result.append(value)
            if self.sensor.has_lnc:
                input_line = self.query_one('#lnc_input', Input)
                value=float(input_line.value) if is_float else int(input_line.value)
                result.append(value)
            if self.sensor.has_unc:
                input_line = self.query_one('#unc_input', Input)
                value=float(input_line.value) if is_float else int(input_line.value)
                result.append(value)
            if self.sensor.has_ucr:
                input_line = self.query_one('#ucr_input', Input)
                value=float(input_line.value) if is_float else int(input_line.value)
                result.append(value)
            if self.sensor.has_unr:
                input_line = self.query_one('#unr_input', Input)
                value=float(input_line.value) if is_float else int(input_line.value)
                result.append(value)
        self.dismiss(result)

# End.
