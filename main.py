def initialize():
    import sys
    import importlib
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    import src.instrument

    importlib.reload(src.instrument)

initialize()

import math
from src.instrument import Instrument, append_instrument
import bpy

high_instrument = Instrument("/home/keller/mpsoftware/bmidi/test.mid", "Stick_High", "rotation_euler.x", math.radians(45), note=77)
low_instrument = Instrument("/home/keller/mpsoftware/bmidi/test.mid", "Stick_Low", "rotation_euler.x", math.radians(45), note=76)

bpy.context.scene.frame_set(0)
bpy.app.handlers.frame_change_pre.clear()

append_instrument(high_instrument)
append_instrument(low_instrument)
