import logging
from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import (strict_discrete_set,
                                              strict_discrete_range,
                                              truncated_range)

class SMT06(Instrument):
    """ Represents a Rohde&Schwarz SMT06 power supply. """

    def __init__(self, adapter, **kwargs):
        kwargs.setdefault("name", "Rohde&Schwarz SMT06")
        super().__init__(
            adapter,
            **kwargs
        )

    # System Setting Commands -------------------------------------------------

    frequency = Instrument.control(
        "FREQ?", "FREQ %s",
        "Control output frequency in Hz. Increment 0.1 Hz.",
        validator=strict_discrete_range,
        values=[0.005, 1000000],
    )

    level = Instrument.control(
        ":POW?", ":POW %s",
        "Control output level in dBm. Increment 0.01 dB.",
        validator=strict_discrete_range,
        values=[-120, 20],
    )

    output = Instrument.control(
        "OUTP?", "OUTP %s",
        "Control output state.",
        validator=strict_discrete_set,
        values=["ON", "OFF"],
    )