#
#   cmd.py (C) 2025, Peter Sulyok
#   ipmiexplorer package: main() function implementation, command-line interface.
#
from .ipmiexplorerapp import IpmiExplorerApp


def main() -> None:
    """Entry point of the `ipmiexplorer` command."""
    app = IpmiExplorerApp()
    app.run()


if __name__ == '__main__':
    main()

# End.
