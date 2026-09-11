# Blender Prompt Animator v2.0 - Dokumentasi Lengkap

## Cara Kerja
Sistem menerima **text prompt** (Bahasa Indonesia atau Inggris) → otomatis generate **script Blender Python (bpy)** → (opsional) **render ke video MP4**.

---

## Fitur

### Basic
| Kategori | Fitur | Contoh Prompt |
|----------|-------|---------------|
| **Objek** | cube, sphere, cylinder, cone, torus, monkey, text, plane, planet, ring | `red cube`, `biru bola`, `yellow monkey` |
| **Warna** | 25+ warna ID + EN | `merah`, `navy blue`, `golden`, `abu-abu` |
| **Durasi** | seconds/detik, fps kustom | `5 seconds`, `3 detik`, `30fps` |
| **Resolusi** | 720p, 1080p, 4k, custom WxH | `4k`, `1080p`, `1920x1080` |
| **Render Engine** | cycles, eevee, wireframe | `cycles`, `eevee` |

### Material Canggih
| Type | Keywords | Effect |
|------|----------|--------|
| Glass | glass, kaca, transparent | Refraction, IOR 1.45 |
| Metallic | metallic, metal, logam, gold | Metallic 1.0, roughness low |
| Emission | emission, glow, cahaya | Self-illuminating |
| Neon | neon | Emission + glossy |
| Glossy | glossy, mirror, cermin | High specular |
| Principled | (default) | Standard PBR |

Contoh: `glass red sphere`, `metallic gold cube`, `neon blue torus`

### Animasi (per-objek)
| Type | Keywords | Motion |
|------|----------|--------|
| Rotate | rotate, berputar, spin | Full 360° + bounce |
| Bounce | bounce, melompat | Up-down + squash/stretch |
| Float | float, mengapung | Sine wave + rotation |
| Move | move, glide | Side-to-side sine |
| Scale | scale, besar kecil | Pulsating scale |
| Orbit | orbit, melingkari | Circular path |
| Patrol | patrol | Sine wave movement |

### Kamera Cerdas
| Mode | Keywords | Behavior |
|------|----------|----------|
| Orbit (default) | (auto) | Gentle arc around scene |
| Dolly | dolly | Move toward subject |
| Zoom | zoom, memium | Focal length change |
| Pan | pan | Orbit around center |
| Follow | follow, mengikuti | Track objects (TRACK_TO constraint) |
| Positions | close up, wide, overhead, low angle | Preset camera positions |

### Tone (Emotional)
| Tone | Effects |
|------|---------|
| romantic | Warm bg, dolly camera, bloom, DoF |
| dramatic | Dark bg, high contrast, 2-point lighting |
| eerie | Deep blue bg, single sun, bloom, dolly |
| dreamy | Soft pastel bg, zoom camera, bloom, DoF |
| epic | Blue bg, bright sun, orbit camera, stars |

### Scene Templates
| Template | Effects |
|----------|---------|
| product_showcase | 3-point lighting, dolly, DoF 4.0 |
| space_epic | Single sun, stars particles, orbit |
| nature_doc | Sun + area light, follow camera |
| abstract | Point lights, pan camera, bloom, elastic |
| cinematic | Dolly, 2-point, DoF, dramatic bg |

### Post-Processing
| Effect | Keywords |
|--------|----------|
| Bloom | bloom, glow, bercahaya |
| Depth of Field | depth of field, dof, bokeh |
| Snow | snow, salju |
| Sparks | spark, spark |
| Stars | star, bintang |

### Easing
| Type | Keywords | Curve |
|------|----------|-------|
| ease (default) | smooth, halus | Auto-in-out |
| linear | linear, linier | Linear |
| bounce | bounce, memantul | Bezier |
| elastic | elastic, elastik | Auto-clamped |
| overshoot | overshoot, snap | Ease-in-out + limits |

---

## Contoh Prompt (Complete)

```
# Basic
red rotating cube, 5 seconds, 24fps
kubus merah berputar, latar biru, 3 detik

# Materials
glass transparent blue sphere, 8 seconds
metallic gold torus with neon glow, 6 seconds

# Multi-objek
blue cube orbiting yellow sphere, studio lighting
merah cube dan biru bola, 5 detik, latar hitam

# Tone + Template
romantic product showcase: glass red rose, warm golden lighting, DoF, bloom
epic space scene: metallic planet, glass rings, stars, cinematic, follow camera
eerie haunted house, ghostly sphere floating, dark, bloom, elastic easing

# Full cinematic
dreamy romantic scene: floating spheres, golden hour, 6 seconds, 4k, 30fps,
  bloom, depth of field, bounce easing, cinematic
```

---

## Cara Pakai

### 1. Command Line
```bash
cd C:\Users\ADVAN\blender_prompt_animator
python blender_prompt_animator.py "prompt..."                           # generate script
python blender_prompt_animator.py --prompt "prompt..." --render         # generate + render
python blender_prompt_animator.py --file prompt.txt --render            # dari file
```

### 2. VS Code
- `Ctrl+Shift+P` → `Tasks: Run Task` → `Blender: Generate Animation from Prompt`
- Atau `Ctrl+Shift+B` untuk Blender: Start langsung

### 3. Quick Launcher
```bat
animate.bat "prompt..." --render
```

### Output
```
blender_output/
├── anim_XXX.py        ← Script Blender (bisa dibuka di Blender)
├── anim_XXX.blend     ← File .blend
├── render_XXX.mp4     ← Video hasil render (--render)
└── meta_XXX.json      ← Metadata lengkap
```

---

## Penggunaan via Kilo Chat
Berikan langsung text prompt di chat ini. Saya akan:
1. Generate script Blender
2. Jalankan render di Blender (jika ada `--render` atau minta render)
3. Laporkan hasil + metadata
