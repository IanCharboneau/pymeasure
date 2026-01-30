


from distro import name
from pymeasure.adapters import adapter
from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import truncated_range, strict_discrete_set, strict_range

class Agilent5230A(Instrument):
    """ represents the Agilent 5230A Network Analyzer"""

    def __init__(self, adapter, name="Agilent 8257D RF Signal Generator", **kwargs):
        super().__init__(
            adapter, name, **kwargs
    )

    start_frequency = Instrument.control(
        "SENS:FREQ:STAR?", "SENS:FREQ:STAR %g",
        """ A floating point property that controls the start frequency
        of the frequency sweep in Hz. """,
        validator=strict_range,
        values=[10e6, 20e9]
    )
    stop_frequency = Instrument.control(
        "SENS:FREQ:STOP?", "SENS:FREQ:STOP %g",
        """ A floating point property that controls the stop frequency
        of the frequency sweep in Hz. """,
        validator=strict_range,
        values=[10e6, 20e9]
    )
    center_frequency = Instrument.control(
        "SENS:FREQ:CENT?", "SENS:FREQ:CENT %g",
        """ A floating point property that controls the center frequency
        of the frequency sweep in Hz. """,
        validator=strict_range,
        values=[10e6, 20e9]
    )
