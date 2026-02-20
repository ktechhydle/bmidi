import mido
import math
import bpy
import mathutils
from collections import defaultdict


def get_midi_channel_ranges(midi_path: str):
    ranges = defaultdict(lambda: [127, 0])

    try:
        mid = mido.MidiFile(midi_path)
    except Exception:
        return {}

    for track in mid.tracks:
        for msg in track:
            if msg.type == "note_on" and msg.velocity > 0:
                ch = msg.channel + 1  # mido is 0–15
                ranges[ch][0] = min(ranges[ch][0], msg.note)
                ranges[ch][1] = max(ranges[ch][1], msg.note)

    # Remove unused channels
    return {
        ch: (mn, mx)
        for ch, (mn, mx) in ranges.items()
        if mn <= mx
    }

def get_channel_items(self, context):
    scene = context.scene

    if scene.bmidi_midi_file:
        channels = get_midi_channel_ranges(scene.bmidi_midi_file)

        if channels:
            return [(str(ch), str(ch), "") for ch in sorted(channels)]

    return []

def get_base_position(object, prop):
    prop_root, prop_axis = prop.split(".")

    return getattr(getattr(object, prop_root), prop_axis)

def get_prop(obj, prop_path: str):
    root, attr = prop_path.split(".")
    return getattr(getattr(obj, root), attr)

def set_prop(obj, prop_path: str, value):
    root, attr = prop_path.split(".")
    container = getattr(obj, root)
    setattr(container, attr, value)

def get_emission_input(mat):
    nodes = mat.node_tree.nodes

    # emission node
    for node in nodes:
        if node.type == 'EMISSION':
            return node.inputs.get("Strength")

    # principled BSDF
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            if "Emission Strength" in node.inputs:
                return node.inputs["Emission Strength"]

    return None


class Instrument:
    def __init__(self, midi_file: str, note: int | None = None, channel: int | None = None):
        self._events = []

        midi = mido.MidiFile(midi_file)
        current_time = 0.0
        active_notes = {} # start_time, velocity

        for msg in midi:
            current_time += msg.time

            if msg.type == "note_on" and msg.velocity > 0:
                if note is not None and msg.note != note:
                    continue

                if channel is not None and msg.channel != channel:
                    continue

                active_notes[(msg.note, msg.channel)] = ( current_time, msg.velocity / 127.0 )

            elif msg.type in ("note_off", "note_on") and msg.velocity == 0:
                if note is not None and msg.note != note:
                    continue

                if channel is not None and msg.channel != channel:
                    continue

                key = (msg.note, msg.channel)
                if key in active_notes:
                    start_time, velocity = active_notes.pop(key)

                    self._events.append({
                        "note": msg.note,
                        "start": start_time,
                        "duration": current_time - start_time,
                        "velocity": velocity,
                    })

    def events(self) -> list[dict[str, float]]:
        return self._events

    def generate_keyframes(self) -> None:
        pass

