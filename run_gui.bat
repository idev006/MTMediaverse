@echo off
REM Run MediaVerse Desktop GUI
REM Requires: pip install PySide6

set VENV_PATH=D:\dev\MTMediaverse\Scripts
set PROJECT_ROOT=D:\dev\MTMediaverse

echo === MediaVerse Desktop GUI ===

REM Activate venv
call %VENV_PATH%\activate.bat

cd %PROJECT_ROOT%

REM Run GUI
python -c "from app.gui.main_window import run_gui; run_gui()"

pause
