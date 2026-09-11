@echo off
REM Blender Prompt Animator - Quick Launcher
REM Usage: animate.bat "your prompt here" [--render]
python "%~dp0blender_prompt_animator.py" --prompt "%*"
