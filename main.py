def initialize():
    import sys
    import importlib
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    import src.instrument
    import src.composition

    importlib.reload(src.instrument)

initialize()

bl_info = {
    "name": "bmidi",
    "author": "Keller Hydle",
    "version": (0, 0, 1),
    "blender": (5, 0, 0),
    "location": "3D Viewport > Sidebar > bmidi",
    "description": "Automatic MIDI-data keyframing for Blender objects",
    "category": "Development"
}

import bpy
import math
from src.instrument import Instrument
from src.composition import Composition

class BMIDI_Item(bpy.types.PropertyGroup):
    type: bpy.props.EnumProperty(
        name="Type",
        items=[
            ("instrument", "Instrument", ""),
            ("composition", "Composition", ""),
        ]
    )
    name: bpy.props.StringProperty(name="Name", default="Instrument")
    midi_file: bpy.props.StringProperty(
        name="MIDI File",
        subtype="FILE_PATH"
    )
    object_name: bpy.props.StringProperty(name="Object")
    object_property: bpy.props.EnumProperty(
        name="Property",
        items=[
            ("location.x", "Location X", ""),
            ("location.y", "Location Y", ""),
            ("location.z", "Location Z", ""),
            ("rotation_euler.x", "Rotation X", ""),
            ("rotation_euler.y", "Rotation Y", ""),
            ("rotation_euler.z", "Rotation Z", ""),
            ("scale.x", "Scale X", ""),
            ("scale.y", "Scale Y", ""),
            ("scale.z", "Scale Z", ""),
        ]
    )
    initial_position: bpy.props.FloatProperty(name="Initial")
    pullback_position: bpy.props.FloatProperty(name="Pullback")
    overshoot_amount: bpy.props.FloatProperty(name="Overshoot")
    note: bpy.props.IntProperty(
        name="Note",
        min=-1,
        max=127,
        default=-1
    )

class BMIDI_UL_items(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon,
        active_data, active_propname, index
    ):
        layout.prop(item, "name", text="", emboss=False, icon="SOUND")

class VIEW_3D_OT_add_item(bpy.types.Operator):
    """
    Adds a new item
    """
    bl_idname = "bmidi_items.add_item"
    bl_label = "Add Item"

    def execute(self, context):
        inst = context.scene.bmidi_items.add()
        inst.name = f"Item {len(context.scene.bmidi_items)}"
        context.scene.bmidi_active_item = len(context.scene.bmidi_items) - 1

        return {'FINISHED'}

class VIEW_3D_OT_remove_item(bpy.types.Operator):
    """
    Removes the selected item
    """
    bl_idname = "bmidi_items.remove_item"
    bl_label = "Remove Item"

    def execute(self, context):
        idx = context.scene.bmidi_active_item
        context.scene.bmidi_items.remove(idx)
        context.scene.bmidi_active_item = max(0, idx - 1)

        return {'FINISHED'}

class VIEW_3D_OT_generate_keyframes(bpy.types.Operator):
    """
    Clears object animation data and generates the keyframes for all instruments and compositions
    """
    bl_idname = "bmidi.generate_keyframes"
    bl_label = "Generate Keyframes"

    def execute(self, context):
        for item in context.scene.bmidi_items:
            needs_radians = True if item.object_property in ("rotation_euler.x", "rotation_euler.y", "rotation_euler.z") else False

            if item.type == "instrument":
                instrument = Instrument(
                    item.midi_file,
                    item.object_name,
                    item.object_property,
                    math.radians(item.initial_position) if needs_radians else item.intial_position,
                    math.radians(item.pullback_position) if needs_radians else item.pullback_position,
                    overshoot_amount=math.radians(item.overshoot_amount) if needs_radians else item.overshoot_amount,
                    note=item.note if item.note > -1 else None,
                )
                instrument.generate_keyframes()
            elif item.type == "composition":
                composition = Composition(
                    item.midi_file,
                    item.object_name,
                    item.object_property,
                    math.radians(item.initial_position) if needs_radians else item.intial_position,
                    math.radians(item.pullback_position) if needs_radians else item.pullback_position,
                    overshoot_amount=math.radians(item.overshoot_amount) if needs_radians else item.overshoot_amount,
                )
                composition.generate_keyframes()

        return {'FINISHED'}

class VIEW_3D_PT_bmidi_panel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "bmidi"
    bl_label = "bmidi"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.template_list(
            "BMIDI_UL_items",
            "",
            scene,
            "bmidi_items",
            scene,
            "bmidi_active_item"
        )

        col = row.column(align=True)
        col.operator("bmidi_items.add_item", icon="ADD", text="")
        col.operator("bmidi_items.remove_item", icon="REMOVE", text="")

        if scene.bmidi_items:
            item = scene.bmidi_items[scene.bmidi_active_item]
            layout.prop(item, "type")
            layout.prop(item, "midi_file")
            layout.prop(item, "object_name")
            layout.prop(item, "object_property")
            layout.prop(item, "initial_position")
            layout.prop(item, "pullback_position")
            layout.prop(item, "overshoot_amount")

            # only show the note property if type is instrument
            if item.type == "instrument":
                layout.prop(item, "note")

        layout.separator()
        layout.operator("bmidi.generate_keyframes")

def register():
    bpy.utils.register_class(BMIDI_Item)
    bpy.utils.register_class(BMIDI_UL_items)

    bpy.types.Scene.bmidi_items = bpy.props.CollectionProperty(
        type=BMIDI_Item
    )
    bpy.types.Scene.bmidi_active_item = bpy.props.IntProperty()

    bpy.utils.register_class(VIEW_3D_PT_bmidi_panel)
    bpy.utils.register_class(VIEW_3D_OT_add_item)
    bpy.utils.register_class(VIEW_3D_OT_remove_item)
    bpy.utils.register_class(VIEW_3D_OT_generate_keyframes)

def unregister():
    bpy.utils.unregister_class(BMIDI_UL_items)
    bpy.utils.unregister_class(VIEW_3D_PT_bmidi_panel)
    bpy.utils.unregister_class(VIEW_3D_OT_add_item)
    bpy.utils.unregister_class(VIEW_3D_OT_remove_item)
    bpy.utils.unregister_class(VIEW_3D_OT_generate_keyframes)

if __name__ == "__main__":
    register()