class HammerInstrument(Instrument):
    """
    Represents a hammer-like instrument that pulls back and springs forward hitting a note

    `object_name`: the object to control
    `object_property`: the blender object property to control, like `rotation_euler.x` or `location.y`
    `pullback_position`: how far the object moves from the initial position before springing back to hit the note
    `overshoot_amount`: how far past the object moves from initial position during a note hit
    `note`: what pitch (numbers 1-127) controls the object, leaving this kwarg blank will result in the object moving based on all the notes in the midi file
    `channel`: what channel (numbers 0-15) controls the object, leaving this kwarg blank will result in the object moving based on all the channels in the midi file
    `affected_object`: an object (if any) that might be affected by this instrument, where `tuple[str, str, float]` is the object's name, property, and movement amount

    ## Example:

    ```python
    snare_drum_hammer = HammerInstrument(
        "track.mid", # midi file
        "Snare_Hammer", # object to control
        "rotation_euler.x", # property to control
        math.radians(35), # pullback amount (the origin is assumed as the object's initial position)
        overshoot_amount=math.radians(3), # overshoot amount (the origin is assumed as the object's initial position)
        note=25, # what pitch controls the object
        channel=9, # what channel controls the object
        affected_object=("Snare", "location.z", -0.1), # what object is affected by this object
    )
    snare_drum_hammer.generate_keyframes() # generate the keyframes
    ```
    """
    def __init__(
        self,
        midi_file: str,
        object_name: str,
        object_property: str,
        pullback_amount: float,
        overshoot_amount: float = 0,
        note: int | None = None,
        channel: int | None = None,
        affected_object: tuple[str, str, float] | None = None,
    ):
        super().__init__(midi_file, note, channel)

        self.object = bpy.data.objects[object_name]
        self.object_property = object_property
        self.pullback_amount = pullback_amount
        self.overshoot_amount = overshoot_amount

        if affected_object is not None:
            self.affected_object = bpy.data.objects[affected_object[0]]
            self.affected_object_property = affected_object[1]
            self.affected_object_movement_amount = affected_object[2]

            self.affected_object.animation_data_clear()

        self.object.animation_data_clear()

    def generate_keyframes(self):
        scene = bpy.context.scene
        fps = scene.render.fps
        obj = self.object
        pullback = self.pullback_amount
        overshoot = self.overshoot_amount
        prop = self.object_property
        keyframe_prop = prop.split(".")[0]
        base = get_base_position(obj, prop)

        for e in self.events():
            start = e["start"] * fps
            duration = 0.08 * fps # ~80ms time
            velocity_scale = 1 + (1 - e["velocity"]) * 1.5

            frame_start = start - (duration * velocity_scale)
            frame_pullback = start - duration
            frame_hit = start
            frame_oscillate = start + duration
            frame_end = start + (duration * velocity_scale)

            # start
            set_prop(obj, prop, base)
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=frame_start
            )

            # pullback
            set_prop(obj, prop, base + pullback)
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=frame_pullback
            )

            # hit
            set_prop(obj, prop, base + overshoot)
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=frame_hit
            )

            # the affected object moves on note hits
            if hasattr(self, "affected_object"):
                affected_prop = self.affected_object_property
                affected_keyframe_prop = affected_prop.split(".")[0]
                prop_root, prop_axis = self.affected_object_property.split(".")
                og_position = getattr(getattr(self.affected_object, prop_root), prop_axis)

                set_prop(self.affected_object, self.affected_object_property, og_position)
                self.affected_object.keyframe_insert(
                    data_path=affected_keyframe_prop,
                    frame=start - 1
                )

                set_prop(self.affected_object, self.affected_object_property, og_position + self.affected_object_movement_amount)
                self.affected_object.keyframe_insert(
                    data_path=affected_keyframe_prop,
                    frame=start
                )

                set_prop(self.affected_object, self.affected_object_property, og_position)
                self.affected_object.keyframe_insert(
                    data_path=affected_keyframe_prop,
                    frame=start + duration
                )

            # oscillate
            set_prop(obj, prop, base - (overshoot * 0.75))
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=frame_oscillate
            )

            # end
            set_prop(obj, prop, base)
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=frame_end
            )

class MovementInstrument(Instrument):
    """
    Represents a movement-like instrument that moves when notes are played

    `object_name`: the object to control
    `object_property`: the blender object property to control, like `rotation_euler.x` or `location.y`
    `final_amount`: where the object moves to when a note is hit (the origin is assumed as the object's initial position)
    `note`: what pitch (numbers 1-127) controls the object, leaving this kwarg blank will result in the object moving based on all the notes in the midi file
    `channel`: what channel (numbers 0-15) controls the object, leaving this kwarg blank will result in the object moving based on all the channels in the midi file

    ## Example:

    ```python
    trumpet_horn = MovementInstrument(
        "track.mid", # midi file
        "Trumpet_Horn", # object to control
        "location.x", # property to control
        0.1, # final amount
        note=25, # what pitch controls the object
        channel=9, # what channel controls the object
    )
    trumpet_horn.generate_keyframes() # generate the keyframes
    ```
    """
    def __init__(
        self,
        midi_file: str,
        object_name: str,
        object_property: str,
        final_amount: float,
        note: int | None = None,
        channel: int | None = None,
    ):
        super().__init__(midi_file, note, channel)

        self.object = bpy.data.objects[object_name]
        self.object_property = object_property
        self.final_amount = final_amount

        self.object.animation_data_clear()

    def generate_keyframes(self):
        fps = bpy.context.scene.render.fps
        obj = self.object
        final = self.final_amount
        prop = self.object_property
        keyframe_prop = prop.split(".")[0]
        base = get_base_position(obj, prop)

        for e in self.events():
            start = e["start"] * fps
            end = (e["start"] + e["duration"]) * fps
            duration = 1 # 1 frame
            velocity_scale = 1 + (1 - e["velocity"]) * 1.5

            frame_start = start - (duration * velocity_scale)
            frame_played = start
            frame_hold = end
            frame_end = end + (duration * velocity_scale)

            # start
            set_prop(obj, prop, base)
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=frame_start
            )

            # note played
            set_prop(obj, prop, base + final)
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=frame_played
            )

            # hold final position until note ends
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=frame_hold
            )

            # return to original after note ends
            set_prop(obj, prop, base)
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=frame_end
            )

