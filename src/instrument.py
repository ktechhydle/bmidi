import mido
import math
import bpy

class Instrument:
    def __init__(self, midi_file: str, object_name: str, object_property: str, reach: float, note: int | None = None):
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

    def handler(self, scene):
        t = scene.frame_current / scene.render.fps
        n = self.original_position

        for data in self.events:
            dt = t - data["start"]

            if 0 <= dt < data["duration"]:
                n += math.sin(math.pi * dt / data["duration"]) * data["velocity"] + self.reach

        exec(f"self.object.{self.object_property} = n")

def append_instrument(instrument: Instrument):
    if not hasattr(bpy, "_instruments"):
        bpy._instruments = []

    if instrument not in bpy._instruments:
        bpy._instruments.append(instrument)

    instrument_handler = lambda scene: instrument.handler(scene)

    if instrument_handler not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(instrument_handler)
