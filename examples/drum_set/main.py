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
from src.instrument import Instrument, append_instrument

offset = 12 # the midi track is offset by 12 due to the way it was created

cowbell_hammer = Instrument("/home/keller/mpsoftware/bmidi/examples/drum_set/track.mid", "Cowbell_Stick", "rotation_euler.x", 90, note=68 - offset)
cowbell = Instrument("/home/keller/mpsoftware/bmidi/examples/drum_set/track.mid", "Cowbell", "rotation_euler.x", 3, note=68 - offset)
tom_drum_hammer = Instrument("/home/keller/mpsoftware/bmidi/examples/drum_set/track.mid", "Tom_Stick", "rotation_euler.x", 90, note=62 - offset)
tom_drum = Instrument("/home/keller/mpsoftware/bmidi/examples/drum_set/track.mid", "Tom", "location.z", -3, note=62 - offset)
snare_drum_hammer = Instrument("/home/keller/mpsoftware/bmidi/examples/drum_set/track.mid", "Snare_Stick", "rotation_euler.x", 90, note=50 - offset)
snare_drum = Instrument("/home/keller/mpsoftware/bmidi/examples/drum_set/track.mid", "Snare", "location.z", -3, note=50 - offset)
kick_drum_hammer = Instrument("/home/keller/mpsoftware/bmidi/examples/drum_set/track.mid", "Kick_Stick", "rotation_euler.x", 90, note=47 - offset)
kick_drum = Instrument("/home/keller/mpsoftware/bmidi/examples/drum_set/track.mid", "Kick", "location.x", -3, note=47 - offset)

bpy.context.scene.frame_set(-1)
bpy.app.handlers.frame_change_pre.clear()

append_instrument(cowbell_hammer)
append_instrument(cowbell)
append_instrument(tom_drum_hammer)
append_instrument(tom_drum)
append_instrument(snare_drum_hammer)
append_instrument(snare_drum)
append_instrument(kick_drum_hammer)
append_instrument(kick_drum)
