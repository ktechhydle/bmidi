import bpy
from src.instrument import HammerInstrument, MovementInstrument

class Composition:
    def __init__(
        self,
        midi_file: str,
        object_prefix: str,
        object_property: str,
        start_range: int = 0,
        end_range: int = 127,
        channel: int | None = None,
        track: str | None = None,
    ):
        pass

    def generate_keyframes(self) -> None:
        pass

class HammerComposition(Composition):
    """
    Represents a composition of hammer instruments, like a piano, xylophone, etc.

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
        track: str | None = None,
    ):
        self.instruments: list[HammerInstrument] = []

        for i in range(start_range, end_range):
            object_name = f"{object_prefix}_{i}"

            instrument = HammerInstrument(
                midi_file,
                object_name,
                object_property,
                initial_position,
                pullback_position,
                overshoot_amount=overshoot_amount,
                note=i,
                channel=channel,
                track=track,
                affected_object=(f"{affected_object[0]}_{i}", affected_object[1], affected_object[2]) if affected_object is not None else None
            )
            self.instruments.append(instrument)

    def generate_keyframes(self):
        for instrument in self.instruments:
            instrument.generate_keyframes()

class MovementComposition(Composition):
    """
    Represents a composition of movement instruments, like pipe organs, brass, etc.

    Objects are represented with the format `<object_prefix>_<note_number>`, for example, a piano key might be named `Key_25`
    """
    def __init__(
        self,
        midi_file: str,
        object_prefix: str,
        object_property: str,
        initial_position: float,
        final_position: float,
        start_range: int = 0,
        end_range: int = 127,
        channel: int | None = None,
        track: str | None = None,
    ):
        self.instruments: list[MovementInstrument] = []

        for i in range(start_range, end_range):
            object_name = f"{object_prefix}_{i}"

            instrument = MovementInstrument(
                midi_file,
                object_name,
                object_property,
                initial_position,
                final_position,
                note=i,
                channel=channel,
                track=track,
            )
            self.instruments.append(instrument)

    def generate_keyframes(self):
        for instrument in self.instruments:
            instrument.generate_keyframes()
