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

from src.instrument import Instrument
import bpy

instrument = Instrument("/home/keller/mpsoftware/bmidi/test.mid", "Stick", "rotation_euler.x", 45)

if not hasattr(bpy, "_instruments"):
    bpy._instruments = []

if instrument not in bpy._instruments:
    bpy._instruments.append(instrument)
