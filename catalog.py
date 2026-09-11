import json
import os
import glob

output_dir = "blender_output"
metas = sorted(glob.glob(os.path.join(output_dir, "meta_*.json")))

print("=== Pond5 Animation Catalog ===")
print()

for i, mf in enumerate(metas, 1):
    with open(mf) as f:
        m = json.load(f)
    s = m["scene_spec"]
    render_mp4 = m.get("render_file", "N/A")
    prompt_short = m["prompt"][:70] + ("..." if len(m["prompt"]) > 70 else "")

    print(f"{i:2d}. {prompt_short}")
    print(f"    Frames: {s['total_frames']}, Res: {s['resolution'][0]}x{s['resolution'][1]}, FPS: {s['fps']}")
    print(f"    Tone: {s['tone']}, Template: {s['template']}, Easing: {s['easing']}, Cam: {s['camera']['animation_type']}")
    print(f"    Effects: bloom={s['bloom']}, dof={s['depth_of_field']}, particles={s['particle_effect']}")
    print(f"    Objects: {len(s['objects'])}, Lights: {len(s['lights'])}")
    print(f"    Script: {os.path.basename(m['script_file'])}")
    mf_base = os.path.basename(render_mp4) if render_mp4 else "--"
    print(f"    Render: {mf_base}")
    print()

print(f"=== Total: {len(metas)} animations cataloged ===")
