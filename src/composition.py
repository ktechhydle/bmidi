import bpy
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
        start_range: int = 0,
        end_range: int = 127,
        overshoot_amount: float = 0,
        affected_object: tuple[str, str, float] | None = None,
        channel: int | None = None,
    ):
        self.instruments: list[Instrument] = []

        for i in range(start_range, end_range):
            object_name = f"{object_prefix}_{i}"

            instrument = Instrument(
                midi_file,
                object_name,
                object_property,
                initial_position,
                pullback_position,
                overshoot_amount=overshoot_amount,
                note=i,
                channel=channel,
                affected_object=(f"{affected_object[0]}_{i}", affected_object[1], affected_object[2]) if affected_object is not None else None
            )
            self.instruments.append(instrument)

    def generate_keyframes(self):
        for instrument in self.instruments:
            instrument.generate_keyframes()
