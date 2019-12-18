#!/usr/bin/env python3
"""Test the class_point module."""

import sys
import unittest
import os

# Try to create a working PYTHONPATH
EXEC_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(
    os.path.abspath(os.path.join(
            os.path.abspath(os.path.join(
                os.path.abspath(os.path.join(
                        EXEC_DIR,
                        os.pardir)), os.pardir)), os.pardir)), os.pardir))

if EXEC_DIR.endswith(
        '/pattoo-agents/tests/test_pattoo_agents/bacnet/ip') is True:
    # We need to prepend the path in case PattooShared has been installed
    # elsewhere on the system using PIP. This could corrupt expected results
    sys.path.insert(0, ROOT_DIR)
else:
    print('''\
This script is not installed in the \
"pattoo-agents/tests/test_pattoo_agents/bacnet/ip" directory. Please fix.''')
    sys.exit(2)

# Pattoo imports
from pattoo_shared.variables import PollingPoint, IPTargetPollingPoints
from pattoo_agents.bacnet.ip import configuration
from tests.libraries.configuration import UnittestConfig


class TestConfigBACnetIP(unittest.TestCase):
    """Checks all ConfigBACnetIP methods."""

    ##########################################################################
    # Initialize variable class
    ##########################################################################
    config = configuration.ConfigBACnetIP()

    def test___init__(self):
        """Testing function __init__."""
        pass

    def test_agent_ip_address(self):
        """Testing method / function agent_ip_address."""
        # Initialize variables
        result = self.config.agent_ip_address()
        self.assertEqual(result, '127.0.0.50')

    def test_target_polling_points(self):
        """Testing function pointvariables."""
        # Initialize key variables.
        result = self.config.target_polling_points()
        points = [123, 345]

        # Test
        self.assertEqual(isinstance(result, list), True)
        self.assertEqual(len(result), 1)

        # Test each dpt
        item = result[0]
        self.assertEqual(isinstance(item, IPTargetPollingPoints), True)
        self.assertEqual(item.target, '127.0.0.60')
        for index, value in enumerate(item.data):
            self.assertEqual(isinstance(value, PollingPoint), True)
            self.assertEqual(value.address, points[index])


if __name__ == '__main__':
    # Make sure the environment is OK to run unittests
    UnittestConfig().create()

    # Do the unit test
    unittest.main()
