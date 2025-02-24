#
#   cmd.py (C) 2025, Peter Sulyok
#   ipmiexp package: Config() class implementation.
#
import os
import sys
from configparser import ConfigParser
from pathlib import Path

class Config:

    DEF_IPMITOOL_PATH: str = '/usr/bin/ipmitool'
    DEF_CONFIG_FILE: str = '~/.config/ipmiexplorer/settings.ini'

    # Constant values for the configuration parameters.
    CS_IPMI: str = 'Ipmi'
    CV_IPMI_COMMAND: str = 'command'
    CV_IPMI_FAN_MODE_DELAY: str = 'fan_mode_delay'
    CV_IPMI_FAN_LEVEL_DELAY: str = 'fan_level_delay'

    config_file: str        # Config file name.
    pc: ConfigParser    # Parsed configuration.

    ipmi_command: str
    ipmi_fan_mode_delay: int
    ipmi_fan_level_delay: int

    def __init__(self, config_file: str):

        # Expand path to user directory if needed.
        if '~' in config_file:
            self.config_file = os.path.expanduser(config_file)
        else:
            self.config_file = config_file

        # Create a new config parser class.
        self.pc = ConfigParser()

        # If parsing of the configuration file is not successful.
        if not self.pc.read(self.config_file):

            # Create the parent directory.
            config_dir = Path(self.config_file).parent.absolute()
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            # Create a new config file with default values.
            with open(self.config_file, 'w+t', encoding='UTF-8') as f:
                f.write("""#
#   settings.ini (C) 2025, Peter Sulyok
#   ipmiexp configuration parameters
#

[Ipmi]
# Path for ipmitool (str, default=/usr/bin/ipmitool)
command=/usr/bin/ipmitool
# Delay time after changing IPMI fan mode (int, seconds, default=10)
fan_mode_delay=10
# Delay time after changing IPMI fan level (int, seconds, default=2)
fan_level_delay=2
# IPMI parameters for remote access (HOST is the BMC network address).
#remote_parameters=-U USERNAME -P PASSWORD -H HOST
""")
            # Read the configuration again and exit if not successful.
            if not self.pc.read(config_file):
                sys.exit(5)

        # Read IPMI configuration parameters.
        self.ipmi_command = self.pc[self.CS_IPMI].get(self.CV_IPMI_COMMAND, self.DEF_IPMITOOL_PATH)
        self.ipmi_fan_mode_delay = self.pc[self.CS_IPMI].getint(self.CV_IPMI_FAN_MODE_DELAY, fallback=10)
        self.ipmi_fan_level_delay = self.pc[self.CS_IPMI].getint(self.CV_IPMI_FAN_MODE_DELAY, fallback=2)
