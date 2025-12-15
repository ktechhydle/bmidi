import bpy
import math
from src.motion import MotionPosition, MotionRotation

# reset frame
bpy.context.scene.frame_set(0)

class Object:
    def __init__(self, control_name: str, note: str, motion: str, motion_axis: int):
        super().__init__()

        self.control_name = control_name
        self.note = note
        self.motion = motion
        self.motion_axis = motion_axis

    def hit(self, frame: int, strength: int,  max_rotation: float, hit_duration: int):
        angle = math.radians(max_rotation) * strength

        obj = bpy.data.objects.get(self.name())

        if obj is None:
            print(f"Object '{self.name()}' not found")

            return

        if self.motion == MotionRotation:
            original_rotation = obj.rotation_euler[self.motion_axis]

            obj.rotation_euler[self.motion_axis] = original_rotation
            obj.keyframe_insert("rotation_euler", frame=frame - hit_duration)

            # hit
            obj.rotation_euler[self.motion_axis] = angle
            obj.keyframe_insert("rotation_euler", frame=frame)

            # return
            obj.rotation_euler[self.motion_axis] = original_rotation
            obj.keyframe_insert("rotation_euler", frame=frame + hit_duration)
        elif self.motion == MotionPosition:
            # TODO: implement
            print("TODO!")

    def reset(self):
        obj = bpy.data.objects.get(self.name())

        if obj is None:
            print(f"Object '{self.name()}' not found")

            return

        # reset animation
        obj.animation_data_clear()

    def name(self) -> str:
        return f"{self.control_name}_{self.note}"
