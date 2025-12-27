def initialize():
    import sys
    import importlib
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[3]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    import src.instrument

    importlib.reload(src.instrument)

initialize()

import bpy
import math
from src.instrument import Instrument

offset = 12 # the midi track is offset by 12 due to the way it was created

cowbell_hammer = Instrument(
    "/home/keller/mpsoftware/bmidi/examples/drum_set/track.mid",
    "Cowbell_Stick",
    "rotation_euler.x",
    math.radians(90),
    math.radians(35),
    overshoot_amount=math.radians(3),
    note=68 - offset,
    affected_object=("Cowbell", "rotation_euler.x", math.radians(1.5))
)
tom_drum_hammer = Instrument(
    "/home/keller/mpsoftware/bmidi/examples/drum_set/track.mid",
    "Tom_Stick",
    "rotation_euler.x",
    math.radians(90),
    math.radians(35),
    overshoot_amount=math.radians(3),
    note=62 - offset,
    affected_object=("Tom", "location.z", -0.1)
)
snare_drum_hammer = Instrument(
    "/home/keller/mpsoftware/bmidi/examples/drum_set/track.mid",
    "Snare_Stick",
    "rotation_euler.x",
    math.radians(90),
    math.radians(35),
    overshoot_amount=math.radians(3),
    note=50 - offset,
    affected_object=("Snare", "location.z", -0.1)
)
kick_drum_hammer = Instrument(
    "/home/keller/mpsoftware/bmidi/examples/drum_set/track.mid",
    "Kick_Stick",
    "rotation_euler.x",
    math.radians(180),
    math.radians(125),
    overshoot_amount=math.radians(3),
    note=47 - offset,
    affected_object=("Kick", "location.x", -0.1)
)

bpy.context.scene.frame_set(-1)

cowbell_hammer.generate_keyframes()
tom_drum_hammer.generate_keyframes()
snare_drum_hammer.generate_keyframes()
kick_drum_hammer.generate_keyframes()
