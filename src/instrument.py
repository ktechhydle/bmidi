import mido
import math
import bpy

class Instrument:
    def __init__(self, midi_file: str, object_name: str, object_property: str, reach: float):
        self.events = []
        self.object = bpy.data.objects[object_name]
        self.object_property = object_property
        exec(f"self.original_position = self.object.{self.object_property}")
        self.reach = reach

        midi = mido.MidiFile(midi_file)
        current_time = 0.0
        active_notes = {} # start_time, velocity

        for msg in midi:
            current_time += msg.time

            if msg.type == "note_on" and msg.velocity > 0:
                active_notes[msg.note] = ( current_time, msg.velocity / 127.0 )

            elif msg.type in ("note_off", "note_on") and msg.velocity == 0:
                if msg.note in active_notes:
                    start_time, velocity = active_notes.pop(msg.note)

                    self.events.append({
                        "start": start_time,
                        "duration": current_time - start_time,
                        "velocity": velocity, "note": msg.note,
                    })

        bpy.app.handlers.frame_change_pre.clear()
        bpy.app.handlers.frame_change_pre.append(lambda scene: self.handler(scene))

    def handler(self, scene):
        t = scene.frame_current / scene.render.fps
        n = self.original_position

        for data in self.events:
            dt = t - data["start"]

            if 0 <= dt < data["duration"]:
                n += math.sin(dt * 30) * data["velocity"] + (self.reach / 2)

        exec(f"self.object.{self.object_property} = n")
