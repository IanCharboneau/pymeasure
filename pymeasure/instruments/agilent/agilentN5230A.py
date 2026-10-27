


from pymeasure.instruments import Instrument, SCPIUnknownMixin
from pymeasure.instruments.validators import (
    strict_discrete_range,
    strict_range,
    strict_discrete_set,
    truncated_discrete_set,
    truncated_range,
    # truncated_discrete_range,
    joined_validators,

)
from pymeasure.instruments.channel import Channel

from io import StringIO
import numpy as np
import pandas as pd


class TraceChannel(Channel):
    """ a channel for adressing traces on the Agilent N5230A Network analyser"""

    start_frequency = Instrument.control(
    "SENS{ch}:FREQ:START?",
    "SENS{ch}:FREQ:START %g",
    """ A floating point property that controls the start frequency of the spectrum analyzer. Unit Hz.""",
    validator=truncated_range,
    values=[10e6, 20e9]
    )

    stop_frequency = Instrument.control(
        "SENS{ch}:FREQ:STOP?",
        "SENS{ch}:FREQ:STOP %g",
        """ A floating point property that controls the stop frequency of the spectrum analyzer. Unit Hz.""",
        validator=truncated_range,
        values=[10e6, 20e9]
    )

    center_frequency = Instrument.control(
        "SENS{ch}:FREQ:CENT?",
        "SENS{ch}:FREQ:CENT %g",
        """ A floating point property that controls the center frequency of the spectrum analyzer. Unit Hz.""",
        validator=truncated_range,
        values=[10e6, 20e9]
    )

    trigger = Instrument.control(
        "SENS{ch}:SWE:MODE?",
        "SENS{ch}:SWE:MODE %s",
        """ A string property that controls the trigger mode of the spectrum analyzer.
        HOLD - channel will not trigger
        CONT - continuous trigger mode
        GRO - channel accepts the number of trigger specified with the last GRO command
        SING - single trigger mode """,
        validator=strict_discrete_set,
        values=["HOLD", "CONT", "GRO", "SING"]
    )

    points = Instrument.control(
        "SENS{ch}:SWE:POIN?",
        "SENS{ch}:SWE:POIN %d",
        """ An integer property that controls the number of points in the sweep of the spectrum analyzer.""",
        validator=truncated_discrete_set,
        values=[1, 20001]
    )

    sweep_time = Instrument.control(
        "SENS{ch}:SWE:TIME?",
        "SENS{ch}:SWE:TIME %g",
        """ A floating point property that controls the sweep time of the spectrum analyzer. Unit seconds.""",
        validator=joined_validators(truncated_range,strict_discrete_set),
        values=[["MIN","MAX"],[0, 86400]]
    )

    sweep_time_auto = Instrument.control(
        "SENS{ch}:SWE:TIME:AUTO?",
        "SENS{ch}:SWE:TIME:AUTO %s",
        """ A string property that controls the automatic sweep time mode of the spectrum analyzer.
        ON - automatic sweep time enabled
        OFF - automatic sweep time disabled """,
        validator=strict_discrete_set,
        values=["ON", "OFF"]
    )

    sweep_type = Instrument.control(
        "SENS{ch}:SWE:TYPE?",
        "SENS{ch}:SWE:TYPE %s",
        """ A string property that controls the sweep type of the spectrum analyzer.
        LIN - linear sweep
        LOG - logarithmic sweep """,
        validator=strict_discrete_set,
        values=["LIN", "LOG","POW", "CW", "SEGM"]
    )

    trace = Instrument.measurement(
        "TRAC{ch}:DATA? FDATA",
        """ A floating point property that retrieves the trace data in the frequency domain of the spectrum analyzer. Unit Hz.""",
    )

    span = Instrument.control(
        "SENS{ch}:FREQ:SPAN?",
        "SENS{ch}:FREQ:SPAN %g",
        """ A floating point property that controls the frequency span of the spectrum analyzer. Unit Hz.""",
        validator=truncated_range,
        values=[0, 20e9]
    )

    bandwidth = Instrument.control(
        "SENS{ch}:BAND?",
        "SENS{ch}:BAND %g",
        """ A floating point property that controls the frequency bandwidth of the spectrum analyzer. Unit Hz.""",
        # this needs to be updated to the correct values -GM-
        validator=truncated_range,
        values=[0, 20e9]
    )

    reduce_if_low_freq_bw = Instrument.control(
        "SENS{ch}:BAND:TRAC?",
        "SENS{ch}:BAND:TRAC %s",
        """ A string property that controls whether the bandwidth is reduced at low frequencies.
        ON - reduce bandwidth at low frequencies
        OFF - do not reduce bandwidth at low frequencies """,
        validator=strict_discrete_set,
        values=["ON", "OFF"]
    )







    

class AgilentN5230A(SCPIUnknownMixin, Instrument):
    """ Represents the AgilentN5230A Network Analyzer
    and provides a high-level interface for taking scans of
    high-frequency spectrums
    """

    def __init__(self, adapter, name="Agilent N5230A Spectrum Analyzer", **kwargs):
        super().__init__(
            adapter,
            name,
            read_termination="\n",
            write_termination="\n",
            timeout=5000, 
            **kwargs
        )

    trace1 = Instrument.ChannelCreator(TraceChannel, 1)
    trace2 = Instrument.ChannelCreator(TraceChannel, 2)
    trace3 = Instrument.ChannelCreator(TraceChannel, 3)
    trace4 = Instrument.ChannelCreator(TraceChannel, 4)

    def trace(self, trace=1):
        rdata = self.trace(trace).trace
        rdata = np.fromstring(rdata, sep=',')
        return pd.DataFrame(rdata, columns=["Frequency (Hz)", "Peak (dB)"])

    def output_power(self, trace=1, mode="OFF"):
        self.write(f"SOUR{trace}:POW:COUP {mode} ")
    

    def output_power_lvl(self, trace = 1 , level = -5, port = 1):
        self.write(f"SOUR{trace}:POW{port} {level}")