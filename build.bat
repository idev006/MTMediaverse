@echo off
REM Build script for MediaVerse
REM Supports PyArmor obfuscation + PyInstaller packaging

setlocal

set VENV_PATH=D:\dev\MTMediaverse\Scripts
set PROJECT_ROOT=D:\dev\MTMediaverse

echo === MediaVerse Build Script ===

REM Activate venv
call %VENV_PATH%\activate.bat

REM Step 1: Run tests first
echo.
echo [1/4] Running tests...
cd %PROJECT_ROOT%
pytest tests/ -v --tb=short
if errorlevel 1 (
    echo Tests failed! Aborting build.
    exit /b 1
)

REM Step 2: Clean previous builds
echo.
echo [2/4] Cleaning previous builds...
rmdir /s /q "%PROJECT_ROOT%\dist" 2>nul
rmdir /s /q "%PROJECT_ROOT%\build" 2>nul
rmdir /s /q "%PROJECT_ROOT%\dist_obfuscated" 2>nul

REM Step 3: Obfuscate with PyArmor (optional)
echo.
echo [3/4] Obfuscating with PyArmor...
set OBFUSCATE=%1
if "%OBFUSCATE%"=="--obfuscate" (
    pyarmor gen --output dist_obfuscated app\
    if errorlevel 1 (
        echo PyArmor obfuscation failed!
        exit /b 1
    )
    echo Obfuscation complete.
) else (
    echo Skipping obfuscation. Use --obfuscate flag to enable.
)

REM Step 4: Build with PyInstaller
echo.
echo [4/4] Building with PyInstaller...
pyinstaller build.spec --noconfirm
if errorlevel 1 (
    echo PyInstaller build failed!
    exit /b 1
)

echo.
echo === Build Complete! ===
echo Output: %PROJECT_ROOT%\dist\MediaVerse\

endlocal
