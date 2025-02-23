#
#   cmd.py (C) 2025, Peter Sulyok
#   ipmiexplorer package: Config() class implementation.
#
import os
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

        # If configuration file name is not specified, use the default path.
        if '~' in config_file:
            self.config_file = os.path.expanduser(config_file)

        # Create a new config parser class.
        self.pc = ConfigParser()

        if not self.pc.read(self.config_file):

            config_dir = Path(self.config_file).parent.absolute()
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            default_config = """#
#   settings.ini (C) 2025, Peter Sulyok
#   ipmiexplorer configuration parameters
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
            """
            with open(self.config_file, 'w+t', encoding='UTF-8') as f:
                f.write(default_config)
            self.pc.read(self.config_file);

        self.ipmi_command = self.pc[self.CS_IPMI].get(self.CV_IPMI_COMMAND, self.DEF_IPMITOOL_PATH)
        self.ipmi_fan_mode_delay = self.pc[self.CS_IPMI].getint(self.CV_IPMI_FAN_MODE_DELAY, fallback=10)
        self.ipmi_fan_level_delay = self.pc[self.CS_IPMI].getint(self.CV_IPMI_FAN_MODE_DELAY, fallback=2)
