from src.instrument import Instrument

class Composition:
    """
    Represents a "composition" of instruments, like a piano, xylophone, etc.

    Objects are represented with the format `<object_prefix>_<note_number>`, for example, a piano key might be named `Key_25`
    """
    def __init__(
        self,
        midi_file: str,
        object_prefix: str,
        object_property: str,
        initial_position: float,
        pullback_position: float,
        overshoot_amount: float = 0,
    ):
        self.instruments: list[Instrument] = []

        for i in range(0, 128):
            instrument = Instrument(midi_file, f"{object_prefix}_{i}", object_property, initial_position, pullback_position, overshoot_amount=overshoot_amount, note=i)
            self.instruments.append(instrument)

    def generate_keyframes(self):
        for instrument in self.instruments:
            instrument.generate_keyframes()
