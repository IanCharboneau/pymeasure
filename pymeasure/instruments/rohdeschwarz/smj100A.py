import logging
from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import (strict_discrete_set,
                                              strict_discrete_range,
                                              strict_range,
                                              truncated_range)

class SMJ100A(Instrument):
    """ Represents a Rohde&Schwarz SMJ100A power supply. """

    def __init__(self, adapter, **kwargs):
        kwargs.setdefault("name", "Rohde&Schwarz SMJ100A")
        super().__init__(
            adapter,
            **kwargs
        )

    frequency = Instrument.control(
        ":FREQ?",
        ":FREQ %g",
        """ A floating point property that represents the output frequency
        in Hz. This property can be set.
        """,
    )

    level = Instrument.control(
        ":POW?",
        ":POW %g",
        """ A floating point property that represents the output power
        in dBm. This property can be set.
        """,
    )

    output = Instrument.control(
        ":OUTP:STAT?",
        ":OUTP:STAT %s",
        """ A string property that represents the output state
        (ON or OFF). This property can be set.
        """,
        validator=strict_discrete_set,
        values=["ON", "OFF", 0, 1],
    )