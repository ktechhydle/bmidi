def initialize():
    import sys
    import importlib
    import bpy
    from pathlib import Path

    ROOT = Path(bpy.data.filepath).parent.parent.parent
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    import src.composition
    import src.motion
    import src.object

    importlib.reload(src.composition)
    importlib.reload(src.motion)
    importlib.reload(src.object)

initialize()

from src.composition import Composition
from src.motion import MotionPosition, MotionRotation, MotionX, MotionY, MotionZ

composition = Composition("Hammer", "/home/keller/mpsoftware/bmidi/tests/chords/chords.mid", MotionRotation, MotionY, 35, hit_duration=6)
composition.run()
