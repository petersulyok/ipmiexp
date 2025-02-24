#
#   ipmiexplorerapp.py (C) 2025, Peter Sulyok
#   ipmiexplorer package: IpmiExplorerApp() class implementation.
#
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

from ipmiexplorer.config import Config
from ipmiexplorer.ipmi import Ipmi

class IpmiExplorerApp(App):

    config: Config      # Configuration class.
    ipmi: Ipmi          # Ipmi class.

    def __init__(self, config_file: str) -> None:
        """"""
        # Load configuration.
        self.config = Config(config_file)
        self.ipmi = Ipmi(self.config.ipmi_command, self.config.ipmi_fan_mode_delay, self.config.ipmi_fan_level_delay)
        self.ipmi.read_sensors()
        super().__init__()


    def compose(self) -> ComposeResult:
        self.title="IPMI Explorer"
        yield Header(show_clock=True)
        yield Footer()
