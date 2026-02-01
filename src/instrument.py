import mido
import math
import bpy
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
    `initial_position`: where the object starts and rests at during notes
    `pullback_position`: how far the object moves from `initial_position` before springing back to hit the note
    `overshoot_amount`: how far past the object moves from `initial_position` during a note hit
    `note`: what pitch (numbers 1-127) controls the object, leaving this kwarg blank will result in the object moving based on all the notes in the midi file
    `channel`: what channel (numbers 0-15) controls the object, leaving this kwarg blank will result in the object moving based on all the channels in the midi file
    `affected_object`: an object (if any) that might be affected by this instrument, where `tuple[str, str, float]` is the object's name, property, and movement amount

    ## Example:

    ```python
    snare_drum_hammer = HammerInstrument(
        "track.mid", # midi file
        "Snare_Hammer", # object to control
        "rotation_euler.x", # property to control
        math.radians(90), # initial value
        math.radians(35), # pullback amount
        overshoot_amount=math.radians(3), # overshoot amount
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
        initial_position: float,
        pullback_position: float,
        overshoot_amount: float = 0,
        note: int | None = None,
        channel: int | None = None,
        affected_object: tuple[str, str, float] | None = None,
    ):
        super().__init__(midi_file, note, channel)

        self.object = bpy.data.objects[object_name]
        self.object_property = object_property
        self.initial_position = initial_position
        self.pullback_position = pullback_position
        self.overshoot_amount = overshoot_amount

        if affected_object is not None:
            self.affected_object = bpy.data.objects[affected_object[0]]
            self.affected_object_property = affected_object[1]
            self.affected_object_movement_amount = affected_object[2]

            self.affected_object.animation_data_clear()

        self.object.animation_data_clear()

    def generate_keyframes(self):
        fps = bpy.context.scene.render.fps
        obj = self.object
        obj.animation_data_clear()
        prop = self.object_property
        keyframe_prop = prop.split(".")[0]

        for e in self.events():
            start_frame = e["start"] * fps
            duration = 0.08 * fps # ~80ms time
            pullback_scale = 1 + (1 - e["velocity"]) * 1.5

            # start
            exec(f"obj.{prop} = self.initial_position")
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=start_frame - (duration * pullback_scale)
            )

            # pullback
            exec(f"obj.{prop} = self.pullback_position")
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=start_frame - duration
            )

            # hit
            exec(f"obj.{prop} = self.initial_position + self.overshoot_amount")
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=start_frame
            )

            # the affected object moves on note hits
            if hasattr(self, "affected_object"):
                affected_prop = self.affected_object_property
                affected_keyframe_prop = affected_prop.split(".")[0]
                prop_root, prop_axis = self.affected_object_property.split(".")
                og_position = getattr(getattr(self.affected_object, prop_root), prop_axis)

                exec(f"self.affected_object.{self.affected_object_property} = og_position")
                self.affected_object.keyframe_insert(
                    data_path=affected_keyframe_prop,
                    frame=start_frame - 1
                )

                exec(f"self.affected_object.{self.affected_object_property} = og_position + self.affected_object_movement_amount")
                self.affected_object.keyframe_insert(
                    data_path=affected_keyframe_prop,
                    frame=start_frame
                )

                exec(f"self.affected_object.{self.affected_object_property} = og_position")
                self.affected_object.keyframe_insert(
                    data_path=affected_keyframe_prop,
                    frame=start_frame + duration
                )

            exec(f"obj.{prop} = self.initial_position - (self.overshoot_amount * 0.75)")
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=start_frame + duration
            )

            # return to original position
            exec(f"obj.{prop} = self.initial_position")
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=start_frame + (duration * pullback_scale)
            )

class MovementInstrument(Instrument):
    """
    Represents a movement-like instrument that moves when notes are played

    `object_name`: the object to control
    `object_property`: the blender object property to control, like `rotation_euler.x` or `location.y`
    `initial_position`: where the object starts
    `final_position`: where the object moves to when a note is hit
    `note`: what pitch (numbers 1-127) controls the object, leaving this kwarg blank will result in the object moving based on all the notes in the midi file
    `channel`: what channel (numbers 0-15) controls the object, leaving this kwarg blank will result in the object moving based on all the channels in the midi file

    ## Example:

    ```python
    trumpet_horn = MovementInstrument(
        "track.mid", # midi file
        "Trumpet_Horn", # object to control
        "location.x", # property to control
        0, # initial value
        0.1, # final value
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
        initial_position: float,
        final_position: float,
        note: int | None = None,
        channel: int | None = None,
    ):
        super().__init__(midi_file, note, channel)

        self.object = bpy.data.objects[object_name]
        self.object_property = object_property
        self.initial_position = initial_position
        self.final_position = final_position

        self.object.animation_data_clear()

    def generate_keyframes(self):
        fps = bpy.context.scene.render.fps
        obj = self.object
        obj.animation_data_clear()
        prop = self.object_property
        keyframe_prop = prop.split(".")[0]

        for e in self.events():
            start_frame = e["start"] * fps
            end_frame = (e["start"] + e["duration"]) * fps
            duration = e["duration"] * fps

            # start
            exec(f"obj.{prop} = self.initial_position")
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=start_frame - 1
            )

            # note played
            exec(f"obj.{prop} = self.final_position")
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=start_frame
            )

            # hold final position until note ends
            exec(f"obj.{prop} = self.final_position")
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=end_frame
            )

            # return to original after note ends
            exec(f"obj.{prop} = self.initial_position")
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=end_frame + 1
            )

