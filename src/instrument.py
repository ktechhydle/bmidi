import mido
import math
import bpy

def spring_step(pos, vel, target, stiffness, damping, dt):
    force = (target - pos) * stiffness
    vel += force * dt
    vel *= damping
    pos += vel * dt
    return pos, vel

class Instrument:
    def __init__(self, midi_file: str, object_name: str, object_property: str, reach: float, note: int | None = None):
        self.events = []
        self.object = bpy.data.objects[object_name]
        self.object_property = object_property
        exec(f"self.original_position = self.object.{self.object_property}")
        self.reach = reach / 10
        self.pos = self.original_position
        self.vel = 0.0

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
        fps = scene.render.fps
        dt = 1.0 / fps
        t = scene.frame_current / fps

        target = self.original_position

        for data in self.events:
            note_t = t - data["start"]

            if 0 <= note_t < data["duration"]:
                target = (self.original_position + self.reach) * data["velocity"]

        stiffness = 80.0    # snap
        damping   = 0.75    # bounce

        self.pos, self.vel = spring_step(
            self.pos,
            self.vel,
            target,
            stiffness,
            damping,
            dt
        )

        exec(f"self.object.{self.object_property} = self.pos")


def append_instrument(instrument: Instrument):
    if not hasattr(bpy, "_instruments"):
        bpy._instruments = []

    if instrument not in bpy._instruments:
        bpy._instruments.append(instrument)

    instrument_handler = lambda scene: instrument.handler(scene)

    if instrument_handler not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(instrument_handler)
