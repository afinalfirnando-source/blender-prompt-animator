@echo off
REM Blender Prompt Animator - Batch Render All Scripts
REM Run all generated Blender scripts in Blender background mode
set BLENDER_PATH="C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
set OUTPUT_DIR=%~dp0blender_output

echo === Batch Rendering All Animation Scripts ===
echo.

for %%f in ("%OUTPUT_DIR%\anim_*.py") do (
    echo Rendering: %%~nxf
    %BLENDER_PATH% --background --python "%%f"
    echo.
)

echo === Batch render complete! ===
echo Output files in: %OUTPUT_DIR%
echo.
pause
