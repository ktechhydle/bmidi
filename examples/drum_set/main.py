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
from src.instrument import Instrument, append_instrument

offset = 12

cowbell = Instrument("/home/keller/mpsoftware/bmidi/examples/drum_set/track.mid", "Cowbell_Stick", "rotation_euler.x", 45, note=68 - offset)
tom_drum = Instrument("/home/keller/mpsoftware/bmidi/examples/drum_set/track.mid", "Tom_Stick", "rotation_euler.x", 45, note=62 - offset)

bpy.context.scene.frame_set(-1)
bpy.app.handlers.frame_change_pre.clear()

append_instrument(cowbell)
append_instrument(tom_drum)