class LightInstrument(Instrument):
    """
    Represents a light-like instrument that changes light properties when notes are played

    `object_name`: the light object to control
    `light_property`: the light property to control, like `data.energy` or `data.spot_size` (for spot lights)
    `initial_amount`: where the light object initializes before and after a note is hit
    `final_amount`: where the light object stays at while a note is hit
    `mode`: "light" for light objects and "emission" for materials
    `fade_effect`: add a fade effect at the end of each note
    `note`: what pitch (numbers 1-127) controls the object, leaving this kwarg blank will result in the object moving based on all the notes in the midi file
    `channel`: what channel (numbers 0-15) controls the object, leaving this kwarg blank will result in the object moving based on all the channels in the midi file

    ## Example:

    ```python
    synth_glow = LightInstrument(
        "track.mid", # midi file
        "Cone_Light", # object to control
        "data.spot_size", # property to control
        math.radians(15), # initial amount
        math.radians(30), # final amount
        mode="light", # mode
        note=25, # what pitch controls the object
        channel=9, # what channel controls the object
    )
    synth_glow.generate_keyframes() # generate the keyframes
    ```
    """
    def __init__(
        self,
        midi_file: str,
        object_name: str,
        light_property: str,
        initial_amount: float,
        final_amount: float,
        mode: str = "light",
        fade_effect: bool = False,
        note: int | None = None,
        channel: int | None = None,
    ):
        super().__init__(midi_file, note, channel)

        self.object = bpy.data.objects[object_name]
        self.light_property = light_property
        self.initial_amount = initial_amount
        self.final_amount = final_amount
        self.mode = mode
        self.fade_effect = fade_effect

        self.object.data.animation_data_clear()

    def generate_keyframes(self):
        fps = bpy.context.scene.render.fps
        obj = self.object
        initial = self.initial_amount
        final = self.final_amount
        fade_effect = self.fade_effect
        prop = self.light_property
        target = obj.data
        keyframe_prop = prop.split(".")[1]

        if self.mode == "emission":
            mat = next((m for m in obj.data.materials if m), None)
            socket = get_emission_input(mat)

            if socket is None:
                raise ValueError("No emission input found.")

            target = socket
            keyframe_prop = "default_value"

        for e in self.events():
            start = e["start"] * fps
            end = (e["start"] + e["duration"]) * fps
            duration = 1 # 1 frame
            velocity_scale = 1 + (1 - e["velocity"]) * 1.5

            frame_start = start - (duration * velocity_scale)
            frame_played = start
            frame_hold = end
            frame_end = end + (duration * velocity_scale)

            # start
            if self.mode == "emission":
                target.default_value = initial
            else:
                 set_prop(obj, prop, initial)
            target.keyframe_insert(
                data_path=keyframe_prop,
                frame=frame_start
            )

            # note played
            if self.mode == "emission":
                target.default_value = initial + final
            else:
                 set_prop(obj, prop, initial + final)
            target.keyframe_insert(
                data_path=keyframe_prop,
                frame=frame_played
            )

            if not fade_effect:
                # hold final position until note ends
                target.keyframe_insert(
                    data_path=keyframe_prop,
                    frame=frame_hold
                )

            # return to original after note ends
            if self.mode == "emission":
                target.default_value = initial
            else:
                 set_prop(obj, prop, initial)
            target.keyframe_insert(
                data_path=keyframe_prop,
                frame=frame_end
            )

