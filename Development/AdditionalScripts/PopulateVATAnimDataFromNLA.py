import bpy

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

START_FRAME = 1
GAP_FRAMES = 0

USE_ACTIVE_OBJECT_ONLY = True
CLEAR_EXISTING_VAT_DATA = True

# If True, strip names use the Action name when available.
# If False, strip names use the NLA strip name.
USE_ACTION_NAME = True


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def get_target_objects():
    if USE_ACTIVE_OBJECT_ONLY:
        obj = bpy.context.object
        return [obj] if obj else []

    return [obj for obj in bpy.context.selected_objects if obj.animation_data]


def get_nla_strips(obj):
    anim_data = obj.animation_data
    if not anim_data:
        return []

    strips = []

    for track_index, track in enumerate(anim_data.nla_tracks):
        if track.mute:
            continue

        for strip_index, strip in enumerate(track.strips):
            if strip.mute:
                continue

            strips.append({
                "object": obj,
                "track": track,
                "strip": strip,
                "track_index": track_index,
                "strip_index": strip_index,
                "original_start": strip.frame_start,
            })

    # Stable order based on current NLA layout
    strips.sort(key=lambda x: (
        x["original_start"],
        x["track_index"],
        x["strip_index"],
        x["object"].name
    ))

    return strips


def clear_vat_anim_data(scene):
    data = scene.vat_anim_data

    # CollectionProperty normally supports clear() in modern Blender.
    if hasattr(data, "clear"):
        data.clear()
    else:
        while len(data) > 0:
            data.remove(0)


def add_vat_entry(scene, name, start_frame, end_frame):
    entry = scene.vat_anim_data.add()
    entry.name = name
    entry.start_frame = int(start_frame)
    entry.end_frame = int(end_frame)
    return entry


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

scene = bpy.context.scene
objects = get_target_objects()

if not objects:
    raise RuntimeError("No valid animated object found.")

all_strips = []

for obj in objects:
    all_strips.extend(get_nla_strips(obj))

if not all_strips:
    raise RuntimeError("No usable NLA strips found.")

if CLEAR_EXISTING_VAT_DATA:
    clear_vat_anim_data(scene)

cursor = START_FRAME

for item in all_strips:
    obj = item["object"]
    strip = item["strip"]

    # Keep the visible timeline duration exactly as currently authored.
    duration = strip.frame_end - strip.frame_start

    new_start = cursor
    new_end = cursor + duration

    strip.frame_start = new_start
    strip.frame_end = new_end

    name_source = strip.action.name if USE_ACTION_NAME and strip.action else strip.name

    # Optional: prefix object name if processing multiple objects.
    if not USE_ACTIVE_OBJECT_ONLY:
        clip_name = f"{obj.name}_{name_source}"
    else:
        clip_name = name_source

    # VAT ranges are usually integer frame ranges.
    # End frame is rounded down from strip.frame_end.
    add_vat_entry(
        scene,
        clip_name,
        round(strip.frame_start),
        round(strip.frame_end)
    )

    cursor = new_end + GAP_FRAMES

scene.frame_start = START_FRAME
scene.frame_end = round(cursor - GAP_FRAMES)

print("Sequential NLA layout complete.")
print(f"Created {len(scene.vat_anim_data)} VAT animation entries.")
print(f"Timeline range: {scene.frame_start} - {scene.frame_end}")