COMPOSITION_TYPES = ("hammer_composition", "movement_composition", "light_composition", "robotic_composition")

def draw_note_controls(layout, item):
    layout.prop(item, "use_note")

    if item.use_note:
        layout.prop(item, "note")

def draw_note_range_controls(layout, item):
    layout.prop(item, "note_range_start")
    layout.prop(item, "note_range_end")

def draw_channel_controls(layout, item, scene):
    if scene.bmidi_midi_file:
        layout.separator()
        layout.prop(item, "channel")

def draw_affected_object_controls(layout, item):
    layout.prop(item, "affects_object", text="Affects Objects" if item.type in COMPOSITION_TYPES else "Affects Object")

    if item.affects_object:
        layout.prop(item, "affected_object_name", text="Object Prefix" if item.type in COMPOSITION_TYPES else "Object")
        layout.prop(item, "affected_object_property")
        layout.prop(item, "affected_amount")
