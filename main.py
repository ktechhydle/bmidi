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
    importlib.reload(src.composition)

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
from src.instrument import get_channel_items, get_midi_channel_ranges
from src.composition import HammerComposition, LightComposition, MovementComposition
from src.controller import RoboticController

ROTATION_PROPERTIES = ("rotation_euler.x", "rotation_euler.y", "rotation_euler.z")
LOCATION_PROPERTIES = ("location.x", "location.y", "location.z")
SCALE_PROPERTIES = ("scale.x", "scale.y", "scale.z")
OBJECT_PROPERTIES = [
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
LIGHT_PROPERTIES = [
    ("data.energy", "Light Power", ""),
    ("emission.emission", "Emissive Power", "Applies only to objects with an emissive material"),
    ("data.spot_size", "Spotlight Angle", "Applies only to spot light objects"),
]

class BMIDI_Item(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Enabled",
        description="Generate keyframes for this item",
        default=True
    )
    type: bpy.props.EnumProperty(
        name="Type",
        items=[
            ("hammer_composition", "Hammer Composition", "A collection of hammer instruments that swing back and \"hit\" notes"),
            ("movement_composition", "Movement Composition", "A collection of instruments that hold a certain position while a note is active"),
            ("light_composition", "Light Composition", "A collection of light instruments that can be controlled by light power or material emissivity while a note is active"),
            ("robotic_controller", "Robotic Controller", "A controller for robotic arm instruments that that swing back and \"hit\" target objects (notes)"),
        ]
    )
    object_prefix: bpy.props.StringProperty(name="Object Prefix")
    object_property: bpy.props.EnumProperty(
        name="Property",
        items=OBJECT_PROPERTIES
    )
    pullback_amount: bpy.props.FloatProperty(name="Pullback Amount")
    overshoot_amount: bpy.props.FloatProperty(name="Overshoot Amount")
    note_range_start: bpy.props.IntProperty(
        name="Note Range Start",
        min=0,
        max=127,
        default=0
    )
    note_range_end: bpy.props.IntProperty(
        name="Note Range End",
        min=0,
        max=127,
        default=127
    )
    use_block_list: bpy.props.BoolProperty(
        name="Use Block List",
        description="Block certain notes used by a composition or controller",
        default=False
    )
    blocked_notes: bpy.props.StringProperty(
        name="Blocked Notes",
        description="Comma separated MIDI notes",
        default=""
    )
    channel: bpy.props.EnumProperty(
        name="Channel",
        items=get_channel_items,
    )

    # light controls
    light_object_property: bpy.props.EnumProperty(
        name="Light Property",
        items=LIGHT_PROPERTIES
    )
    light_object_fade_effect: bpy.props.BoolProperty(name="Fade Effect")

    # robotic controls
    robot_target_object_name: bpy.props.StringProperty(name="Target Object Prefix")
    robot_pullback_axis: bpy.props.EnumProperty(
        name="Pullback Axis",
        items=[
            ("x", "X Axis", ""),
            ("y", "Y Axis", ""),
            ("z", "Z Axis", ""),
        ]
    )

class BMIDI_UL_items(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon,
        active_data, active_propname, index
    ):
        row = layout.row(align=True)
        row.prop(item, "object_prefix", text="", emboss=False, icon="SOUND")
        row.prop(item, "type", text="", emboss=False)
        row.prop(item, "enabled", text="")

class VIEW_3D_OT_add_item(bpy.types.Operator):
    """Adds a new item"""
    bl_idname = "bmidi_items.add_item"
    bl_label = "Add Item"

    def execute(self, context):
        context.scene.bmidi_items.add()
        context.scene.bmidi_active_item = len(context.scene.bmidi_items) - 1

        return {'FINISHED'}

class VIEW_3D_OT_remove_item(bpy.types.Operator):
    """Removes the selected item"""
    bl_idname = "bmidi_items.remove_item"
    bl_label = "Remove Item"

    def execute(self, context):
        idx = context.scene.bmidi_active_item
        context.scene.bmidi_items.remove(idx)
        context.scene.bmidi_active_item = max(0, idx - 1)

        return {'FINISHED'}

class VIEW_3D_OT_duplicate_item(bpy.types.Operator):
    """Duplicates the selected item"""
    bl_idname = "bmidi_items.duplicate_item"
    bl_label = "Duplicate Item"

    def execute(self, context):
        items = context.scene.bmidi_items
        idx = context.scene.bmidi_active_item

        if idx < 0 or idx >= len(items):
            return {'CANCELLED'}

        src = items[idx]

        # create new item
        items.add()
        dst = items[-1]

        # copy all RNA properties
        for prop in src.bl_rna.properties:
            if prop.identifier == "rna_type":
                continue
            setattr(dst, prop.identifier, getattr(src, prop.identifier))

        dst.object_prefix = f"{src.object_prefix} (COPY)"

        # move it right after the original
        items.move(len(items) - 1, idx + 1)
        context.scene.bmidi_active_item = idx + 1

        return {'FINISHED'}

class VIEW_3D_OT_generate_keyframes(bpy.types.Operator):
    """
    Clears object animation data and generates the keyframes for all instruments and compositions
    """
    bl_idname = "bmidi.generate_keyframes"
    bl_label = "Generate Keyframes"

    def execute(self, context):
        context.scene.frame_set(-1)
        midi_file = context.scene.bmidi_midi_file

        if not midi_file:
            self.report({'ERROR'}, "No MIDI file selected")
            return {'CANCELLED'}

        for item in context.scene.bmidi_items:
            if not item.enabled:
                continue

            needs_radians = (True if item.object_property in ROTATION_PROPERTIES else False) or (item.type == "light_composition" and item.light_object_property == "data.spot_size")

            pullback_amount = math.radians(item.pullback_amount) if needs_radians else item.pullback_amount
            overshoot_amount = math.radians(item.overshoot_amount) if needs_radians else item.overshoot_amount
            channel = int(item.channel) - 1

            note_start = item.note_range_start
            note_end = item.note_range_end + 1 # 0 - 128
            blocked_notes = [int(i) for i in item.blocked_notes.strip().split(",") if item.use_block_list]
            notes = [i for i in range(note_start, note_end) if i not in blocked_notes]

            if item.type == "hammer_composition":
                composition = HammerComposition(
                    midi_file,
                    item.object_prefix,
                    item.object_property,
                    pullback_amount,
                    notes,
                    overshoot_amount=overshoot_amount,
                    channel=channel,
                )
                composition.generate_keyframes()
            elif item.type == "movement_composition":
                composition = MovementComposition(
                    midi_file,
                    item.object_prefix,
                    item.object_property,
                    pullback_amount,
                    notes,
                    channel=channel,
                )
                composition.generate_keyframes()
            elif item.type == "light_composition":
                composition = LightComposition(
                    midi_file,
                    item.object_prefix,
                    item.light_object_property,
                    pullback_amount,
                    overshoot_amount,
                    notes,
                    mode="light" if item.light_object_property != "emission.emission" else "emission",
                    fade_effect=item.light_object_fade_effect,
                    channel=channel,
                )
                composition.generate_keyframes()
            elif item.type == "robotic_controller":
                instrument = RoboticController(
                    midi_file,
                    item.object_prefix,
                    item.robot_target_object_name,
                    pullback_amount,
                    item.robot_pullback_axis,
                    notes,
                    channel=channel,
                )
                instrument.generate_keyframes()

        return {'FINISHED'}

class VIEW_3D_PT_bmidi_panel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "bmidi"
    bl_label = "bmidi"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        box = layout.box()
        box.prop(scene, "bmidi_midi_file")

        if scene.bmidi_midi_file:
            midi_path = scene.bmidi_midi_file

            layout.separator()
            box.label(text="MIDI Information", icon="INFO")

            if midi_path:
                channel_ranges = get_midi_channel_ranges(midi_path)

                if channel_ranges:
                    for ch in sorted(channel_ranges):
                        n, z = channel_ranges[ch]
                        box.label(text=f"Channel {ch}: Notes {n}-{z}")
                else:
                    box.label(text="Error parsing midi file", icon="ERROR")
        else:
            box.label(text="No midi file selected")

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
        col.separator()
        col.operator("bmidi_items.duplicate_item", icon="DUPLICATE", text="")

        if scene.bmidi_items:
            item = scene.bmidi_items[scene.bmidi_active_item]

            layout.prop(item, "object_prefix", text="Object Prefix" if item.type != "robotic_controller" else "Control Object")

            if item.type != "robotic_controller":
                layout.prop(item, "object_property" if item.type not in ("light_instrument", "light_composition") else "light_object_property")
            else:
                layout.prop(item, "robot_target_object_name")
                layout.prop(item, "robot_pullback_axis")

            if item.type == "movement_composition":
                layout.prop(item, "pullback_amount", text="Final Amount")
            elif item.type == "light_composition":
                layout.prop(item, "pullback_amount", text="Initial Factor")
                layout.prop(item, "overshoot_amount", text="Final Factor")
            else:
                layout.prop(item, "pullback_amount")

            if item.type not in ("movement_composition", "light_composition", "robotic_controller"):
                layout.prop(item, "overshoot_amount")

            layout.prop(item, "note_range_start")
            layout.prop(item, "note_range_end")
            layout.prop(item, "use_block_list")

            if item.use_block_list:
                layout.prop(item, "blocked_notes")

            layout.separator()

            if item.type in ("light_instrument", "light_composition"):
                layout.prop(item, "light_object_fade_effect")

            layout.separator()
            layout.prop(item, "channel")

        layout.separator()
        layout.operator("bmidi.generate_keyframes", icon="MODIFIER")

def register():
    bpy.utils.register_class(BMIDI_Item)
    bpy.utils.register_class(BMIDI_UL_items)

    bpy.types.Scene.bmidi_items = bpy.props.CollectionProperty(
        type=BMIDI_Item
    )
    bpy.types.Scene.bmidi_active_item = bpy.props.IntProperty()
    bpy.types.Scene.bmidi_midi_file = bpy.props.StringProperty(
        name="MIDI File",
        subtype="FILE_PATH",
    )

    bpy.utils.register_class(VIEW_3D_PT_bmidi_panel)
    bpy.utils.register_class(VIEW_3D_OT_add_item)
    bpy.utils.register_class(VIEW_3D_OT_remove_item)
    bpy.utils.register_class(VIEW_3D_OT_duplicate_item)
    bpy.utils.register_class(VIEW_3D_OT_generate_keyframes)

def unregister():
    bpy.utils.unregister_class(BMIDI_UL_items)
    bpy.utils.unregister_class(VIEW_3D_PT_bmidi_panel)
    bpy.utils.unregister_class(VIEW_3D_OT_add_item)
    bpy.utils.unregister_class(VIEW_3D_OT_remove_item)
    bpy.utils.unregister_class(VIEW_3D_OT_duplicate_item)
    bpy.utils.unregister_class(VIEW_3D_OT_generate_keyframes)

if __name__ == "__main__":
    register()
