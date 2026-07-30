import logging
from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import (strict_discrete_set,
                                              strict_discrete_range,
                                              strict_range,
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
        validator=strict_range,
        values=[0.005, 6e9],
    )

    level = Instrument.control(
        ":POW?", ":POW %s",
        "Control output level in dBm. Increment 0.01 dB.",
        validator=strict_range,
        values=[-120, 20],
    )

    output = Instrument.control(
        "OUTP?", "OUTP %s",
        "Control output state.",
        validator=strict_discrete_set,
        values=["ON", "OFF"],
    )

    FM1_Dev = Instrument.control(
        "FM1?", "FM1 %s",
        "Control frequency modulation deviation",
        validator=strict_range,
        values=[0, 100e6],
    )

    FM1_Source = Instrument.control(
        "FM1:SOUR ?", "FM1:SOUR %s",
        "Control frequency modulation state.",
        validator=strict_discrete_set,
        values=["INT", "EXT1", "EXT2"],
    )

    FM1_State = Instrument.control(
        "FM1:STAT?", "FM1:STAT %s",
        "Control frequency modulation state.",
        validator=strict_discrete_set,
        values=["ON", "OFF"],
    )

    LF_Gen1 = Instrument.control(
        ":FM1:INT:FREQ?", ":FM1:INT:FREQ %s",
        "Control low frequency generator 1 frequency in Hz. Increment 0.1 Hz.",
        validator=strict_discrete_set,
        values=["0.4kHz", "1kHz", "3kHz", "15kHz"],
    )



    PULM_State = Instrument.control(
        ":PULM:SOUR INT;STAT?", ":PULM:SOUR INT;STAT %s",
        "Control pulse modulation state.",
        validator=strict_discrete_set,
        values=["ON", "OFF"],
    )
    PULM_Source = Instrument.control(
        ":PULM:SOUR?", ":PULM:SOUR %s",
        "Control pulse modulation source.",
        validator=strict_discrete_set,
        values=["INT", "EXT","PULSE-GEN"],
    )
    PULM_Polarity = Instrument.control(
        ":PULM:POL?", ":PULM:POL %s",
        "Control pulse modulation polarity.",
        validator=strict_discrete_set,
        values=["NORM", "INV"],
    )

    PULM_Ext_Imp = Instrument.control(
        ":PULM:EXT:IMP?", ":PULM:EXT:IMP %s",
        "Control pulse modulation external impedance.",
        validator=strict_discrete_set,
        values=["50", "10k"],
    )

    PULM_Period = Instrument.control(
        ":PULS:PER?", ":PULS:PER %s",
        "Control pulse modulation period in seconds. Increment 0.1 s.",
        # validator=strict_range,
        # values=[0.0000000000000000001, 100],
    )

    PULM_Width = Instrument.control(
        ":PULS:WIDT?", ":PULS:WIDT %s",
        "Control pulse modulation width in seconds. Increment 0.1 s.",
        # validator=strict_range,
        # values=[0.0000000000000001, 100],
    )

