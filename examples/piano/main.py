def initialize():
    import sys
    import importlib
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[3]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    import src.composition

    importlib.reload(src.composition)

initialize()

import bpy
import math
from src.composition import Composition

composition = Composition(
    "/home/keller/mpsoftware/bmidi/examples/piano/track.mid",
    "Key",
    "rotation_euler.y",
    math.radians(0),
    math.radians(10),
    overshoot_amount=math.radians(3),
)

bpy.context.scene.frame_set(-1)

composition.generate_keyframes()
