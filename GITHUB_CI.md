# GitHub CI Setup - Render Animations di GitHub Actions

## Apa ini?
Workflow GitHub Actions yang **meng-render animasi Blender di cloud** tanpa membebani PC lokal. Cocok untuk batch rendering 20+ animasi sekaligus.

## Cara Pakai

### 1. Push ke GitHub
```bash
git init
git remote add origin https://github.com/YOUR_USERNAME/prompt-animator.git
git add .
git commit -m "Add Blender Prompt Animator + Pond5 animations"
git push -u origin main
```

### 2. Jalankan Workflow
- Buka repo di GitHub
- Buka tab "Actions"
- Pilih workflow "Render Animations"
- Klik "Run workflow" ↗
- Pilih resolusi & engine (opsional)
- Tunggu sampai selesai (~30-60 menit untuk 20 animasi)

### 3. Download Hasil
- Setiap render muncul sebagai artifact terpisah
- Atau download semua sekaligus via "Artifacts"

---

## Workflow Details

### Mode CI (otomatis aktif)
| Setting | Local | CI Mode |
|---------|-------|---------|
| Render Engine | Cycles (128 samples) | Eevee |
| Resolution | 4K (3840x2160) | 1080p (1920x1080) |
| FPS | 60fps | 30fps (auto-downgrade) |
| Duration | 10s | 10s |

### Parallel Rendering
- 20 animasi dirender secara **parallel** (maks 4 job sekaligus)
- Masing-masing job ~5-15 menit dengan Eevee
- Total completion: ~45 menit

### Files di workflow
```
.blender_prompt_animator/
├── .github/workflows/render.yml   # GitHub Actions workflow
├── blender_prompt_animator.py     # Core tool
├── pond5_seamless.txt             # 20 prompt batch
├── pond5_prompts.txt              # 20 prompt original
├── POND5_LISTINGS.md              # Template listing jual
├── EXAMPLES.md                    # Dokumentasi lengkap
├── catalog.py                     # Generate katalog metadata
├── render_all.bat                 # Local batch render
├── animate.bat                    # Quick launcher
├── requirements.txt               # Python dependencies
├── README.md                      # Quick start
└── blender_output/                # Generated scripts + renders
    ├── anim_*.py                  # Blender scripts
    ├── meta_*.json                # Metadata
    └── render_*.mp4              # Video output
```

---

## Cara Kerja Workflow

1. **Job `generate-scripts`**:
   - Install Blender 4.2
   - Run `--all --ci` untuk generate 20 script
   - Upload semua script sebagai artifact

2. **Job `render-animations` (parallel x20)**:
   - Download script artifact
   - Pilih 1 script berdasarkan matrix index
   - Render di Blender background mode
   - Upload video sebagai artifact

---

## Custom Render Settings

Bisa diubah di GitHub Actions "Run workflow" dialog:
- **Resolution**: 1080p atau 720p
- **Engine**: Eevee (cepat) atau Cycles (high quality, lambat)
- **Max animations**: Batasi berapa banyak yang mau dirender

---

## Local Testing (sebelum push)

```bash
# Generate all scripts in CI mode (tanpa render)
python blender_prompt_animator.py --all --file pond5_seamless.txt --ci

# Render satu secara lokal
blender --background --python "blender_output\anim_XXX.py"

# Render semua secara lokal (butuh Blender terpasir)
render_all.bat
```

---

## Estimated GitHub Actions Costs
- Gratis untuk public repo (2000 menit/bulan)
- 20 animasi x ~12 menit = ~240 menit
- Cukup untuk sebulan dengan sisa kuota 1760 menit
