# Blender Prompt Animator

## Quick Start
```bash
# Install Python 3.11+
pip install -r requirements.txt

# Generate animation from prompt
python blender_prompt_animator.py "red rotating cube, 5 seconds, 4k, 30fps, render"

# Generate all Pond5 animations
python blender_prompt_animator.py --all --file pond5_seamless.txt --ci

# Render generated script in Blender
blender --background --python "blender_output/anim_XXX.py"
```

## Requirements
- Python 3.11+ (stdlib only, no pip packages needed)
- Blender 4.2+ (for rendering)
- No external dependencies

## Documentation
- [EXAMPLES.md](EXAMPLES.md) — Full feature documentation
- [GITHUB_CI.md](GITHUB_CI.md) — GitHub Actions CI setup
- [POND5_LISTINGS.md](POND5_LISTINGS.md) — Pond5 listing templates

## VS Code Integration
- `Ctrl+Shift+P` → `Tasks: Run Task` → `Blender: Generate Animation from Prompt`
- `Ctrl+Shift+B` → Blender: Start (launch Blender directly)
- `F5` → Blender: Run Script
