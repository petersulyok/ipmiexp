#
#   ipmi.py (C) 2025, Peter Sulyok
#   ipmiexplorer package: Ipmi() class implementation.
#
import configparser
import subprocess
import time


class Ipmi:
    """IPMI class implementation, interface for `ipmitool`."""

    command: str                        # Full path for ipmitool command.
    fan_mode_delay: float               # Delay time after execution of IPMI set fan mode function
    fan_level_delay: float              # Delay time after execution of IPMI set fan level function
    swapped_zones: bool                 # CPU and HD zones are swapped

    # Constant values for IPMI fan modes:
    STANDARD_MODE: int = 0
    FULL_MODE: int = 1
    OPTIMAL_MODE: int = 2
    PUE_MODE: int = 3
    HEAVY_IO_MODE: int = 4

    # Constant values for IPMI fan zones:
    CPU_ZONE: int = 0
    HD_ZONE: int = 1

    # Constant values for the results of IPMI operations:
    SUCCESS: int = 0
    ERROR: int = -1

    # Constant values for the configuration parameters.
    CS_IPMI: str = 'Ipmi'
    CV_IPMI_COMMAND: str = 'command'
    CV_IPMI_FAN_MODE_DELAY: str = 'fan_mode_delay'
    CV_IPMI_FAN_LEVEL_DELAY: str = 'fan_level_delay'

    def __init__(self, config: configparser.ConfigParser) -> None:
        """Initialize the Ipmi class with a log class and with a configuration class.

        Args:
            config (configparser.ConfigParser): configuration values
        """
        # Set default or read from configuration
        self.command = config[self.CS_IPMI].get(self.CV_IPMI_COMMAND, '/usr/bin/ipmitool')
        self.fan_mode_delay = config[self.CS_IPMI].getint(self.CV_IPMI_FAN_MODE_DELAY, fallback=10)
        self.fan_level_delay = config[self.CS_IPMI].getint(self.CV_IPMI_FAN_LEVEL_DELAY, fallback=2)

        # Check 1: fan_mode_delay must be positive.
        if self.fan_mode_delay < 0:
            raise ValueError(f'Negative fan_mode_delay ({self.fan_mode_delay})')
        # Check 2: fan_mode_delay must be positive.
        if self.fan_level_delay < 0:
            raise ValueError(f'Negative fan_level_delay ({self.fan_level_delay})')

    def get_fan_mode(self) -> int:
        """Get the current IPMI fan mode.

        Returns:
            int: fan mode (ERROR, STANDARD_MODE, FULL_MODE, OPTIMAL_MODE, PUE_MODE, HEAVY_IO_MODE)

        Raises:
            FileNotFoundError: ipmitool command cannot be found
            ValueError: output of the ipmitool cannot be interpreted/converted
            RuntimeError: ipmitool execution problem in IPMI (e.g. non-root user, incompatible IPMI system
                or motherboard)
        """
        r: subprocess.CompletedProcess  # result of the executed process
        m: int                          # fan mode

        # Read the current IPMI fan mode.
        try:
            r = subprocess.run([self.command, 'raw', '0x30', '0x45', '0x00'],
                               check=False, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(r.stderr)
            m = int(r.stdout)
        except (FileNotFoundError, ValueError) as e:
            raise e
        return m

    def get_fan_mode_name(self, mode: int) -> str:
        """Get the name of the specified IPMI fan mode.

        Args:
            mode (int): fan mode
        Returns:
            str: name of the fan mode ('ERROR', 'STANDARD', 'FULL', 'OPTIMAL', 'PUE', 'HEAVY IO')
        """
        fan_mode_name: str              # Name of the fan mode

        fan_mode_name = 'ERROR'
        if mode == self.STANDARD_MODE:
            fan_mode_name = 'STANDARD'
        elif mode == self.FULL_MODE:
            fan_mode_name = 'FULL'
        elif mode == self.OPTIMAL_MODE:
            fan_mode_name = 'OPTIMAL'
        elif mode == self.PUE_MODE:
            fan_mode_name = 'PUE'
        elif mode == self.HEAVY_IO_MODE:
            fan_mode_name = 'HEAVY IO'
        return fan_mode_name

    def set_fan_mode(self, mode: int) -> None:
        """Set the IPMI fan mode.

        Args:
            mode (int): fan mode (STANDARD_MODE, FULL_MODE, OPTIMAL_MODE, HEAVY_IO_MODE)
        """
        # Validate mode parameter.
        if mode not in {self.STANDARD_MODE, self.FULL_MODE, self.OPTIMAL_MODE, self.PUE_MODE, self.HEAVY_IO_MODE}:
            raise ValueError(f'Invalid fan mode value ({mode}).')
        # Call ipmitool command and set the new IPMI fan mode.
        try:
            subprocess.run([self.command, 'raw', '0x30', '0x45', '0x01', str(mode)],
                           check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError as e:
            raise e
        # Give time for IPMI system/fans to apply changes in the new fan mode.
        time.sleep(self.fan_mode_delay)

    def set_fan_level(self, zone: int, level: int) -> None:
        """Set the IPMI fan level in a specific zone. Raise an exception in case of invalid parameters.

        Args:
            zone (int): fan zone (CPU_ZONE, HD_ZONE)
            level (int): fan level in % (0-100)
        """
        # Validate zone parameter
        if zone not in {self.CPU_ZONE, self.HD_ZONE}:
            raise ValueError(f'Invalid value: zone ({zone}).')
        # Handle swapped zones
        if self.swapped_zones:
            zone = 1 - zone
        # Validate level parameter (must be in the interval [0..100%])
        if level not in range(0, 101):
            raise ValueError(f'Invalid value: level ({level}).')
        # Set the new IPMI fan level in the specific zone
        try:
            subprocess.run([self.command, 'raw', '0x30', '0x70', '0x66', '0x01', str(zone), str(level)],
                           check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError as e:
            raise e
        # Give time for IPMI and fans to spin up/down.
        time.sleep(self.fan_level_delay)

# End.