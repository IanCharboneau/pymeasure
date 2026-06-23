from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import strict_range

class Ha1600A(Instrument):
    """
    Represents the Aim-TTi HA1600A Power and Harmonics Analyzer.
    """
    
    def __init__(self, adapter, name="Aim-TTi HA1600A Power Analyzer", **kwargs):
        super().__init__(
            adapter,
            # read_termination="\r\n",
            # write_termination="\r\n",
            name=name,
            **kwargs
        )

    # Basic SCPI commands for instrument control
    id = Instrument.measurement("*IDN?", "Returns the instrument's identification string")
    voltage_rms = Instrument.measurement("V RMS?", "Reads the supply voltage RMS")
    current_rms = Instrument.measurement("I RMS?", "Reads the load current RMS")
    true_power = Instrument.measurement("WATTS?", "Reads the true power in Watts")
    apparent_power = Instrument.measurement("VA?", "Reads the apparent power")
    power_factor = Instrument.measurement("PF?", "Reads the power factor")
    frequency = Instrument.measurement("FREQ?", "Reads the supply frequency")

    def reset(self):
        """Resets the instrument to default state."""
        self.write("*RST")
        
    def start_measurement(self):
        """Starts a harmonic or flicker measurement sequence."""
        self.write("START")
        
    def stop_measurement(self):
        """Stops the current measurement sequence."""
        self.write("STOP")
