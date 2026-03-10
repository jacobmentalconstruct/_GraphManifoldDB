@echo off
REM ============================================================
REM  Graph Manifold — Run
REM  Activates .venv and launches the app via module invocation.
REM ============================================================

if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found. Run setup_env.bat first.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python -m src.app %*
