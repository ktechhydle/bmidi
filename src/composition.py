import bpy
from src.instrument import HammerInstrument, LightInstrument, MovementInstrument, RoboticInstrument

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

class RoboticComposition(Composition):
    """
    Represents a robotic arm that will move to hit specified targets (notes)

    Targets are represented with the format `<object_prefix><note_number>`, for example, a drum head might be named `Snare25`
    """
    def __init__(
        self,
        midi_file: str,
        control_object: str,
        target_object_prefix: str,
        pullback_amount: float,
        pullback_axis: str,
        notes: list[int],
        channel: int | None = None,
        affected_object: tuple[str, str, float] | None = None,
    ):
        self.instruments: list[RoboticInstrument] = []
        self._starting_note = None
        self._final_note = None

        all_events = []

        for i in notes:
            target_object_name = f"{target_object_prefix}{i}"

            try:
                bpy.data.objects[target_object_name]
            except:
                continue

            instrument = RoboticInstrument(
                midi_file,
                control_object,
                target_object_name,
                pullback_amount,
                pullback_axis,
                note=i,
                channel=channel,
            )

            self.instruments.append(instrument)

            # collect events globally
            for e in instrument.events():
                e_copy = e.copy()
                e_copy["note"] = i
                all_events.append(e_copy)

        # detect the final and starting notes globally
        if all_events:
            starting_event = min(
                all_events,
                key=lambda e: e["start"] + e.get("duration", 0)
            )
            final_event = max(
                all_events,
                key=lambda e: e["start"] + e.get("duration", 0)
            )
            self._starting_note = starting_event["note"]
            self._final_note = final_event["note"]

    def generate_keyframes(self):
        for instrument in self.instruments:
            if instrument.note == self._starting_note:
                instrument.set_initialize_enabled(True)

            if instrument.note == self._final_note:
                instrument.set_return_enabled(True)

            instrument.generate_keyframes()
