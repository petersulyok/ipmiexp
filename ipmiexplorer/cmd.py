#
#   cmd.py (C) 2025, Peter Sulyok
#   ipmiexplorer package: main() function implementation, command-line interface.
#
from argparse import ArgumentParser, Namespace
from ipmiexplorer.config import Config
from ipmiexplorer.ipmiexplorerapp import IpmiExplorerApp

version_str: str = "0.1.0"


def main() -> None:
    """Entry point of the `ipmiexplorer` command."""
    ap: ArgumentParser      # Argument parser.
    pr:Namespace            # Parsed arguments.

    # Parse the command line arguments.
    ap = ArgumentParser(description='An IPMI explorer program.')
    ap.add_argument('-c', action='store', dest='config_file', default=Config.DEF_CONFIG_FILE,
                            help='configuration file')
    ap.add_argument('-v', action='version', version='%(prog)s ' + version_str)
    # Note: the argument parser can exit here with the following exit codes:
    # 0 - printing help or version text
    # 2 - invalid parameter
    pr = ap.parse_args()

    app = IpmiExplorerApp(pr.config_file)
    app.run()


if __name__ == '__main__':
    main()

# End.
