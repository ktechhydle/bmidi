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
from src.instrument import HammerInstrument, MovementInstrument, get_midi_channel_ranges
from src.composition import HammerComposition, MovementComposition

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
COMPOSITION_TYPES = ("hammer_composition", "movement_composition")

class BMIDI_Item(bpy.types.PropertyGroup):
    type: bpy.props.EnumProperty(
        name="Type",
        items=[
            ("hammer_instrument", "Hammer Instrument", ""),
            ("movement_instrument", "Movement Instrument", ""),
            ("hammer_composition", "Hammer Composition", ""),
            ("movement_composition", "Movement Composition", ""),
        ]
    )
    object_name: bpy.props.StringProperty(name="Object")
    object_property: bpy.props.EnumProperty(
        name="Property",
        items=OBJECT_PROPERTIES
    )
    initial_position: bpy.props.FloatProperty(name="Initial")
    pullback_position: bpy.props.FloatProperty(name="Pullback")
    overshoot_amount: bpy.props.FloatProperty(name="Overshoot")
    use_note: bpy.props.BoolProperty(name="Use Note")
    note: bpy.props.IntProperty(
        name="Note",
        min=0,
        max=127,
        default=0
    )
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
    channel: bpy.props.IntProperty(
        name="Channel",
        min=1,
        max=16,
        default=1
    )
    affects_object: bpy.props.BoolProperty(name="Affects Object")
    affected_object_name: bpy.props.StringProperty(name="Object")
    affected_object_property: bpy.props.EnumProperty(
        name="Property",
        items=OBJECT_PROPERTIES
    )
    affected_amount: bpy.props.FloatProperty(name="Amount")

class BMIDI_UL_items(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon,
        active_data, active_propname, index
    ):
        layout.prop(item, "object_name", text="", emboss=False, icon="SOUND")

class VIEW_3D_OT_add_item(bpy.types.Operator):
    """
    Adds a new item
    """
    bl_idname = "bmidi_items.add_item"
    bl_label = "Add Item"

    def execute(self, context):
        context.scene.bmidi_items.add()
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
        context.scene.frame_set(-1)
        midi_file = context.scene.bmidi_midi_file

        if not midi_file:
            self.report({'ERROR'}, "No MIDI file selected")
            return {'CANCELLED'}

        for item in context.scene.bmidi_items:
            needs_radians = True if item.object_property in ROTATION_PROPERTIES else False

            pullback_position = math.radians(item.pullback_position) if needs_radians else item.pullback_position
            initial_position = math.radians(item.initial_position) if needs_radians else item.initial_position
            overshoot_amount = math.radians(item.overshoot_amount) if needs_radians else item.overshoot_amount
            affected_object = (
                item.affected_object_name,
                item.affected_object_property,
                math.radians(item.affected_amount) if item.affected_object_property in ROTATION_PROPERTIES else item.affected_amount
            ) if item.affects_object else None

            if item.type == "hammer_instrument":
                instrument = HammerInstrument(
                    midi_file,
                    item.object_name,
                    item.object_property,
                    initial_position,
                    pullback_position,
                    overshoot_amount=overshoot_amount,
                    note=item.note if item.use_note else None,
                    channel=item.channel - 1,
                    affected_object=affected_object,
                )
                instrument.generate_keyframes()
            elif item.type == "movement_instrument":
                instrument = MovementInstrument(
                    midi_file,
                    item.object_name,
                    item.object_property,
                    initial_position,
                    pullback_position,
                    note=item.note if item.use_note else None,
                    channel=item.channel - 1,
                )
                instrument.generate_keyframes()
            elif item.type == "hammer_composition":
                composition = HammerComposition(
                    midi_file,
                    item.object_name,
                    item.object_property,
                    initial_position,
                    pullback_position,
                    start_range=item.note_range_start,
                    end_range=item.note_range_end + 1, # 0 - 128
                    overshoot_amount=overshoot_amount,
                    affected_object=affected_object,
                    channel=item.channel - 1,
                )
                composition.generate_keyframes()
            elif item.type == "movement_composition":
                composition = MovementComposition(
                    midi_file,
                    item.object_name,
                    item.object_property,
                    initial_position,
                    pullback_position,
                    start_range=item.note_range_start,
                    end_range=item.note_range_end + 1, # 0 - 128
                    channel=item.channel - 1,
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

        if scene.bmidi_items:
            item = scene.bmidi_items[scene.bmidi_active_item]
            layout.prop(item, "type")
            layout.prop(item, "midi_file")
            layout.prop(item, "object_name", text="Object" if item.type in COMPOSITION_TYPES else "Object Prefix") # if compositions is selected change the label
            layout.prop(item, "object_property")
            layout.prop(item, "initial_position")
            layout.prop(item, "pullback_position", text="Final" if item.type == "movement_instrument" or item.type == "movement_composition" else "Pullback")

            if item.type not in ("movement_instrument", "movement_composition"):
                layout.prop(item, "overshoot_amount")

            if item.type in COMPOSITION_TYPES:
                layout.prop(item, "note_range_start")
                layout.prop(item, "note_range_end")
                layout.prop(item, "channel")

            layout.separator()

            if item.type not in COMPOSITION_TYPES:
                layout.prop(item, "use_note")

                if item.use_note:
                    layout.prop(item, "note")
                    layout.prop(item, "channel")

            if item.type != "movement_instrument":
                layout.prop(item, "affects_object", text="Affects Objects" if item.type in COMPOSITION_TYPES else "Affects Object")

                if item.affects_object:
                    layout.prop(item, "affected_object_name", text="Object Prefix" if item.type in COMPOSITION_TYPES else "Object")
                    layout.prop(item, "affected_object_property")
                    layout.prop(item, "affected_amount")

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
    bpy.utils.register_class(VIEW_3D_OT_generate_keyframes)

def unregister():
    bpy.utils.unregister_class(BMIDI_UL_items)
    bpy.utils.unregister_class(VIEW_3D_PT_bmidi_panel)
    bpy.utils.unregister_class(VIEW_3D_OT_add_item)
    bpy.utils.unregister_class(VIEW_3D_OT_remove_item)
    bpy.utils.unregister_class(VIEW_3D_OT_generate_keyframes)

if __name__ == "__main__":
    register()
