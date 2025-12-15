def initialize():
    import sys
    import importlib
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[1]
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

composition = Composition("Hammer", "/home/keller/mpsoftware/bmidi/tests/scale_down.mid", MotionRotation, MotionY, 35)
composition.run()
