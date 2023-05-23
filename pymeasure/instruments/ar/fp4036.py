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

import math
import re
from pymeasure.instruments import Instrument
import pyvisa
from time import sleep, time

import logging

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def check_get_errors(reply):
    """Check for errors in the reply"""
    if len(reply) == 18 and reply[13] == "O":
        log.error("Overrange")
    if len(reply) == 18 and reply[14] == "W":
        log.warning("Low battery")
    if len(reply) == 18 and reply[15] == "F":
        log.error("Battery failure")

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
    return reply


def process_axis(axis):
    """Checks human readable axis  for correctness and transforms it into the probe readable axis, an
    Checks probe readable axis for errors and transforms it into human readable axis"""
    if len(axis) > 3:
        axis = check_get_errors(axis)
        if len(axis) == 16:
            axis = (
                ("X" if axis[13] == "E" else "")
                + ("Y" if axis[14] == "E" else "")
                + ("Z" if axis[15] == "E" else "")
            )
            # print(axis)
            return axis
        else:
            raise ValueError("Axis must be a string of length 3 or less")
    else:
        x = bool(re.search("x", axis, re.IGNORECASE))
        y = bool(re.search("y", axis, re.IGNORECASE))
        z = bool(re.search("z", axis, re.IGNORECASE))
        # print(("E" if x else "D") + ("E" if y else "D") + ("E" if z else "D"))
        return ("E" if x else "D") + ("E" if y else "D") + ("E" if z else "D")


def process_axis_data(response):
    error, subresponce = response.split("\r", 1)
    error = check_get_errors(error)
    value = proccess_data(subresponce)
    return f"{value['field']}"


def process_axis_data_unit(response):
    error, subresponce = response.split("\r", 1)
    error = check_get_errors(error)
    value = proccess_data(subresponce)
    return f"{value['field']}" + f"{value['unit']} "


def proccess_data(response):
    """calls the check_get_errors, then returns the value without the command echo and processes data when required"""
    value = check_get_errors(response)[2:]
    if len(value) < 8:
        return value
    if len(value) == 8:
        field = value[0:5]
        unit = {" V ": "V/m", "MW2": "mW/cm^2", "KV2": "(V/m)^2"}[value[5:8]]
        return {"field": field, "unit": unit}
    if len(value) == 16:
        field = value[0:5]
        unit = {" V ": "V/m", "MW2": "mW/cm^2", "KV2": "(V/m)^2"}[value[5:8]]

        recorder = value[8:11]
        overrange = True if value[11] == "O" else False
        battery = {"N": "Safe", "W": "Low", "F": "Fail"}[value[12]]
        # axis = process_axis(response)
        axis = (
            ("X" if value[13] == "E" else "")
            + ("Y" if value[14] == "E" else "")
            + ("Z" if value[15] == "E" else "")
        )
        # return value, unit, recorder, overrange, battery, axis
        return {
            "field": float(value),
            "unit": unit,
            "recorder": int(recorder),
            "overrange": overrange,
            "battery": battery,
            "axis": axis,
        }


