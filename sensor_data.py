#!/usr/bin/env python3
# Copyright (C) 2018  Simon Redman <simon@ergotech.com>

# This file is part of Linux Temperature Monitor.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software. If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime
import re
import subprocess
import sys
from typing import Dict, List

class Temperature:
    """
    Sensors report the current temperature, as well as some thresholds
    """

    def __init__(self, reading: List[str]):
        """
        :param reading:
        """
        self.temperature = None
        self.parse_reading(reading)

    def parse_reading(self, reading: List[str]) -> None:
        for line in reading:
            # Match some string, which ends with an underscore and is thrown away, then:
            #   Match a string. This is the name of the line from `sensors`
            #   Match a decimal number. This is the reading's value
            name, value, *unused = re.match(r'.*\d_(.*): (\d+\.\d+)', line).groups()

            value = float(value)

            if name == 'input':
                self.temperature = value
            elif name == 'max':
                self.max = value
            elif name == 'crit':
                self.crit = value
            elif name == 'crit_alarm':
                self.crit_alarm = value
            else:
                # Something unexpected
                raise ValueError('Unexpected sensor reading')

    def __repr__(self):
        return str(self.temperature)

class SensorData:
    """
    Contain all temperatures associated with a temperature reading
    """
    cpus: Dict[str, float]   # Map CPU names to current temperature
    others: Dict[str, float] # Map other hardware components to their temperature

    raw_data: str # Unprocessed sensor data

    timestamp: datetime

    def __init__(self):
        self.timestamp = datetime.today()
        self.cpus = {}
        self.others = {}

        self.raw_data = SensorData.get_raw_data()
        self.parse_raw_data()

    def parse_raw_data(self) -> None:
        """
        FSM to parse the read data
        """
        lines = self.raw_data.splitlines()
        index = 0

        while index < len(lines):
            line = lines[index]
            index += 1
            if not line.startswith('Adapter'):
                continue

            next_line = lines[index + 1]
            while not len(next_line) == 0: # Blank line indicates the end of an adapter
                # Start parsing:
                # Get the name of the thing for which we are reading the temperature
                name = lines[index]

                # Collect all data associated with this device
                reading: List[str] = []
                while True:
                    next_line = lines[index + 1]
                    if not next_line.startswith(' '):
                        break
                    reading.append(next_line)
                    index = index + 1

                if name.startswith('Core'):
                    self.cpus[name] = Temperature(reading)
                else:
                    # This is not sufficient to do anything useful, since most other devices
                    # use the exact same, non-descriptive name
                    self.others[name] = Temperature(reading)
                index += 1

    @staticmethod
    def get_raw_data() -> str:
        output = subprocess.check_output(['sensors', '-u'])
        return output.decode(sys.stdout.encoding)