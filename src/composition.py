import bpy
from src.instrument import HammerInstrument, LightInstrument, MovementInstrument

class Composition:
    def __init__(
        self,
        midi_file: str,
        object_prefix: str,
        object_property: str,
        start_range: int = 0,
        end_range: int = 127,
        channel: int | None = None,
    ):
        pass

    def generate_keyframes(self) -> None:
        pass

class HammerComposition(Composition):
    """
    Represents a composition of hammer instruments, like a piano, xylophone, etc.

    Objects are represented with the format `<object_prefix><note_number>`, for example, a piano key might be named `Key25`
    """
    def __init__(
        self,
        midi_file: str,
        object_prefix: str,
        object_property: str,
        pullback_amount: float,
        notes: list[int],
        overshoot_amount: float = 0,
        channel: int | None = None,
    ):
        self.instruments: list[HammerInstrument] = []

        for i in notes:
            object_name = f"{object_prefix}{i}"

            try:
                bpy.data.objects[object_name]
            except:
                continue

            instrument = HammerInstrument(
                midi_file,
                object_name,
                object_property,
                pullback_amount,
                overshoot_amount=overshoot_amount,
                note=i,
                channel=channel,
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
        final_amount: float,
        notes: list[int],
        channel: int | None = None,
    ):
        self.instruments: list[MovementInstrument] = []

        for i in notes:
            object_name = f"{object_prefix}{i}"

            try:
                bpy.data.objects[object_name]
            except:
                continue

            instrument = MovementInstrument(
                midi_file,
                object_name,
                object_property,
                final_amount,
                note=i,
                channel=channel,
            )
            self.instruments.append(instrument)

    def generate_keyframes(self):
        for instrument in self.instruments:
            instrument.generate_keyframes()

class LightComposition(Composition):
    """
    Represents a composition of light instruments, like studio effects, splashes, etc.

    Objects are represented with the format `<object_prefix><note_number>`, for example, a piano key might be named `Key25`
    """
    def __init__(
        self,
        midi_file: str,
        object_prefix: str,
        light_property: str,
        initial_amount: float,
        final_amount: float,
        notes: list[int],
        mode: str = "light",
        fade_effect: bool = False,
        channel: int | None = None,
    ):
        self.instruments: list[LightInstrument] = []

        for i in notes:
            object_name = f"{object_prefix}{i}"

            try:
                bpy.data.objects[object_name]
            except:
                continue

            instrument = LightInstrument(
                midi_file,
                object_name,
                light_property,
                initial_amount,
                final_amount,
                mode=mode,
                fade_effect=fade_effect,
                note=i,
                channel=channel,
            )
            self.instruments.append(instrument)

    def generate_keyframes(self):
        for instrument in self.instruments:
            instrument.generate_keyframes()
