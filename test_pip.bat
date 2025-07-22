@echo off
echo Testing Python and pip installation...
echo.

echo Testing python command:
python --version
if errorlevel 1 (
    echo Python not found with 'python' command
) else (
    echo Python found!
)

echo.
echo Testing py command:
py --version
if errorlevel 1 (
    echo Python not found with 'py' command
) else (
    echo Python found with py!
)

echo.
echo Testing pip:
pip --version
if errorlevel 1 (
    echo pip not found, trying python -m pip:
    python -m pip --version
    if errorlevel 1 (
        echo pip not working with python -m pip either
        echo Try: py -m pip --version
        py -m pip --version
    ) else (
        echo pip works with: python -m pip
    )
) else (
    echo pip works directly!
)

echo.
echo Recommended commands to try:
echo 1. python -m pip install pyinstaller
echo 2. py -m pip install pyinstaller
echo 3. pip install --user pyinstaller

echo.
pause
