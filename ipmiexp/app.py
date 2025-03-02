#
#   app.py (C) 2025, Peter Sulyok
#   ipmiexp package: IpmiExpApp() class implementation.
#
from typing import List
from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.containers import HorizontalGroup, Vertical, VerticalScroll
from textual.widgets import Button, ContentSwitcher, DataTable, Label

from ipmiexp.config import Config
from ipmiexp.ipmi import Ipmi, IpmiSensor, IpmiZone
from ipmiexp.modal import ModalWindow

class IpmiExpApp(App):

    config: Config              # Configuration class.
    ipmi: Ipmi                  # Ipmi class.
    sensors: List[IpmiSensor]   # IPMI sensors.
    zones: List[IpmiZone]       # Ipmi zones.

    CSS = """
    Screen {
        align: center middle;
        padding: 1;
    }
    ContentSwitcher {
        border: round $primary;
        height: 1fr;
    }
    
    #fans_table {
        border: round $primary;
    }
    #zones_table {
        border: round $primary;
    }
    """

    def __init__(self, config_file: str) -> None:
        """"""
        # Load configuration.
        self.config = Config(config_file)
        self.ipmi = Ipmi(self.config.ipmi_command, self.config.ipmi_fan_mode_delay, self.config.ipmi_fan_level_delay)
        self.sensors = self.ipmi.read_sensors()
        self.zones = self.ipmi.read_zones()
        super().__init__()

    def compose(self) -> ComposeResult:
        self.title="IPMI Explorer"
        yield Header(show_clock=False)
        yield Footer()
        with HorizontalGroup():
            yield Button("Sensors", id="sensors_page", variant="primary")
            yield Button("Fans", id="fans_page", variant="default")
            yield Button("Event", id="events_page", variant="default")
            yield Button("BMC", id="bmc_page", variant="default")
            yield Button("Settings", id="settings_page", variant="default")
        with ContentSwitcher(initial="sensors_page"):
            yield DataTable(id="sensors_page", cursor_type='row', zebra_stripes=True)
            with VerticalScroll(id="fans_page"):
                yield Label("Fan mode: ")
                with HorizontalGroup():
                    yield Button("Set mode", id="set_mode")
                    yield Button("Set level", id="set_level")
                    yield Button("Find zones", id="find_zones")
                with HorizontalGroup():
                    yield DataTable(id="fans_table", cursor_type='row', zebra_stripes=True)
                    yield DataTable(id="zones_table", cursor_type='row', zebra_stripes=True)
            with VerticalScroll(id="events_page"):
                yield Label("Events")
            with VerticalScroll(id="bmc_page"):
                yield Label("BMC")
            with VerticalScroll(id="settings_page"):
                yield Label("Settings")

    def on_button_pressed(self, event: Button.Pressed) -> None:

        if event.button.id in {"sensors_page", "fans_page", "events_page", "bmc_page", "settings_page"}:
            self.query_one('#'+self.query_one(ContentSwitcher).current, Button).variant = "default"
            self.query_one(ContentSwitcher).current = event.button.id
            self.query_one('#'+event.button.id, Button).variant = 'primary'
        if event.button.id == "set_level":
            m = ModalWindow("Hello", "Yes", "No")
            self.push_screen(m)


    def on_mount(self) -> None:

        # "Sensors" content.
        table = self.query_one("#sensors_page", DataTable)
        table.add_columns("ID", "Name", "Location", "Reading", "Unit", "LNR", "LCR", "LNC", "UNC", "UCR", "UNR")
        for r in self.sensors:
            if r.has_reading:
                if r.has_unit:
                    unit = r.unit
                    if r.type_id == IpmiSensor.TYPE_VOLTAGE:
                        value = f'{r.reading:.3f}'
                    else:
                        value = f'{r.reading}'
                else:
                    value = f'0x{r.reading:02x}'
                    unit = ''
            else:
                value = "-"
                unit = ''
            if r.has_reading and r.has_threshold:
                unr = f'{r.unr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.unr}'
                ucr = f'{r.ucr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.ucr}'
                unc = f'{r.unc:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.unc}'
                lnr = f'{r.lnr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lnr}'
                lcr = f'{r.lcr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lcr}'
                lnc = f'{r.lnc:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lnc}'
            else:
                unr = ucr = unc = lnr = lcr = lnc = '-'
            table.add_rows([(f'0x{r.id:x}', r.name, r.location, value, unit, lnr, lcr, lnc, unc, ucr, unr)])

        # "Fans" page.
        table = self.query_one("#fans_table", DataTable)
        table.border_title = "Fans"
        table.add_columns("ID", "Name", "RPM", "Level")
        for r in self.sensors:
            if r.type_id == IpmiSensor.TYPE_FAN:
                table.add_rows([(f"0x{r.id:02x}", r.name, r.reading if r.has_reading else "-", "-")])
        table = self.query_one("#zones_table", DataTable)
        table.border_title = "Zones"
        table.add_columns("Number", "Name", "Level", "Fans")
        for z in self.zones:
            table.add_rows([(f"{z.id}", z.name, z.level, "-")])


# End.
