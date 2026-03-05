#
#   cmd.py (C) 2025, Peter Sulyok
#   ipmiexp package: main() function implementation, command-line interface.
#
from argparse import ArgumentParser, Namespace
from ipmiexp.config import Config
from ipmiexp.app import IpmiExpApp

version_str: str = "0.1.0"


def main() -> None:
    """Entry point of the `ipmiexp` command."""
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

    app = IpmiExpApp(pr.config_file)
    app.run()


if __name__ == '__main__':
    main()

# End.
