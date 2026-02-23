#
#   ipmi.py (C) 2025, Peter Sulyok
#   ipmiexp package: Ipmi() class implementation.
#
import re
import subprocess
import time
from typing import List, Union


class IpmiSensor:

    # Constants for sensor types.
    TYPE_TEMPERATURE: int = 0x01
    TYPE_VOLTAGE: int = 0x02
    TYPE_FAN: int = 0x04
    TYPE_PHYSICAL_SECURITY: int = 0x05
    TYPE_BATTERY = 0x29

    NO_VALUE: str = "-"
    EMPTY_VALUE: str = ""

    name: str                   # Sensor name.
    id: int                     # Sensor ID.
    entity_id: str              # Sensor entity ID.
    location: str               # Sensor location.
    type_name:str               # Sensor type name.
    type_id: int                # Sensor type ID.
    has_threshold: bool         # Sensor has thresholds.
    has_reading:bool            # Sensor has reading.
    has_unit:bool               # Sensor has unit.
    reading: Union[float, int]  # Sensor integer or float reading value.
    unit: str                   # Sensor reading unit.
    has_status: bool            # Sensor has status.
    status: str                 # Sensor status.
    has_unr:bool                # Sensor has non-recoverable threshold.
    unr: Union[float, int]      # Sensor upper non-recoverable threshold.
    has_ucr: bool               # Sensor has upper critical threshold.
    ucr: Union[float, int]      # Sensor upper critical threshold.
    has_unc: bool               # Sensor upper has non-critical threshold.
    unc: Union[float, int]      # Sensor upper non-critical threshold.
    has_lnr: bool               # Sensor has lower non-recoverable threshold.
    lnr: Union[float, int]      # Sensor lower non-recoverable threshold.
    has_lcr: Union[float, int]  # Sensor has lower critical threshold.
    lcr: Union[float, int]      # Sensor lower critical threshold.
    has_lnc: Union[float, int]  # Sensor has lower non-critical threshold.
    lnc: Union[float, int]      # Sensor lower non-critical threshold.


class IpmiZone:
    """Class for IPMI zone."""
    id: int                     # Zone ID.
    name: str                   # Zone name.
    level: int                  # Zone current fan level.
    fans: List[int]             # Connected fans in the zone