class FP4036(Instrument):
    """Represents the Amplifier Research FP4036 isotropic field probe
    and provides a high-level for interacting with the instrument.
    """

    autorange = True  # only works for methods not measurements
    # battery_errors = True
    # return_errors = True
    return_units = True  # works for measurements and methods

    def __init__(
        self, adapter, name="Amplifier Research Isotropic Field Probe", **kwargs
    ):
        kwargs.setdefault("read_termination", "\r")
        kwargs.setdefault("write_termination", "\r")
        kwargs.setdefault("baud_rate", 9600)
        kwargs.setdefault("data_bits", 7)
        kwargs.setdefault("parity", pyvisa.constants.Parity.odd)
        kwargs.setdefault("stop_bits", pyvisa.constants.StopBits.one)
        kwargs.setdefault("timeout", 100)

        # set_autorange(autoragne)
        # set_battery_errors(battery_errors)
        # set_return_errors(return_errors)
        # set_return_units(return_units)

        super().__init__(adapter, name, includeSCPI=False, **kwargs)
        # DTR or RTS must be set to 0 to enable communication, activates the fiber optic modem
        self.adapter.connection.set_visa_attribute(
            pyvisa.constants.VI_ATTR_ASRL_DTR_STATE, 0
        )

        sleep(0.5)
        self.wakeup  # wake up the probe
        sleep(0.1)
        self.write("S0")  # disable sleep
        try:  # clear the buffer
            self.read()
            self.read()
        except:
            pass
        self.adapter.connection.timeout = 1000

    battery_voltage = Instrument.measurement(
        "B",
        """ Reads the battery voltage in Volts. """,
        preprocess_reply=check_get_errors,
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
        "R",
        "R%s",
        """ set the range  10.0 V/m, 30.0 V/m,  100.0 V/m, or 300.0 V/m. """,
        map_values=True,
        values={
            "10.0": 1,
            "30.0": 2,
            "100.0": 3,
            "300.0": 4,
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            "n": "N",
            "N": "N",
            "next": "N",
        },
        check_set_errors=True,
        preprocess_reply=check_get_errors,
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
        "TC",
        """ Reads the temperature in degrees C. """,
        preprocess_reply=check_get_errors,
    )

    temperature_fahrenheit = Instrument.measurement(
        "TF",
        """ Reads the temperature in degrees F. """,
        preprocess_reply=check_get_errors,
    )

    # set units
    # U1 V/m
    # U2 mW/cm^2
    # U3 W/m^2
    # UN next unit

    unit = Instrument.control(
        "D2",
        "U%g",
        """ set the unit to V/m, mW/cm^2, or W/m^2. """,
        map_values=False,  # uses asymetric mapping via get_process and set_process
        check_set_errors=True,
        set_process=lambda v: {
            1: 1,
            2: 2,
            3: 3,
            "V/m": 1,
            "mW/cm^2": 3,
            "(V/m)^2": 2,
            "v/m": 1,
            "mw/cm^2": 3,
            "(v/m)^2": 2,
            " V ": 1,
            "MW2": 3,
            "KV2": 2,
        }[v],
        get_process=lambda v: {
            " V ": "V/m",
            "MW2": "mW/cm^2",
            "KV2": "(V/m)^2",
        }[check_get_errors(v)[5:8]],
    )
    axis = Instrument.control(
        "D2",
        "A%s",
        """ cotrol which axis or axes are active. """,
        check_set_errors=True,
        get_process=process_axis,
        set_process=process_axis,
    )

    x = Instrument.measurement(
        "AEDD/rD2",
        """ Reads the x axis value in the current units. """,
        preprocess_reply=process_axis_data,
        dynamic=True,
    )

    y = Instrument.measurement(
        "ADED/rD2",
        """ Reads the y axis value in the current units. """,
        preprocess_reply=process_axis_data,
        dynamic=True,
    )

    z = Instrument.measurement(
        "ADDE/rD2",
        """ Reads the z axis value in the current units. """,
        preprocess_reply=process_axis_data,
        dynamic=True,
    )
    field = Instrument.measurement(
        "AEEE/rD2",
        """ Reads the field strength in the current units. """,
        preprocess_reply=process_axis_data,
        dynamic=True,
    )

    def get_data(self):
        result = self.ask("D2")
        result = check_get_errors(result)
        value = result[0:5]
        unit = {" V ": "V/m", "MW2": "mW/cm^2", "KV2": "(V/m)^2"}[result[5:8]]
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
            "value": float(value),
            "unit": unit,
            "recorder": int(recorder),
            "overrange": overrange,
            "battery": battery,
            "axis": axis,
        }

    def set_axis(self, axis):
        x = bool(re.search("x", axis, re.IGNORECASE))
        y = bool(re.search("y", axis, re.IGNORECASE))
        z = bool(re.search("z", axis, re.IGNORECASE))
        self.write(
            "A" + ("E" if x else "D") + ("E" if y else "D") + ("E" if z else "D")
        )
        self.check_errors()

    def get_axis(self):
        axis = self.getdata()["axis"]
        return axis

    def get_x(self):
        """Reads the x-axis value in the current unit."""
        # old_axis = self.axis
        self.axis = "X"
        # result = self.get_data()["value"]
        result = self.get_data()
        # self.axis = old_axis
        return result["value"] + (result["unit"])

    def get_y(self):
        """Reads the y-axis value in the current unit."""
        # old_axis = self.axis
        self.axis = "Y"
        result = self.get_data()["value"]
        # self.axis = old_axis
        return result

    def get_z(self):
        """Reads the z-axis value in the current unit."""
        # old_axis = self.axis
        self.axis = "Z"
        result = self.get_data()["value"]
        # self.axis = old_axis
        return result

    def get_field(self):
        """Reads the field value in the current unit."""
        # old_axis = self.axis
        self.axis = "XYZ"
        result = self.get_data()["value"]
        # self.axis = old_axis
        return result

    def get_direction(self):
        """Reads the direction of the field in the current unit."""
        x = self.get_x()
        y = self.get_y()
        z = self.get_z()
        result = math.sqrt(x**2 + y**2 + z**2)
        result = (x / result, y / result, z / result)
        return result

    def get_max(self, get_axis=False):
        """Reads the maximum value in the current unit."""
        x = self.get_x()
        y = self.get_y()
        z = self.get_z()
        result = max(x, y, z)
        axis = "X" if x == result else "Y" if y == result else "Z"
        return result if not get_axis else (result, axis)

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

    def shutdown(self):
        """Shutdown the probe."""
        self.write("S300")  # probe will sleep after 5 minutes

    def check_errors(self):
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
            log.info(f"probe:{result}")
        return result

    def set_return_units(self, return_units):
        """set wether the unit is returnturend in the reply of property functions"""
        unitfuncs = ["x", "y", "z", "field", "max", "average"]
        if return_units:
            for func in unitfuncs:
                setattr(self, f"{func}_preprocess_reply", process_axis_data_unit)

        else:
            for func in unitfuncs:
                setattr(self, f"{func}_preprocess_reply", process_axis_data)
