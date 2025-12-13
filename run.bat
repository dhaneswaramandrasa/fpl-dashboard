@echo off

echo Starting FPL Dashboard...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo Dependencies installed
echo.

REM Run Streamlit
echo Launching FPL Dashboard...
echo Dashboard will open in your browser at http://localhost:8501
echo.
echo Press Ctrl+C to stop the dashboard
echo.

streamlit run app.py

pause
