#
#   cmd.py (C) 2025, Peter Sulyok
#   ipmiexp package: Config() class implementation.
#
import os
import sys
from configparser import ConfigParser
from pathlib import Path
from typing import List


class Config:

    DEF_IPMITOOL_PATH: str = '/usr/bin/ipmitool'
    DEF_CONFIG_FILE: str = '~/.config/ipmiexp/settings.ini'
    DEF_CONFIG_VALUES: str = """#
#   settings.ini (C) 2025, Peter Sulyok
#   ipmiexp program configuration parameters
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

[Zone names]
0=CPU zone
1=Peripheral zone
2=Zone 2
3=Zone 3
4=Zone 4
5=Zone 5
6=Zone 6
7=Zone 7
"""

    # Constant values for the configuration parameters.
    CS_IPMI: str = 'Ipmi'
    CS_ZONE: str = 'Zone names'

    CV_IPMI_COMMAND: str = 'command'
    CV_IPMI_FAN_MODE_DELAY: str = 'fan_mode_delay'
    CV_IPMI_FAN_LEVEL_DELAY: str = 'fan_level_delay'

    config_file: str        # Config file name.
    pc: ConfigParser        # Parsed configuration.

    ipmi_command: str
    ipmi_fan_mode_delay: int
    ipmi_fan_level_delay: int
    zone_names:List[str]

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
                f.write(self.DEF_CONFIG_VALUES)

            # Read the configuration again and exit if not successful.
            if not self.pc.read(config_file):
                sys.exit(5)

        # Read IPMI configuration parameters.
        self.ipmi_command = self.pc[self.CS_IPMI].get(self.CV_IPMI_COMMAND, self.DEF_IPMITOOL_PATH)
        self.ipmi_fan_mode_delay = self.pc[self.CS_IPMI].getint(self.CV_IPMI_FAN_MODE_DELAY, fallback=10)
        self.ipmi_fan_level_delay = self.pc[self.CS_IPMI].getint(self.CV_IPMI_FAN_MODE_DELAY, fallback=2)

        # Read zone names.
        self.zone_names = []
        index=0
        while index < 8:
            s = self.pc[self.CS_ZONE].get(str(index))
            if s is None:
                break
            self.zone_names.append(s)
            index += 1

# End.