class RoboticInstrument(Instrument):
    """
    Represents a robotic-arm-like instrument that reaches and hits a note at a specified position

    `control_object`: the object to control (typically an IK target)
    `target_object`: the object to reach and hit the note
    `pullback_amount`: how far the arm should pull back before hitting a note
    `pullback_axis`: what axis direction pulls back on the arm
    `note`: what pitch (numbers 1-127) controls the object, leaving this kwarg blank will result in the object moving based on all the notes in the midi file
    `channel`: what channel (numbers 0-15) controls the object, leaving this kwarg blank will result in the object moving based on all the channels in the midi file
    `affected_object`: an object (if any) that might be affected by this instrument, where `tuple[str, str, float]` is the object's name, property, and movement amount

    ## Example:

    ```python
    snare_drum_arm = RoboticInstrument(
        "track.mid", # midi file
        "IK_Target", # object to control
        "Snare_Drum", # target object to hit
        0.1, # how far to wind up
        "z", # what axis to wind up
        note=25, # what pitch controls the object
        channel=9, # what channel controls the object
        affected_object=("Snare", "location.z", -0.1), # what object is affected by this object
    )
    snare_drum_arm.generate_keyframes() # generate the keyframes
    ```
    """
    def __init__(
        self,
        midi_file: str,
        control_object: str,
        target_object: str,
        pullback_amount: float,
        pullback_axis: str,
        initialize_enabled: bool = False,
        return_enabled: bool = False,
        note: int | None = None,
        channel: int | None = None,
        affected_object: tuple[str, str, float] | None = None,
    ):
        super().__init__(midi_file, note, channel)

        self.control_object = bpy.data.objects[control_object]
        self.target_object = bpy.data.objects[target_object]
        self.pullback_amount = pullback_amount
        self.pullback_axis = pullback_axis
        self.note = note

        self._initialize_enabled = initialize_enabled
        self._return_enabled = return_enabled

        if affected_object is not None:
            self.affected_object = bpy.data.objects[affected_object[0]]
            self.affected_object_property = affected_object[1]
            self.affected_object_movement_amount = affected_object[2]

            self.affected_object.animation_data_clear()

        self.control_object.animation_data_clear()

    def generate_keyframes(self):
        fps = bpy.context.scene.render.fps
        control = self.control_object
        target = self.target_object
        pullback = self.pullback_amount
        axis = self.pullback_axis
        base = control.location.copy()

        offset_vec = mathutils.Vector(
            (
                pullback if axis == "x" else 0,
                pullback if axis == "y" else 0,
                pullback if axis == "z" else 0,
            )
        )

        if self.events() and self._initialize_enabled:
            event = self.events()[0]
            start = (event["start"] - event["duration"]) * fps

            control.location = base
            control.keyframe_insert(
                data_path="location",
                frame=start
            )

        for e in self.events():
            start = e["start"] * fps
            # pullback_scale = 1 + (1 - e["velocity"]) * 1.5
            duration = e["duration"] * fps

            pullback_frames = duration * 0.2
            strike_frames = duration * 0.3
            rebound_frames = duration * 0.2
            pullback_start = start - pullback_frames
            strike_mid = start - (strike_frames * 0.5)
            impact = start
            rebound_end = start + rebound_frames

            # pullback
            control.location = target.location + offset_vec
            control.keyframe_insert(
                data_path="location",
                frame=pullback_start
            )

            # strike mid
            control.location = target.location + (offset_vec * 0.5)
            control.keyframe_insert(
                data_path="location",
                frame=strike_mid
            )

            # hit
            control.location = target.location
            control.keyframe_insert(
                data_path="location",
                frame=impact
            )

            # the affected object moves on note hits
            if hasattr(self, "affected_object"):
                affected_prop = self.affected_object_property
                affected_keyframe_prop = affected_prop.split(".")[0]
                prop_root, prop_axis = self.affected_object_property.split(".")
                og_position = getattr(getattr(self.affected_object, prop_root), prop_axis)

                set_prop(self.affected_object, self.affected_object_property, og_position)
                self.affected_object.keyframe_insert(
                    data_path=affected_keyframe_prop,
                    frame=start - 1
                )

                set_prop(self.affected_object, self.affected_object_property, og_position + self.affected_object_movement_amount)
                self.affected_object.keyframe_insert(
                    data_path=affected_keyframe_prop,
                    frame=start
                )

                set_prop(self.affected_object, self.affected_object_property, og_position)
                self.affected_object.keyframe_insert(
                    data_path=affected_keyframe_prop,
                    frame=start + duration
                )

            # return
            control.location = target.location + offset_vec
            control.keyframe_insert(
                data_path="location",
                frame=rebound_end
            )

        # return to final resting position after all motion is complete
        if self.events() and self._return_enabled:
            event = self.events()[-1]
            end = (event["start"] + event["duration"]) * fps

            control.location = base
            control.keyframe_insert(
                data_path="location",
                frame=end
            )

    def set_initialize_enabled(self, enabled: bool):
        self._initialize_enabled = enabled

    def set_return_enabled(self, enabled: bool):
        self._return_enabled = enabled