class Ipmi:
    """IPMI class implementation, interface for `ipmitool`."""

    command: str                        # Full path for ipmitool command.
    fan_mode_delay: float               # Delay time after execution of IPMI set fan mode function
    fan_level_delay: float              # Delay time after execution of IPMI set fan level function
    zone_names: List[str]               # Zone names.

    # Constant values for IPMI fan modes:
    STANDARD_MODE: int = 0
    FULL_MODE: int = 1
    OPTIMAL_MODE: int = 2
    PUE_MODE: int = 3
    HEAVY_IO_MODE: int = 4


    def __init__(self, command: str, fan_mode_delay: int, fan_level_delay: int, zone_names: List[str]) -> None:
        """Initialize the Ipmi class.

        Args:
            command (str): ipmitool command
            fan_mode_delay (int): delay in seconds for changing fan mode
            fan_level_delay (int): delay in seconds for changing fan level
        """
        # Set default or read from configuration
        self.command = command
        self.fan_mode_delay = fan_mode_delay
        self.fan_level_delay = fan_level_delay
        self.zone_names = zone_names

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
                raise RuntimeError(f'ipmitool error ({r.returncode}): {r.stderr}')
            m = int(r.stdout)
        except (FileNotFoundError, RuntimeError, ValueError) as e:
            raise e
        return m

    def get_fan_mode_name(self, mode: int) -> str:
        """Get the name of the specified IPMI fan mode.

        Args:
            mode (int): fan mode
        Returns:
            str: name of the fan mode ('???', 'STANDARD', 'FULL', 'OPTIMAL', 'PUE', 'HEAVY IO')
        """
        fan_mode_name: str              # Name of the fan mode

        fan_mode_name = '???'
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
            mode (int): fan mode (STANDARD_MODE, FULL_MODE, OPTIMAL_MODE, PUE_MODE, HEAVY_IO_MODE)
        """
        r: subprocess.CompletedProcess  # result of the executed process

        # Validate mode parameter.
        if mode not in {self.STANDARD_MODE, self.FULL_MODE, self.OPTIMAL_MODE, self.PUE_MODE, self.HEAVY_IO_MODE}:
            raise ValueError(f'Invalid fan mode value ({mode}).')
        # Call ipmitool command and set the new IPMI fan mode.
        try:
            r = subprocess.run([self.command, 'raw', '0x30', '0x45', '0x01', str(mode)],
                               check=False, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f'ipmitool error ({r.returncode}): {r.stderr}')
        except (FileNotFoundError, RuntimeError) as e:
            raise e
        # Give time for IPMI system/fans to apply changes in the new fan mode.
        time.sleep(self.fan_mode_delay)

    def set_fan_level(self, zone: int, level: int) -> None:
        """Set the IPMI fan level in a specific zone. Raise an exception in case of invalid parameters.

        Args:
            zone (int): fan zone (CPU_ZONE, HD_ZONE)
            level (int): fan level in % (0-100)
        """
        r: subprocess.CompletedProcess  # result of the executed process

        # Validate zone parameter
        if zone < 0:
            raise ValueError(f'Negative zone value ({zone}).')
        # Validate level parameter (must be in the interval [0..100%])
        if level not in range(0, 101):
            raise ValueError(f'Invalid level value ({level}).')
        # Set the new IPMI fan level in the specific zone
        try:
            r = subprocess.run([self.command, 'raw', '0x30', '0x70', '0x66', '0x01', str(zone), str(level)],
                           check=False, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f'ipmitool error ({r.returncode}): {r.stderr}')
        except (FileNotFoundError, RuntimeError) as e:
            raise e
        # Give time for IPMI and fans to spin up/down.
        time.sleep(self.fan_level_delay)

    def get_fan_level(self, zone: int) -> int:
        """Get the current fan level in a specific zone. Raise an exception in case of invalid parameters.

        Args:
            zone (int): fan zone (CPU_ZONE, HD_ZONE)
        Returns:
            int: fan level
        """
        r: subprocess.CompletedProcess  # result of the executed process
        l: int                          # zone level

        # Validate zone parameter
        if zone < 0:
            raise ValueError(f'Invalid zone value ({zone}).')
        # Get the current IPMI fan level in the specific zone
        try:
            r = subprocess.run([self.command, 'raw', '0x30', '0x70', '0x66', '0x00', str(zone)],
                               check=False, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f'ipmitool error ({r.returncode}): {r.stderr}')
            l = int(r.stdout, 16)
        except (FileNotFoundError, RuntimeError, ValueError) as e:
            raise e
        return l

    def read_sensors(self) -> List[IpmiSensor]:
        """Read the detailed IPMI sensors information."""

        r: subprocess.CompletedProcess  # result of the executed process
        output_lines: List[str]         # Output lines.
        result: List[IpmiSensor]        # List of IPMI sensors.

        # Read detailed IPMI sensor information.
        try:
            r = subprocess.run([self.command, '-v', 'sdr'],
                               check=False, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f'ipmitool error ({r.returncode}): {r.stderr}')
            output_lines = r.stdout.splitlines()
        except (FileNotFoundError, RuntimeError) as e:
            raise e

        # Parsing loop of the output.
        result = []
        n = 0
        while n < len(output_lines):

            # Read a sensor block.
            if 'Sensor ID' in output_lines[n]:

                # Create a new sensor class.
                s = IpmiSensor()
                s.has_threshold = False
                s.has_reading = False
                s.has_unit = False
                s.has_status = False
                s.has_unr = False
                s.has_ucr = False
                s.has_unc = False
                s.has_lnr = False
                s.has_lcr = False
                s.has_lnc = False

                # Read the 'Sensor ID' line.
                # https://docs.python.org/3/library/re.html
                m = re.match(r'^Sensor ID\s+:\s+(?P<name>.+)\s+\((?P<id>\S+)\)\s*$', output_lines[n])
                if m:
                    s.name = m['name']
                    try:
                        s.id = int(m['id'], 16)
                        n += 1
                    except ValueError as e:
                        raise e
                else:
                    raise RuntimeError(f'ipmitool parsing error ({output_lines[n]})')

                # Read the 'Entity ID' line.
                m = re.match(r'^\s+Entity ID\s+:\s+(?P<entity_id>\S+)\s+\((?P<location>.+)\)$', output_lines[n])
                if m:
                    s.entity_id = m['entity_id']
                    s.location = m['location']
                    n += 1
                else:
                    raise RuntimeError(f'ipmitool parsing error ({output_lines[n]})')

                # Read the 'Sensor Type' line.
                m = re.match(r'^\s+Sensor Type\s+\((?P<threshold>\S+)\)\s*:\s+(?P<type_name>.+)\s+\((?P<type_id>\S+)\)$',
                             output_lines[n])
                if m:
                    s.has_threshold = bool(m['threshold'] == 'Threshold')
                    s.type_name = m['type_name']
                    try:
                        s.type_id = int(m['type_id'], 16)
                        n += 1
                    except ValueError as e:
                        raise e
                else:
                    raise RuntimeError(f'ipmitool parsing error ({output_lines[n]})')

                # Read the 'Sensor Reading' line.
                m = re.match(r'^\s+Sensor Reading\s+:\s*No Reading\s*$', output_lines[n])
                if m is None:
                    s.has_reading = True

                    # Try to read the simple form (e.g. 'Sensor Reading        : 4h')
                    m = re.match(r'^\s+Sensor Reading\s+:\s*(?P<reading>\S+)h\s*$', output_lines[n])
                    if m:
                        try:
                            s.reading = int(m['reading'], 16)
                        except ValueError as e:
                            raise e
                        n += 1
                    else:
                        # Try to read the simple form (e.g. 'Sensor Reading        : 3.316 (+/- 0) Volts')
                        m = re.match(r'^\s+Sensor Reading\s+:\s+(?P<reading>\S+)\s+\(.*\)\s+(?P<unit>.+)\s*$', output_lines[n])
                        if m:
                            try:
                                if s.type_id == IpmiSensor.TYPE_VOLTAGE:
                                    s.reading = float(m['reading'])
                                else:
                                    s.reading = int(m['reading'])
                            except ValueError as e:
                                raise e
                            s.unit = m['unit']
                            s.has_unit = True
                            n += 1
                        else:
                            raise RuntimeError(f'ipmitool parsing error ({output_lines[n]})')

                # Parsing the remaining lines in the sensor block.
                while n < len(output_lines) and output_lines[n]:

                    # Read the 'Status' line.
                    if s.has_threshold and 'Status' in output_lines[n]:
                        m = re.match(r'^\s+Status\s+:\s*(?P<status>.+)\s*$', output_lines[n])
                        if m:
                            s.status = m['status']
                            if s.status == 'Not Available':
                                s.has_status = False
                            else:
                                s.has_status = True
                        else:
                            raise RuntimeError(f'ipmitool parsing error ({output_lines[n]})')

                    # Read the 'Upper non-recoverable' line.
                    elif s.has_threshold and 'Upper non-recoverable' in output_lines[n]:
                        m = re.match(r'^\s+Upper non-recoverable\s+:\s+(?P<threshold>\S+)\s*$', output_lines[n])
                        if m:
                            try:
                                if s.type_id == IpmiSensor.TYPE_VOLTAGE:
                                    s.unr = float(m['threshold'])
                                else:
                                    s.unr = int(float(m['threshold']))
                            except ValueError as e:
                                raise e
                            s.has_unr = True
                        else:
                            raise RuntimeError(f'ipmitool parsing error ({output_lines[n]})')

                    # Read the 'Upper critical' line.
                    elif s.has_threshold and 'Upper critical' in output_lines[n]:
                        m = re.match(r'^\s+Upper critical\s+:\s+(?P<threshold>\S+)\s*$', output_lines[n])
                        if m:
                            try:
                                if s.type_id == IpmiSensor.TYPE_VOLTAGE:
                                    s.ucr = float(m['threshold'])
                                else:
                                    s.ucr = int(float(m['threshold']))
                            except ValueError as e:
                                raise e
                            s.has_ucr = True
                        else:
                            raise RuntimeError(f'ipmitool parsing error ({output_lines[n]})')

                    # Read the 'Upper non-critical' line.
                    elif s.has_threshold and 'Upper non-critical' in output_lines[n]:
                        m = re.match(r'^\s+Upper non-critical\s+:\s+(?P<threshold>\S+)\s*$', output_lines[n])
                        if m:
                            try:
                                if s.type_id == IpmiSensor.TYPE_VOLTAGE:
                                    s.unc = float(m['threshold'])
                                else:
                                    s.unc = int(float(m['threshold']))
                            except ValueError as e:
                                raise e
                            s.has_unc = True
                        else:
                            raise RuntimeError(f'ipmitool parsing error ({output_lines[n]})')

                    # Read the 'Lower non-recoverable' line.
                    elif s.has_threshold and 'Lower non-recoverable' in output_lines[n]:
                        m = re.match(r'^\s+Lower non-recoverable\s+:\s+(?P<threshold>\S+)\s*$', output_lines[n])
                        if m:
                            try:
                                if s.type_id == IpmiSensor.TYPE_VOLTAGE:
                                    s.lnr = float(m['threshold'])
                                else:
                                    s.lnr = int(float(m['threshold']))
                            except ValueError as e:
                                raise e
                            s.has_lnr = True
                        else:
                            raise RuntimeError(f'ipmitool parsing error ({output_lines[n]})')

                    # Read the 'Lower critical' line.
                    elif s.has_threshold and 'Lower critical' in output_lines[n]:
                        m = re.match(r'^\s+Lower critical\s+:\s+(?P<threshold>\S+)\s*$', output_lines[n])
                        if m:
                            try:
                                if s.type_id == IpmiSensor.TYPE_VOLTAGE:
                                    s.lcr = float(m['threshold'])
                                else:
                                    s.lcr = int(float(m['threshold']))
                            except ValueError as e:
                                raise e
                            s.has_lcr = True
                        else:
                            raise RuntimeError(f'ipmitool parsing error ({output_lines[n]})')

                    # Read the 'Lower non-critical' line.
                    elif s.has_threshold and 'Lower non-critical' in output_lines[n]:
                        m = re.match(r'^\s+Lower non-critical\s+:\s+(?P<threshold>\S+)\s*$', output_lines[n])
                        if m:
                            try:
                                if s.type_id == IpmiSensor.TYPE_VOLTAGE:
                                    s.lnc = float(m['threshold'])
                                else:
                                    s.lnc = int(float(m['threshold']))
                            except ValueError as e:
                                raise e
                            s.has_lnc = True
                        else:
                            raise RuntimeError(f'ipmitool parsing error ({output_lines[n]})')

                    # Move to the next line.
                    n+=1

                # Add the parsed sensor to the result list.
                result.append(s)

            # Otherwise move to the next line.
            else:
                n+=1

        return result

    def read_zones(self) -> List[IpmiZone]:
        """Read the detailed IPMI sensors information."""

        result: List[IpmiZone]          # Result list of the IPMI zones.

        # Read all IPMI zones.
        result = []
        n = 0
        while True:
            try:
                l = self.get_fan_level(n)
            except (RuntimeError, FileNotFoundError, ValueError) as e:
                raise e
            if l == 0:
                break
            z = IpmiZone()
            z.id = n
            if self.zone_names[n] is not None:
                z.name = self.zone_names[n]
            else:
                z.name = f'Zone {n}'
            z.level = l
            n += 1
            result.append(z)

        return result

    def read_events(self) -> str:
        """Read list of IPMI events.
        """
        r: subprocess.CompletedProcess  # result of the executed process

        # Validate zone parameter
        try:
            r = subprocess.run([self.command, 'sel', 'elist'],
                           check=False, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f'ipmitool error ({r.returncode}): {r.stderr}')
        except (FileNotFoundError, RuntimeError) as e:
            raise e
        return r.stdout

    def read_bmc_info(self) -> str:
        """Read BMC information from `ipmitool bmc info`."""
        r: subprocess.CompletedProcess  # result of the executed process

        try:
            r = subprocess.run([self.command, 'bmc', 'info'],
                               check=False, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f'ipmitool error ({r.returncode}): {r.stderr}')
        except (FileNotFoundError, RuntimeError) as e:
            raise e
        return r.stdout

    def bmc_reset(self, reset_type: str = 'cold') -> None:
        """Reset the BMC.

        Args:
            reset_type (str): reset type ('cold' or 'warm')
        """
        r: subprocess.CompletedProcess  # result of the executed process

        try:
            r = subprocess.run([self.command, 'bmc', 'reset', reset_type],
                               check=False, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f'ipmitool error ({r.returncode}): {r.stderr}')
        except (FileNotFoundError, RuntimeError) as e:
            raise e

    def set_lower_threshold(self, name: str, lower: List[str]) -> None:
        """Set lower threshold values for the specific sensor.
        """
        r: subprocess.CompletedProcess  # result of the executed process
        args: List[str]                 # Command line arguments

        # Validate zone parameter
        try:
            args = [self.command, 'sensor', 'thresh', name, 'lower']
            args += lower
            r = subprocess.run(args, check=False, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f'ipmitool error ({r.returncode}): {r.stderr}')
        except (FileNotFoundError, RuntimeError) as e:
            raise e

    def set_upper_threshold(self, name: str, upper: List[str]) -> None:
        """Set upper threshold values for the specific sensor.
        """
        r: subprocess.CompletedProcess  # result of the executed process
        args: List[str]                 # Command line arguments

        # Validate zone parameter
        try:
            args = [self.command, 'sensor', 'thresh', name, 'upper']
            args += upper
            r = subprocess.run(args, check=False, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f'ipmitool error ({r.returncode}): {r.stderr}')
        except (FileNotFoundError, RuntimeError) as e:
            raise e


# End.