#!/usr/bin/env python3
"""Classe to manage SNMP agent configurations."""

# Standard imports
import itertools

# Import project libraries
from pattoo_shared import configuration
from pattoo_shared import data as lib_data
from pattoo_shared.configuration import Config
from pattoo_shared.constants import PATTOO_AGENT_MODBUSTCPD
from pattoo_agents.agents.modbus.variables import (
    InputRegisterVariable, HoldingRegisterVariable, DeviceRegisterVariables)


class ConfigModbusTCP(Config):
    """Class gathers all configuration information."""

    def __init__(self):
        """Initialize the class.

        Args:
            None

        Returns:
            None

        """
        # Instantiate the Config parent
        Config.__init__(self)

    def registervariables(self):
        """Get list of dicts of SNMP information in configuration file.

        Args:
            group: Group name to filter results by

        Returns:
            result: List of RegisterVariable items

        """
        # Initialize key variables
        result = []

        # Get configuration snippet
        key = PATTOO_AGENT_MODBUSTCPD
        sub_key = 'polling_groups'
        groups = configuration.search(
            key, sub_key, self._configuration, die=True)

        # Create Tuple instance to populate
        result = []

        # Create snmp objects
        for group in groups:
            for register in ['input_registers', 'holding_registers']:
                if register in group:
                    result.extend(_create_drv(group, register))
        return result


def _get_unit(data):
    """Get the unit to be polled in the polling_group.

    Args:
        data: Configuration dict for the polling_group

    Returns:
        result: unit value

    """
    # Ignore invalid non-dicts
    if isinstance(data, dict) is False:
        result = 0
        return result

    # Default value
    if 'unit' not in data:
        result = 0
        return result

    # Non integer values got to default
    unit = data['unit']
    valid = False not in [
        lib_data.is_numeric(unit),
        isinstance(unit, str) is True,
        unit is not False,
        unit is not True,
        unit is not None
        ]
    if valid is False:
        result = 0
        return result

    # Convert float values to integer values
    if isinstance(unit, float) is True:
        result = int(unit)
    else:
        result = unit

    # Return
    return result


def _create_drv(data, register_type):
    """Create a list of DeviceRegisterVariables for polling.

    Args:
        data: Configuration dict

    Returns:
        result: list of DeviceRegisterVariables

    """
    # Initialize key variables
    result = []

    # Only return valid value
    if isinstance(data, dict) is True:
        # Screen data for keys and correct type
        if (register_type not in 'input_registers') and (
                register_type not in 'holding_registers'):
            return []
        if isinstance(data['ip_devices'], list) is False and isinstance(
                data[register_type], list) is False:
            return []

        # Get the modbus unit value
        unit = _get_unit(data)

        # Process
        for ip_device in data['ip_devices']:
            variables = []
            register_counts = _create_register_counts(data[register_type])
            for register, count in register_counts:
                if register_type == 'holding_registers':
                    variables.append(HoldingRegisterVariable(
                        register=register, count=count, unit=unit))
                else:
                    variables.append(InputRegisterVariable(
                        register=register, count=count, unit=unit))
            drv = DeviceRegisterVariables(ip_device)
            drv.add(variables)
            result.append(drv)

    # Return
    return result


def _create_register_counts(listing):
    """Convert a list of integers into ranges.

    Args:
        listing: List of integers to group

    Returns:
        result: List of tuples [(start, length of range), ...]

    """
    # Process data
    result = []
    ranges = list(_ranger(listing))
    for (start, stop) in ranges:
        result.append((start, stop - start + 1))
    result.sort()
    return result


def _ranger(listing):
    """Convert a list of integers into ranges.

    Args:
        listing: List of integers to group

    Yields:
        List of tuples [(start, stop of range), ...]

    """
    # Remove duplicates
    listing = list(set(listing))

    # Sort data beforehand to ensure grouping works.
    listing.sort()

    # Group data.
    for _, second in itertools.groupby(
            enumerate(listing), lambda pair: pair[1] - pair[0]):
        second = list(second)
        yield second[0][1], second[-1][1]
