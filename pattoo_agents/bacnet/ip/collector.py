#!/usr/bin/env python3
"""Pattoo library for collecting BACnetIP data."""

# Standard libraries
import socket

# PIP libraries
from BAC0.core.io.IOExceptions import (
    UnknownObjectError, NoResponseFromController)

# Pattoo libraries
from pattoo_agents.bacnet.ip import configuration
from pattoo_shared import agent
from pattoo_shared import data
from pattoo_shared import log
from pattoo_shared.constants import DATA_FLOAT, DATA_STRING
from pattoo_shared.variables import (
    DataPoint, DataPointMeta, DeviceDataPoints, AgentPolledData, DeviceGateway)
from .constants import PATTOO_AGENT_BACNETIPD


def poll(bacnet):
    """Get BACnetIP agent data.

    Performance data from BACnetIP enabled devices.

    Args:
        None

    Returns:
        agentdata: AgentPolledData object for all data gathered by the agent

    """
    # Initialize key variables.
    config = configuration.ConfigBACnetIP()
    polling_interval = config.polling_interval()

    # Initialize AgentPolledData
    agent_program = PATTOO_AGENT_BACNETIPD
    agent_hostname = socket.getfqdn()
    agent_id = agent.get_agent_id(agent_program, agent_hostname)
    agentdata = AgentPolledData(
        agent_id, agent_program, agent_hostname, polling_interval)
    gateway = DeviceGateway(agent_hostname)

    # Poll oids for all devices and update the DeviceDataPoints
    poller = _PollBACnetIP(bacnet)
    ddv_list = poller.data()
    gateway.add(ddv_list)
    agentdata.add(gateway)

    # Return data
    return agentdata


class _PollBACnetIP(object):
    """Poll BACnetIP devices."""

    def __init__(self, bacnet):
        """Initialize the class.

        Args:
            bacnet: BAC0 object

        Returns:
            None

        """
        # Initialize key variables.
        self._bacnet = bacnet

        config = configuration.ConfigBACnetIP()
        self._ip_polltargets = {}

        # Get SNMP OIDs to be polled (Along with authorizations and ip_devices)
        device_poll_targets = config.device_polling_targets()

        # Create a dict of oid lists keyed by ip_device
        for dpt in device_poll_targets:
            # Ignore invalid data
            if dpt.valid is False:
                continue

            # Process
            next_device = dpt.device
            if next_device in self._ip_polltargets:
                self._ip_polltargets[next_device].extend(dpt.data)
            else:
                self._ip_polltargets[next_device] = dpt.data

    def data(self):
        """Get agent data.

        Update the DeviceDataPoints with DataPoints

        Args:
            None

        Returns:
            ddv_list: List of type DeviceDataPoints

        """
        # Initialize key variables
        arguments = []
        ddv_list = []

        # Poll all devices in sequence
        for ip_device, dpts in sorted(self._ip_polltargets.items()):
            arguments.append((ip_device, dpts))

        for ip_device, dpts in arguments:
            result = self._serial_poller(ip_device, dpts)
            if result.valid is True:
                ddv_list.append(result)

        # Return
        return ddv_list

    def _serial_poller(self, ip_device, polltargets):
        """Poll each spoke in parallel.

        Args:
            ip_device: Device to poll
            polltargets: List of PollingTarget objects to poll
            bacnet: BAC0 connect object

        Returns:
            ddv: DeviceDataPoints for the SNMPVariable device

        """
        # Intialize data gathering
        ddv = DeviceDataPoints(ip_device)
        object2poll = 'analogValue'

        # Get list of type DataPoint
        datapoints = []
        for polltarget in polltargets:
            # Get polling results
            poller_string = (
                '{} {} {} presentValue'.format(
                    ip_device, object2poll, polltarget.address))

            try:
                value = self._bacnet.read(poller_string)
            except NoResponseFromController:
                log_message = (
                    'No BACnet response from {}. Timeout.'.format(ip_device))
                log.log2info(51004, log_message)
                continue
            except UnknownObjectError:
                log_message = ('''\
Unknown BACnet object {} requested from device {}.\
'''.format(object2poll, ip_device))
                log.log2info(51005, log_message)
                continue
            except Exception as reason:
                log_message = ('BACnet error polling {}. Reason: {}'.format(
                    ip_device, str(reason)))
                log.log2info(51006, log_message)
                continue
            except:
                log_message = (
                    'Unknown BACnet error polling {}.'.format(ip_device))
                log.log2info(51007, log_message)
                continue

            # Do multiplication
            if data.is_numeric(value) is True:
                value = float(value) * polltarget.multiplier
                data_type = DATA_FLOAT
            else:
                data_type = DATA_STRING

            # Update datapoints
            datapoint = DataPoint(
                'BACnet_analogValue', value, data_type=data_type)
            datapoint.add(DataPointMeta('point', polltarget.address))
            datapoint.add(DataPointMeta('device', ip_device))
            datapoints.append(datapoint)

        # Return
        ddv.add(datapoints)
        return ddv
