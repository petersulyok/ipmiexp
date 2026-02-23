#
#   app.py (C) 2025, Peter Sulyok
#   ipmiexp package: IpmiExpApp() class implementation.
#
from typing import List, Union
from textual.app import App, ComposeResult
from textual.coordinate import Coordinate
from textual import work
from textual.widgets import Header, Footer, LoadingIndicator
from textual.containers import HorizontalGroup, VerticalScroll, ScrollableContainer
from textual.widgets import Button, ContentSwitcher, DataTable, Label

from ipmiexp.config import Config
from ipmiexp.ipmi import Ipmi, IpmiSensor, IpmiZone
from ipmiexp.modal import ConfirmWindow, SetFanModeWindow, SetLevelWindow, SetThresholdWindow


class IpmiExpApp(App):

    config: Config              # Configuration class.
    ipmi: Ipmi                  # Ipmi class.
    sensors: List[IpmiSensor]   # IPMI sensors.
    zones: List[IpmiZone]       # Ipmi zones.
    fan_mode: int               # Current IPMI fan mode.
    events: str                 # IPMI events.
    bmc_info: str               # BMC information text.
    _loaded: set                # Set of tab IDs whose data has been loaded.

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
    #bmc_reset {
        margin-top: 1;
    }
    """

    def __init__(self, config_file: str) -> None:
        self.config = Config(config_file)
        self.ipmi = Ipmi(self.config.ipmi_command, self.config.ipmi_fan_mode_delay,
                         self.config.ipmi_fan_level_delay, self.config.zone_names)
        self.sensors = []
        self.zones = []
        self.fan_mode = 0
        self.events = ""
        self.bmc_info = ""
        self._loaded = set()
        super().__init__()

    def compose(self) -> ComposeResult:
        self.title = "IPMI Explorer"
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
                    yield Label("Current fan mode: -", id="current_fan_mode")
                    yield Button("Set fan mode", id="set_fan_mode")
                    yield Button("Explore", id="find_zones")
                with HorizontalGroup():
                    yield DataTable(id="fans_table", cursor_type='row', zebra_stripes=True)
                    yield DataTable(id="zones_table", cursor_type='row', zebra_stripes=True)
            with ScrollableContainer(id="events_page"):
                yield LoadingIndicator(id="events_loading")
                yield Label("", id="events_label")
            with VerticalScroll(id="bmc_page"):
                yield LoadingIndicator(id="bmc_loading")
                yield Label("", id="bmc_label")
                yield Button("BMC Reset", id="bmc_reset", variant="error")
            with VerticalScroll(id="settings_page"):
                yield Label("Settings")

    def on_mount(self) -> None:
        # Set up column structure for sensors_page — data loaded lazily.
        table = self.query_one("#sensors_page", DataTable)
        table.loading = True
        table.add_columns("ID", "Name", "Location", "Reading", "Unit", "LNR", "LCR", "LNC", "UNC", "UCR", "UNR")

        # Set up column structure for fans_page tables — data loaded lazily.
        fans_table = self.query_one("#fans_table", DataTable)
        fans_table.loading = True
        fans_table.border_title = "Fans"
        fans_table.add_columns("ID", "Name", "RPM", "Level")

        zones_table = self.query_one("#zones_table", DataTable)
        zones_table.loading = True
        zones_table.border_title = "Zones"
        zones_table.add_columns("ID", "Name", "Level", "Fans")

        # Hide events content until loaded.
        self.query_one("#events_label", Label).display = False

        # Hide BMC content until loaded.
        self.query_one("#bmc_label", Label).display = False
        self.query_one("#bmc_reset", Button).display = False

        # Trigger load for the initial tab.
        self._load_tab("sensors_page")

    def _load_tab(self, tab_id: str) -> None:
        """Trigger background data loading for a tab if not already loaded."""
        if tab_id in self._loaded:
            return
        self._loaded.add(tab_id)
        if tab_id == "sensors_page":
            self._load_sensors_page()
        elif tab_id == "fans_page":
            self._load_fans_page()
        elif tab_id == "events_page":
            self._load_events_page()
        elif tab_id == "bmc_page":
            self._load_bmc_page()

    @work(thread=True)
    def _load_sensors_page(self) -> None:
        """Background worker: fetch sensor data and populate the sensors table."""
        sensors = self.ipmi.read_sensors()
        self.call_from_thread(self._populate_sensors_table, sensors)

    @work(thread=True)
    def _load_fans_page(self) -> None:
        """Background worker: fetch fan/zone data and populate the fans page."""
        fan_mode = self.ipmi.get_fan_mode()
        zones = self.ipmi.read_zones()
        # Reuse already-loaded sensor data if available, otherwise fetch independently.
        sensors = self.sensors if self.sensors else self.ipmi.read_sensors()
        self.call_from_thread(self._populate_fans_page, sensors, fan_mode, zones)

    @work(thread=True)
    def _load_events_page(self) -> None:
        """Background worker: fetch event log and populate the events page."""
        events = self.ipmi.read_events()
        self.call_from_thread(self._populate_events_page, events)

    @work(thread=True)
    def _load_bmc_page(self) -> None:
        """Background worker: fetch BMC info and populate the BMC page."""
        bmc_info = self.ipmi.read_bmc_info()
        self.call_from_thread(self._populate_bmc_page, bmc_info)

    def _populate_sensors_table(self, sensors: List[IpmiSensor]) -> None:
        """Populate the sensors DataTable (called on main thread)."""
        self.sensors = sensors
        table = self.query_one("#sensors_page", DataTable)
        for r in sensors:
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
                unr = (f'{r.unr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.unr}') if r.has_unr else IpmiSensor.NO_VALUE
                ucr = (f'{r.ucr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.ucr}') if r.has_ucr else IpmiSensor.NO_VALUE
                unc = (f'{r.unc:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.unc}') if r.has_unc else IpmiSensor.NO_VALUE
                lnr = (f'{r.lnr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lnr}') if r.has_lnr else IpmiSensor.NO_VALUE
                lcr = (f'{r.lcr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lcr}') if r.has_lcr else IpmiSensor.NO_VALUE
                lnc = (f'{r.lnc:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lnc}') if r.has_lnc else IpmiSensor.NO_VALUE
            else:
                unr = ucr = unc = lnr = lcr = lnc = IpmiSensor.NO_VALUE
            table.add_row(f'0x{r.id:x}', r.name, r.location, value, unit, lnr, lcr, lnc, unc, ucr, unr,
                          key=f"0x{r.id:x}")
        table.loading = False

    def _populate_fans_page(self, sensors: List[IpmiSensor], fan_mode: int, zones: List[IpmiZone]) -> None:
        """Populate the fans page tables (called on main thread)."""
        self.fan_mode = fan_mode
        self.zones = zones
        if not self.sensors:
            self.sensors = sensors

        self.query_one("#current_fan_mode", Label).update(
            f"Current fan mode: {self.ipmi.get_fan_mode_name(fan_mode)} ({fan_mode})")

        fans_table = self.query_one("#fans_table", DataTable)
        for r in sensors:
            if r.type_id == IpmiSensor.TYPE_FAN:
                fans_table.add_rows([(f"0x{r.id:02x}", r.name,
                                      r.reading if r.has_reading else IpmiSensor.NO_VALUE,
                                      IpmiSensor.NO_VALUE)])
        fans_table.loading = False

        zones_table = self.query_one("#zones_table", DataTable)
        for z in zones:
            zones_table.add_rows([(f'{z.id}', z.name, z.level, "-")])
        zones_table.loading = False

    def _populate_events_page(self, events: str) -> None:
        """Update the events page content (called on main thread)."""
        self.events = events
        self.query_one("#events_loading", LoadingIndicator).display = False
        label = self.query_one("#events_label", Label)
        label.update(events)
        label.display = True

    def _populate_bmc_page(self, bmc_info: str) -> None:
        """Update the BMC page content (called on main thread)."""
        self.bmc_info = bmc_info
        self.query_one("#bmc_loading", LoadingIndicator).display = False
        label = self.query_one("#bmc_label", Label)
        label.update(bmc_info)
        label.display = True
        self.query_one("#bmc_reset", Button).display = True

    def action_set_threshold(self) -> None:

        def save_threshold(result: List[Union[float, int]]) -> None:
            if len(result):
                table = self.query_one("#sensors_page", DataTable)
                sensor = self.sensors[table.cursor_row]
                lower = []
                upper = []
                is_float = bool(sensor.type_id == IpmiSensor.TYPE_VOLTAGE)
                n = 0
                if sensor.has_lnr:
                    lower.append(f'{result[n]:.3f}' if is_float else f'{result[n]}')
                    n+=1
                if sensor.has_lcr:
                    lower.append(f'{result[n]:.3f}' if is_float else f'{result[n]}')
                    n += 1
                if sensor.has_lnc:
                    lower.append(f'{result[n]:.3f}' if is_float else f'{result[n]}')
                    n += 1
                if sensor.has_unc:
                    upper.append(f'{result[n]:.3f}' if is_float else f'{result[n]}')
                    n += 1
                if sensor.has_ucr:
                    upper.append(f'{result[n]:.3f}' if is_float else f'{result[n]}')
                    n += 1
                if sensor.has_unr:
                    upper.append(f'{result[n]:.3f}' if is_float else f'{result[n]}')
                    n += 1
                if len(lower):
                    self.ipmi.set_lower_threshold(sensor.name, lower)
                if len(upper):
                    self.ipmi.set_upper_threshold(sensor.name, upper)
                self.sensors = self.ipmi.read_sensors()
                self.update_sensor_table()

        if self.query_one(ContentSwitcher).current == "sensors_page" and self.sensors:
            table = self.query_one("#sensors_page", DataTable)
            sensor=self.sensors[table.cursor_row]
            if sensor.has_reading and sensor.has_threshold:
                self.push_screen(SetThresholdWindow(sensor), save_threshold)

    def action_set_zone_level(self) -> None:

        def save_new_level(result: int) -> None:
            if result in range(0, 100):
                zone = self.query_one("#zones_table", DataTable).cursor_row
                self.ipmi.set_fan_level(zone, result)
                result = self.ipmi.get_fan_level(zone)
                table = self.query_one("#zones_table", DataTable)
                table.update_cell_at(Coordinate(zone, 2), result, update_width=True)

        if self.query_one(ContentSwitcher).current == "fans_page" and self.zones:
            table = self.query_one("#zones_table", DataTable)
            self.push_screen(SetLevelWindow(self.zones[table.cursor_row]), save_new_level)

    def action_refresh(self) -> None:
        """Re-read data for all loaded tabs and refresh the display."""

        # Refresh sensors data and update sensors_page table.
        if "sensors_page" in self._loaded:
            self.sensors = self.ipmi.read_sensors()
            self.update_sensor_table()

        # Refresh fans_page using updated sensor data.
        if "fans_page" in self._loaded:
            table = self.query_one("#fans_table", DataTable)
            row = 0
            for r in self.sensors:
                if r.type_id == IpmiSensor.TYPE_FAN:
                    table.update_cell_at(Coordinate(row, 2),
                                         r.reading if r.has_reading else IpmiSensor.NO_VALUE,
                                         update_width=True)
                    row += 1
            self.zones = self.ipmi.read_zones()
            table = self.query_one("#zones_table", DataTable)
            row = 0
            for z in self.zones:
                table.update_cell_at(Coordinate(row, 2), z.level, update_width=True)
                row += 1

        # Refresh events_page content.
        if "events_page" in self._loaded:
            self.events = self.ipmi.read_events()
            self.query_one("#events_label", Label).update(self.events)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """All button pressed event processed here."""

        def save_new_fan_mode(result: int) -> None:
            if result != -1 and result != self.fan_mode:
                self.ipmi.set_fan_mode(result)
                self.fan_mode = self.ipmi.get_fan_mode()
                self.query_one("#current_fan_mode", Label).update(
                               f"Current fan mode: {self.ipmi.get_fan_mode_name(self.fan_mode)}"
                               f" ({self.fan_mode})")

        if event.button.id in {"sensors_page", "fans_page", "events_page", "bmc_page", "settings_page"}:
            self.query_one('#'+self.query_one(ContentSwitcher).current, Button).variant = "default"
            self.query_one(ContentSwitcher).current = event.button.id
            self.query_one('#'+event.button.id, Button).variant = "primary"
            self._load_tab(event.button.id)
        if event.button.id == "set_fan_mode":
            m = SetFanModeWindow(self.fan_mode)
            self.push_screen(m, callback=save_new_fan_mode)
        if event.button.id == "bmc_reset":
            def do_bmc_reset(confirmed: bool) -> None:
                if confirmed:
                    self.ipmi.bmc_reset()
            self.push_screen(ConfirmWindow("Reset the BMC controller?"), callback=do_bmc_reset)

    def update_sensor_table(self) -> None:
        """Update the sensor table (Reading, threshold columns) after re-reading the sensors."""
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
                unr = (f'{r.unr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.unr}') if r.has_unr else IpmiSensor.NO_VALUE
                ucr = (f'{r.ucr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.ucr}') if r.has_ucr else IpmiSensor.NO_VALUE
                unc = (f'{r.unc:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.unc}') if r.has_unc else IpmiSensor.NO_VALUE
                lnr = (f'{r.lnr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lnr}') if r.has_lnr else IpmiSensor.NO_VALUE
                lcr = (f'{r.lcr:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lcr}') if r.has_lcr else IpmiSensor.NO_VALUE
                lnc = (f'{r.lnc:.3f}' if r.type_id == IpmiSensor.TYPE_VOLTAGE else f'{r.lnc}') if r.has_lnc else IpmiSensor.NO_VALUE
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


# End.
