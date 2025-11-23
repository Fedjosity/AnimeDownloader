@echo off
cd /d "%~dp0"

echo AnimeDownloader Setup Script
echo ================================================

set PYTHON_EXE=
for %%I in (python py) do (
    where %%I >nul 2>&1
    if not errorlevel 1 set PYTHON_EXE=%%I
)

if "%PYTHON_EXE%"=="" (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo Using Python interpreter: %PYTHON_EXE%
echo.

if not exist "venv" (
    echo Creating virtual environment...
    "%PYTHON_EXE%" -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created.
) else (
    echo Virtual environment found.
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment.
    pause
    exit /b 1
)

set PYTHON_EXE=python

if not exist "requirements.txt" (
    echo Error: requirements.txt not found.
    pause
    exit /b 1
)

echo Installing required packages...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt >nul 2>&1

if errorlevel 1 (
    echo Error: Failed to install requirements.
    pause
    exit /b 1
)

echo Requirements installed.

findstr /i "playwright" requirements.txt >nul
if not errorlevel 1 (
    echo Installing Playwright browser.
    python -m playwright install chromium >nul 2>&1
)

if not exist "main.py" (
    echo Error: main.py not found.
    pause
    exit /b 1
)

echo Starting AnimeDownloader.
echo ================================================
python main.py