#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2023 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import re
from pymeasure.instruments import Instrument
import pyvisa
from time import sleep, time

import logging

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class FP4036(Instrument):
    """Represents the Amplifier Research FP4036 isotropic field probe
    and provides a high-level for interacting with the instrument.
    """

    autorange = True

    def __init__(
        self, adapter, name="Amplifier Research Isotropic Field Probe", **kwargs
    ):
        kwargs.setdefault("read_termination", "\r")
        kwargs.setdefault("write_termination", "\r")
        kwargs.setdefault("baud_rate", 9600)
        kwargs.setdefault("data_bits", 7)
        kwargs.setdefault("parity", pyvisa.constants.Parity.odd)
        kwargs.setdefault("stop_bits", pyvisa.constants.StopBits.one)
        kwargs.setdefault("timeout", 1000)

        super().__init__(adapter, name, includeSCPI=False, **kwargs)
        # DTR or RTS must be set to 0 to enable communication, activates the fiber optic modem
        self.adapter.connection.set_visa_attribute(
            pyvisa.constants.VI_ATTR_ASRL_DTR_STATE, 0
        )

    battery_voltage = Instrument.measurement(
        "B", """ Reads the battery voltage in Volts. """
    )

    # get data
    # D1 short form data
    # D2 long form data

    # range
    # R1 0.1 to 1.0 V/m
    # R2 1.0 to 10.0 V/m
    # R3 10.0 to 100.0 V/m
    # R4 100.0 to 1000.0 V/m
    # RN next range
    range = Instrument.control(
        "R%g",
        'R""',
        """ set the range  10.0 V/m, 30.0 V/m,  100.0 V/m, or 300.0 V/m. """,
        map_values=True,
        values={1: 1, 2: 2, 3: 3, 4: 4, "10.0": 1, "30.0": 2, "100.0": 3, "300.0": 4},
        check_set_errors=True,
    )

    # sleep timese
    # S0 disable sleep
    # Sx sleep after x seconds, can be worken up by sending any command, including S0, doesn;t respond to wake up command
    sleep_timer = Instrument.setting(
        "S%g",
        """ set the sleep timer to x seconds, or disable sleep. """,
        check_set_errors=True,
    )

    temperature = Instrument.measurement(
        "TC", """ Reads the temperature in degrees C. """, check_get_errors=True
    )

    temperature_farinheight = Instrument.measurement(
        "TF", """ Reads the temperature in degrees F. """, check_get_errors=True
    )

    # set units
    # U1 V/m
    # U2 mW/cm^2
    # U3 W/m^2
    # UN next unit

    unit = Instrument.measurement(
        "U%g",
        """ set the unit to V/m, mW/cm^2, or W/m^2. """,
        map_values=True,
        values={
            1: 1,
            2: 2,
            3: 3,
            "V/m": 1,
            "mW/cm^2": 2,
            "(V/m)^2": 3,
            "v/m": 1,
            "mw/cm^2": 2,
            "(v/m)^2": 3,
        },
    )
    axis = (
        Instrument.control(
            "A%g",
            "D2",
            """ Enable or disable the X, Y, and Z axis. """,
            get_process=self.process_axis,
            set_process=self.process_axis,
        ),
    )

    def get_data(self):
        result = self.ask("D2")
        result = self.check_errors_process(result)
        value = result[0:5]
        unit = {" V ": "V/m", "mW2": "mW/cm^2", " V2": "(V/m)^2"}[result[5:8]]
        recorder = result[8:11]
        overrange = True if result[11] == "O" else False
        battery = {"N": "Safe", "W": "Low", "F": "Fail"}[result[12]]
        axis = (
            ("X" if result[13] == "E" else "")
            + ("Y" if result[14] == "E" else "")
            + ("Z" if result[15] == "E" else "")
        )
        # return value, unit, recorder, overrange, battery, axis
        return {
            "value": value,
            "unit": unit,
            "recorder": recorder,
            "overrange": overrange,
            "battery": battery,
            "axis": axis,
        }

    def select_axis(self, axis):
        x = bool(re.search("x", axis, re.IGNORECASE))
        y = bool(re.search("y", axis, re.IGNORECASE))
        z = bool(re.search("z", axis, re.IGNORECASE))
        self.write(
            "A" + ("E" if x else "D") + ("E" if y else "D") + ("E" if z else "D")
        )

    def get_axis(self):
        axis = self.getdata()["axis"]
        return axis

    def process_axis(self, axis):
        if len(axis) != 3:
            if len(axis) == 16:
                axis = (
                    ("X" if axis[13] == "E" else "")
                    + ("Y" if axis[14] == "E" else "")
                    + ("Z" if axis[15] == "E" else "")
                )
                return axis
            else:
                raise ValueError("Axis must be a string of length 3")
        else:
            x = bool(re.search("x", axis, re.IGNORECASE))
            y = bool(re.search("y", axis, re.IGNORECASE))
            z = bool(re.search("z", axis, re.IGNORECASE))

            return ("E" if x else "D") + ("E" if y else "D") + ("E" if z else "D")

    def get_x(self):
        """Reads the x-axis value in the current unit."""
        self.axis = "X"
        result, _ = self.get_data()["value"]
        return result

    def get_y(self):
        """Reads the y-axis value in the current unit."""
        self.axis = "Y"
        result, _ = self.get_data()["value"]
        return result

    def get_z(self):
        """Reads the z-axis value in the current unit."""
        self.axis = "Z"
        result = self.get_data()["value"]
        return result

    def get_field(self):
        """Reads the field value in the current unit."""
        self.axis = "XYZ"
        result = self.get_data()["value"]
        return result

    def get_max(self):
        """Reads the maximum value in the current unit."""
        x = self.get_x()
        y = self.get_y()
        z = self.get_z()
        result = max(x, y, z)

        return result

    def get_average(self):
        """Reads the average value in the current unit."""
        x = self.get_x()
        y = self.get_y()
        z = self.get_z()
        result = (x + y + z) / 3

        return result

    def zero(self):
        """Zero the probe."""
        self.write("Z")

    def wakeup(self):
        """Wake up the probe."""
        self.write("\0")

    def check_set_errors(self):
        """Handle returns from set commands."""
        result = self.read()
        if result == ":E01":
            log.error("comunication error")
        elif result == ":E02":
            log.error("Buffer overflow")
        elif result == ":E03":
            log.error("Invalid command")
        elif result == ":E04":
            log.error("Invalid parameter")
        elif result == ":E05":
            log.error("Hardware error")
        elif result == ":E06":
            log.error("Parity error")
        else:
            log.error(f"probe:{result}")

    def check_errors_process(self, reply):
        """Check for errors in the reply. and return the reply without the command echo"""
        if reply == ":E01":
            log.error("comunication error")
        elif reply == ":E02":
            log.error("Buffer overflow")
        elif reply == ":E03":
            log.error("Invalid command")
        elif reply == ":E04":
            log.error("Invalid parameter")
        elif reply == ":E05":
            log.error("Hardware error")
        elif reply == ":E06":
            log.error("Parity error")
        elif reply == "":
            log.error("No reply")
        else:
            return reply[2:]

        return reply[1:]
