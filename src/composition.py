import mido
from src.object import Object

class Composition:
    def __init__(
        self,
        name: str,
        midi_path: str,
        motion: str,
        motion_axis: int,
        max_n: int,
        fps: int = 24,
        hit_duration: int = 6
    ):
        super().__init__()

        self.name = name
        self.midi_path = midi_path
        self.motion = motion
        self.motion_axis = motion_axis
        self.fps = fps
        self.hit_duration = hit_duration
        self.max_n = max_n

        self.events = []
        self.objects = {}

        mid = mido.MidiFile(self.midi_path)

        print(mid)

        current_time = 0.0

        for msg in mid:
            current_time += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                self.events.append({
                    "time": current_time,
                    "velocity": msg.velocity / 127.0,
                    "note": msg.note,
                })

        # create one object per note
        for e in self.events:
            note = str(e["note"])

            if note not in self.objects:
                self.objects[note] = Object(self.name, note, self.motion, self.motion_axis)
                self.objects[note].reset()

    def run(self):
        for e in self.events:
            frame = e["time"] * self.fps
            note = str(e["note"])
            object = self.objects[note]
            object.hit(frame, e["velocity"], self.max_n, self.hit_duration)
