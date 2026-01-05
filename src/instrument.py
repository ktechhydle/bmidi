import mido
import math
import bpy


class Instrument:
    """
    Represents a single "instrument" that can be controlled by a specific pitch or the whole midi file

    `object_name`: the object to control
    `object_property`: the blender object property to control, like `rotation_euler.x` or `location.y`
    `initial_position`: where the object starts and rests at during notes
    `pullback_position`: how far the object moves from `initial_position` before springing back to hit the note
    `overshoot_amount`: how far past the object moves from `initial_position` during a note hit
    `note`: what pitch (numbers 1-127) controls the object, leaving this kwarg blank will result in the object moving based on all the notes in the midi file
    `affected_object`: an object (if any) that might be affected by this instrument, where `tuple[str, str, float]` is the object's name, property, and movement amount

    ## Example:

    ```python
    snare_drum_hammer = Instrument(
        "track.mid", # midi file
        "Snare_Stick", # object to control
        "rotation_euler.x", # property to control
        math.radians(90), # initial value
        math.radians(35), # pullback amount
        overshoot_amount=math.radians(3), # overshoot amount
        note=25, # what pitch controls the object
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
        affected_object: tuple[str, str, float] | None = None,
    ):
        self.events = []
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

        midi = mido.MidiFile(midi_file)
        current_time = 0.0
        active_notes = {} # start_time, velocity

        for msg in midi:
            current_time += msg.time

            if msg.type == "note_on" and msg.velocity > 0:
                if note is not None and msg.note != note:
                    continue

                active_notes[msg.note] = ( current_time, msg.velocity / 127.0 )

            elif msg.type in ("note_off", "note_on") and msg.velocity == 0:
                if note is not None and msg.note != note:
                    continue

                if msg.note in active_notes:
                    start_time, velocity = active_notes.pop(msg.note)

                    self.events.append({
                        "note": msg.note,
                        "start": start_time,
                        "duration": current_time - start_time,
                        "velocity": velocity,
                    })

        self.object.animation_data_clear()

    def generate_keyframes(self):
        fps = bpy.context.scene.render.fps
        obj = self.object
        obj.animation_data_clear()
        prop = self.object_property
        keyframe_prop = prop.split(".")[0]

        for e in self.events:
            start_frame = int(e["start"] * fps)
            end_frame = int((e["start"] + e["duration"]) * fps)
            duration = int(e["duration"] * fps)
            note_velocity = e["velocity"]

            # start
            exec(f"obj.{prop} = self.initial_position")
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=start_frame - (duration * 1.75)
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
                    frame=start_frame - duration
                )

                exec(f"self.affected_object.{self.affected_object_property} = og_position + self.affected_object_movement_amount")
                self.affected_object.keyframe_insert(
                    data_path=affected_keyframe_prop,
                    frame=start_frame
                )

                exec(f"self.affected_object.{self.affected_object_property} = og_position")
                self.affected_object.keyframe_insert(
                    data_path=affected_keyframe_prop,
                    frame=end_frame
                )

            exec(f"obj.{prop} = self.initial_position - (self.overshoot_amount * 0.75)")
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=end_frame - (duration * 0.1)
            )

            # return to original position
            exec(f"obj.{prop} = self.initial_position")
            obj.keyframe_insert(
                data_path=keyframe_prop,
                frame=end_frame
            )
