#!/usr/bin/env python3
# Monitor temperatures with hooks to perform an action at certain cutoffs
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

import argparse
import subprocess
import time

from sensor_data import SensorData, Temperature


def generate_notification(component: str, temperature: float, timeout: int = 0) -> None:
    """
    Generate a notification, reporting the noted temperature and component
    :param component: The hardware component about which we want to report the temperature
    :param temperature: The temperature of the component being reported
    :param timeout: Miliseconds after which the notification should be cleared -- 0 means never
    """
    NOTIFICATION_TEMPLATE = "{component} is overheating at {temperature}C"
    notification_body = NOTIFICATION_TEMPLATE.format(component=component, temperature=temperature)

    subprocess.check_output(['notify-send', 'CPU Overheating', notification_body, '-t', str(timeout)])


def read_sensors() -> (float, str):
    """
    Perform a sensor reading and return the temperature of the hottest CPU and its name
    :return: Hottest CPU temperature
    """
    reading = SensorData()
    max_cpu_temperature: float = float('-inf')
    hottest_cpu: str = ''
    for cpu in reading.cpus.keys():
        cpu_temp: Temperature = reading.cpus[cpu]
        if cpu_temp.temperature > max_cpu_temperature:
            max_cpu_temperature = cpu_temp.temperature
            hottest_cpu = cpu
    return max_cpu_temperature, hottest_cpu


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Present notifications about CPU temperature to the logged-in user")
    parser.add_argument('--critical', type=int, action='store', default=95,
                        help="Cutoff for critical temperature")
    parser.add_argument('--delay', type=int, action='store', default=60,
                        help="Number of seconds between temperature readings")
    parser.add_argument('--keep_alerting', type=bool, action='store', default=False,
                        help="Keep generating alerts, even if nothing has changed")
    parser.add_argument('--ignore_critical', action='store_true', default=False,
                        help="Generate alerts even if the temperature is non-critical")
    parser.add_argument('--oneshot', action='store_true', default=False,
                        help="Run once, then stop")

    args = parser.parse_args()

    while(True):
        max_temp, hot_cpu = read_sensors()

        if (max_temp > args.critical or args.ignore_critical):
            generate_notification(hot_cpu, max_temp, timeout=args.delay)
        time.sleep(args.delay)

        if args.oneshot: break