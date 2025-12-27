import mido
import math
import bpy


class Instrument:
    def __init__(
        self,
        midi_file: str,
        object_name: str,
        object_property: str,
        initial_position: float,
        pullback_position: float,
        overshoot_amount: float = 0,
        note: int | None = None,
        affects_object: tuple[str, str] | None = None,
    ):
        self.events = []
        self.object = bpy.data.objects[object_name]
        self.object_property = object_property
        self.initial_position = initial_position
        self.pullback_position = pullback_position
        self.overshoot_amount = overshoot_amount

        if affects_object is not None:
            self.affects_object = (bpy.data.objects[affects_object[0]], affects_object[1])

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

            if hasattr(self, "affects_object"):
                # TODO: make affected object feel impact from hit
                pass

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
