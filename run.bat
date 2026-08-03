@echo off
title MACR - Multi-Agent Code Review System
color 0A
set PYTHONPATH=C:\Users\Ananya\Downloads\MACR\src
set PROJECT_DIR=C:\Users\Ananya\Downloads\MACR

:menu
cls
echo.
echo  =====================================================
echo   MACR - Multi-Agent Code Review System
echo  =====================================================
echo.
echo   [1]  Review samples/test.py  (No Memory)
echo   [2]  Review samples/test.py  (With Memory)
echo   [3]  Run Metrics Dashboard (evaluate.py)
echo   [4]  Run Unit Tests
echo   [5]  Open Last Report
echo   [6]  Review a Custom File
echo   [7]  Start Web UI (FastAPI)
echo   [0]  Exit
echo.
set /p choice=  Enter your choice: 

if "%choice%"=="1" goto review_no_memory
if "%choice%"=="2" goto review_with_memory
if "%choice%"=="3" goto evaluate
if "%choice%"=="4" goto tests
if "%choice%"=="5" goto open_report
if "%choice%"=="6" goto custom_file
if "%choice%"=="7" goto start_ui
if "%choice%"=="0" goto exit
goto menu

:review_no_memory
cls
echo.
echo  Running review WITHOUT memory...
echo  -----------------------------------------------
cd /d %PROJECT_DIR%
python -W ignore src/cli/main.py samples/test.py --output report_no_memory.md --no-memory --verbose
echo.
echo  Done! Report saved to: report_no_memory.md
pause
goto menu

:review_with_memory
cls
echo.
echo  Running review WITH memory (FAISS)...
echo  -----------------------------------------------
cd /d %PROJECT_DIR%
python -W ignore src/cli/main.py samples/test.py --output report_with_memory.md --verbose
echo.
echo  Done! Report saved to: report_with_memory.md
pause
goto menu

:evaluate
cls
echo.
echo  Running Metrics Dashboard...
echo  -----------------------------------------------
cd /d %PROJECT_DIR%
python -W ignore scripts/evaluate.py samples/test.py
echo.
pause
goto menu

:tests
cls
echo.
echo  Running Unit Tests...
echo  -----------------------------------------------
cd /d %PROJECT_DIR%
python -m pytest tests/ -v -W ignore::FutureWarning
echo.
pause
goto menu

:open_report
cls
echo.
echo  Opening last report...
if exist "%PROJECT_DIR%\report_with_memory.md" (
    start %PROJECT_DIR%\report_with_memory.md
) else if exist "%PROJECT_DIR%\report_no_memory.md" (
    start %PROJECT_DIR%\report_no_memory.md
) else (
    echo  No report found. Run a review first!
)
pause
goto menu

:custom_file
cls
echo.
set /p filepath=  Enter full path to your Python file: 
echo.
echo  Running review on: %filepath%
echo  -----------------------------------------------
cd /d %PROJECT_DIR%
python -W ignore src/cli/main.py "%filepath%" --output custom_report.md --no-memory --verbose
echo.
echo  Done! Report saved to: custom_report.md
start %PROJECT_DIR%\custom_report.md
pause
goto menu

:start_ui
cls
echo.
echo  Starting MACR Web UI on http://localhost:8000
echo  Press Ctrl+C to stop the server
echo  -----------------------------------------------
cd /d %PROJECT_DIR%
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
echo.
pause
goto menu

:exit
echo.
echo  Goodbye!
exit
