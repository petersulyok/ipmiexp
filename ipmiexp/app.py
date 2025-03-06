#
#   app.py (C) 2025, Peter Sulyok
#   ipmiexp package: IpmiExpApp() class implementation.
#
from typing import List
from textual.app import App, ComposeResult
from textual.coordinate import Coordinate
from textual.widgets import Header, Footer
from textual.containers import HorizontalGroup, VerticalScroll, ScrollableContainer
from textual.widgets import Button, ContentSwitcher, DataTable, Label

from ipmiexp.config import Config
from ipmiexp.ipmi import Ipmi, IpmiSensor, IpmiZone
from ipmiexp.modal import SetFanModeWindow, SetLevelWindow

class IpmiExpApp(App):

    config: Config              # Configuration class.
    ipmi: Ipmi                  # Ipmi class.
    sensors: List[IpmiSensor]   # IPMI sensors.
    zones: List[IpmiZone]       # Ipmi zones.
    fan_mode: int               # Current IPMI fan mode.
    events: str                 # IPMI events.

    BINDINGS = [
        ("t", "set_threshold", "Set threshold"),
        ("l", "set_zone_level", "Set zone level"),
        ("r", "refresh", "Refresh"),
    ]

    CSS = """
    Screen {
        align: center middle;
        padding: 1;
    }
    ContentSwitcher {
        border: round $primary;
        height: 1fr;
    }
    
    .Selected_content {
        background: $primary;
    }
    
    #fans_table {
        border: round $primary;
    }
    #zones_table {
        border: round $primary;
    }
    #current_fan_mode {
        width: 40;
        padding: 1;
        background: $secondary;
    }
    """


    def __init__(self, config_file: str) -> None:
        """"""
        # Load configuration.
        self.config = Config(config_file)
        self.ipmi = Ipmi(self.config.ipmi_command, self.config.ipmi_fan_mode_delay, self.config.ipmi_fan_level_delay)
        self.read_data()
        super().__init__()

    def read_data(self) -> None:
        self.sensors = self.ipmi.read_sensors()
        self.zones = self.ipmi.read_zones()
        self.fan_mode = self.ipmi.get_fan_mode()
        self.events = self.ipmi.read_events()

    def compose(self) -> ComposeResult:
        self.title="IPMI Explorer"
        yield Header(show_clock=False)
        yield Footer()
        with HorizontalGroup():
            yield Button("Sensors", id="sensors_page", variant="primary")
            yield Button("Fans", id="fans_page")
            yield Button("Events", id="events_page")
            yield Button("BMC", id="bmc_page")
            yield Button("Settings", id="settings_page")
        with ContentSwitcher(initial="sensors_page"):
            yield DataTable(id="sensors_page", cursor_type='row', zebra_stripes=True)
            with VerticalScroll(id="fans_page"):
                with HorizontalGroup():
                    yield Label(f"Current fan mode: {self.ipmi.get_fan_mode_name(self.fan_mode)}"
                                f" ({self.fan_mode})", id="current_fan_mode", )
                    yield Button("Set fan mode", id="set_fan_mode")
                    yield Button("Explore", id="find_zones")
                with HorizontalGroup():
                    yield DataTable(id="fans_table", cursor_type='row', zebra_stripes=True)
                    yield DataTable(id="zones_table", cursor_type='row', zebra_stripes=True)
            with ScrollableContainer(id="events_page"):
                yield Label(self.events)
            with VerticalScroll(id="bmc_page"):
                yield Label("BMC")
            with VerticalScroll(id="settings_page"):
                yield Label("Settings")

    def action_set_threshold(self) -> None:
        if self.query_one(ContentSwitcher).current == "sensors_page":
            print("Threshold.")

    def action_set_zone_level(self) -> None:

        def save_new_level(result: int) -> None:
            zone = self.query_one("#zones_table", DataTable).cursor_row
            self.ipmi.set_fan_level(zone, result)
            result = self.ipmi.get_fan_level(zone)
            table = self.query_one("#zones_table", DataTable)
            table.update_cell_at(Coordinate(zone, 2), result, update_width=True)

        table = self.query_one("#zones_table", DataTable)
        self.push_screen(SetLevelWindow(table.cursor_row), save_new_level)

    def action_refresh(self) -> None:
        """Re-read data and refresh the display."""

        # Re-read data from IPMI.
        self.read_data()

        # Update table on "Sensors" page.
        table = self.query_one("#sensors_page", DataTable)
        row=0
        for r in self.sensors:
            if r.has_reading:
                if r.has_unit:
                    if r.type_id == IpmiSensor.TYPE_VOLTAGE:
                        value = f'{r.reading:.3f}'
                    else:
                        value = f'{r.reading}'
                else:
                    value = f'0x{r.reading:02x}'
            else:
                value = IpmiSensor.NO_VALUE
            if r.has_reading and r.has_threshold:
                if r.has_unr:
                    unr = f'{r.unr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.unr}'
                else:
                    unr = IpmiSensor.NO_VALUE
                if r.has_ucr:
                    ucr = f'{r.ucr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.ucr}'
                else:
                    ucr = IpmiSensor.NO_VALUE
                if r.has_unr:
                    unc = f'{r.unc:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.unc}'
                else:
                    unc = IpmiSensor.NO_VALUE
                if r.has_lnr:
                    lnr = f'{r.lnr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lnr}'
                else:
                    lnr = IpmiSensor.NO_VALUE
                if r.has_lcr:
                    lcr = f'{r.lcr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lcr}'
                else:
                    lcr = IpmiSensor.NO_VALUE
                if r.has_lnc:
                    lnc = f'{r.lnc:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lnc}'
                else:
                    lnc = IpmiSensor.NO_VALUE
            else:
                unr = ucr = unc = lnr = lcr = lnc = IpmiSensor.NO_VALUE
            table.update_cell_at(Coordinate(row, 3), value, update_width=True)
            table.update_cell_at(Coordinate(row, 5), lnr, update_width=True)
            table.update_cell_at(Coordinate(row, 6), lcr, update_width=True)
            table.update_cell_at(Coordinate(row, 7), lnc, update_width=True)
            table.update_cell_at(Coordinate(row, 8), unc, update_width=True)
            table.update_cell_at(Coordinate(row, 9), ucr, update_width=True)
            table.update_cell_at(Coordinate(row, 10), unr, update_width=True)
            row+=1

        # Update tables on "Fans" page.
        table = self.query_one("#fans_table", DataTable)
        row = 0
        for r in self.sensors:
            if r.type_id == IpmiSensor.TYPE_FAN:
                table.update_cell_at(Coordinate(row, 2), r.reading if r.has_reading else IpmiSensor.NO_VALUE, update_width=True)
                row += 1
        row = 0
        table = self.query_one("#zones_table", DataTable)
        for z in self.zones:
            table.update_cell_at(Coordinate(row, 2), z.level, update_width=True)
            row += 1

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """All button pressed event processed here."""
        def save_new_fan_mode(result: int) -> None:
            if result != -1 and result != self.fan_mode:
                self.ipmi.set_fan_mode(result)
                self.fan_mode = self.ipmi.get_fan_mode()
                self.query_one("#current_fan_mode",
                               Label).update(f"Current fan mode: {self.ipmi.get_fan_mode_name(self.fan_mode)}"
                                             f" ({self.fan_mode})")

        if event.button.id in {"sensors_page", "fans_page", "events_page", "bmc_page", "settings_page"}:
            self.query_one('#'+self.query_one(ContentSwitcher).current, Button).variant = "default"
            self.query_one(ContentSwitcher).current = event.button.id
            self.query_one('#'+event.button.id, Button).variant = "primary"
        if event.button.id == "set_fan_mode":
            m = SetFanModeWindow(self.fan_mode)
            self.push_screen(m, callback=save_new_fan_mode)

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
                value = IpmiSensor.NO_VALUE
                unit = IpmiSensor.EMPTY_VALUE
            if r.has_reading and r.has_threshold:
                if r.has_unr:
                    unr = f'{r.unr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.unr}'
                else:
                    unr = IpmiSensor.NO_VALUE
                if r.has_ucr:
                    ucr = f'{r.ucr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.ucr}'
                else:
                    ucr = IpmiSensor.NO_VALUE
                if r.has_unr:
                    unc = f'{r.unc:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.unc}'
                else:
                    unc = IpmiSensor.NO_VALUE
                if r.has_lnr:
                    lnr = f'{r.lnr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lnr}'
                else:
                    lnr = IpmiSensor.NO_VALUE
                if r.has_lcr:
                    lcr = f'{r.lcr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lcr}'
                else:
                    lcr = IpmiSensor.NO_VALUE
                if r.has_lnc:
                    lnc = f'{r.lnc:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lnc}'
                else:
                    lnc = IpmiSensor.NO_VALUE
            else:
                unr = ucr = unc = lnr = lcr = lnc = IpmiSensor.NO_VALUE
            table.add_row(f'0x{r.id:x}', r.name, r.location, value, unit, lnr, lcr, lnc, unc, ucr, unr,
                          key=f"0x{r.id:x}")

        # "Fans" page.
        table = self.query_one("#fans_table", DataTable)
        table.border_title = "Fans"
        table.add_columns("ID", "Name", "RPM", "Level")
        for r in self.sensors:
            if r.type_id == IpmiSensor.TYPE_FAN:
                table.add_rows([(f"0x{r.id:02x}", r.name, r.reading if r.has_reading else IpmiSensor.NO_VALUE,
                                 IpmiSensor.NO_VALUE)])
        table = self.query_one("#zones_table", DataTable)
        table.border_title = "Zones"
        table.add_columns("Number", "Name", "Level", "Fans")
        for z in self.zones:
            table.add_rows([(f"{z.id}", z.name, z.level, "-")])

# End.