class RoboticInstrument(Instrument):
    """
    Represents a robotic-arm-like instrument that reaches and hits a note at a specified position

    `bone_name`: the bone to control
    `rest_position`: the armature's resting position
    `reach_position`: the armature's reach position to hit the note
    `note`: what pitch (numbers 1-127) controls the object, leaving this kwarg blank will result in the object moving based on all the notes in the midi file
    `channel`: what channel (numbers 0-15) controls the object, leaving this kwarg blank will result in the object moving based on all the channels in the midi file
    `affected_object`: an object (if any) that might be affected by this instrument, where `tuple[str, str, float]` is the object's name, property, and movement amount

    ## Example:

    ```python
    snare_drum_arm = RoboticInstrument(
        "track.mid", # midi file
        "Bone1", # bone to control
        (0, 0, 0), # initial position
        (1, 1, 1), # final position
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
        armature_name: str,
        bone_name: str,
        rest_position: tuple[float, float, float],
        reach_position: tuple[float, float, float],
        note: int | None = None,
        channel: int | None = None,
        affected_object: tuple[str, str, float] | None = None,
    ):
        super().__init__(midi_file, note, channel)

        self.armature = bpy.data.objects[armature_name]
        self.pose_bone = self.armature.pose.bones.get(bone_name)
        self.rest_position = rest_position
        self.reach_position = reach_position

        if affected_object is not None:
            self.affected_object = bpy.data.objects[affected_object[0]]
            self.affected_object_property = affected_object[1]
            self.affected_object_movement_amount = affected_object[2]

            self.affected_object.animation_data_clear()

        self.armature.animation_data_clear()

    def generate_keyframes(self):
        fps = bpy.context.scene.render.fps
        arm = self.armature
        bone = self.pose_bone

        for e in self.events():
            start_frame = e["start"] * fps
            duration = 0.08 * fps
            pullback_scale = 1 + (1 - e["velocity"]) * 1.5

            bone.location = self.rest_position
            arm.keyframe_insert(
                data_path=f'pose.bones["{bone.name}"].location',
                frame=start_frame - (duration * pullback_scale)
            )

            # hit
            bone.location = self.reach_position
            arm.keyframe_insert(
                data_path=f'pose.bones["{bone.name}"].location',
                frame=start_frame
            )

            # if hasattr(self, "affected_object"):
            #     affected_prop = self.affected_object_property
            #     affected_keyframe_prop = affected_prop.split(".")[0]
            #     prop_root, prop_axis = self.affected_object_property.split(".")
            #     og_position = getattr(getattr(self.affected_object, prop_root), prop_axis)

            #     exec(f"self.affected_object.{self.affected_object_property} = og_position")
            #     self.affected_object.keyframe_insert(
            #         data_path=affected_keyframe_prop,
            #         frame=start_frame - 1
            #     )

            #     exec(f"self.affected_object.{self.affected_object_property} = og_position + self.affected_object_movement_amount")
            #     self.affected_object.keyframe_insert(
            #         data_path=affected_keyframe_prop,
            #         frame=start_frame
            #     )

            #     exec(f"self.affected_object.{self.affected_object_property} = og_position")
            #     self.affected_object.keyframe_insert(
            #         data_path=affected_keyframe_prop,
            #         frame=start_frame + duration
            #     )

            # return
            bone.location = self.rest_position
            arm.keyframe_insert(
                data_path=f'pose.bones["{bone.name}"].location',
                frame=start_frame + (duration * pullback_scale)
            )
