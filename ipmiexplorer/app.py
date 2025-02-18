#
#   app.py (C) 2025, Peter Sulyok
#   ipmiexplorer package: IpmiExplorerApp() class implementation.
#

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

class IpmiExplorerApp(App):

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()