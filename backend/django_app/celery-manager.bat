@echo off
echo OCH Platform - Celery Management Script
echo ========================================

:menu
echo.
echo Choose an option:
echo 1. Start Celery Worker
echo 2. Start Celery Beat (Scheduler)
echo 3. Start Flower (Monitoring)
echo 4. Check Redis Status
echo 5. Install Requirements
echo 6. Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto worker
if "%choice%"=="2" goto beat
if "%choice%"=="3" goto flower
if "%choice%"=="4" goto redis_status
if "%choice%"=="5" goto install
if "%choice%"=="6" goto exit

echo Invalid choice. Please try again.
goto menu

:worker
echo Starting Celery Worker...
echo Press Ctrl+C to stop
celery -A core worker --loglevel=info --pool=solo
goto menu

:beat
echo Starting Celery Beat Scheduler...
echo Press Ctrl+C to stop
celery -A core beat --loglevel=info
goto menu

:flower
echo Starting Flower Monitoring...
echo Open http://localhost:5555 in your browser
echo Press Ctrl+C to stop
celery -A core flower
goto menu

:redis_status
echo Checking Redis Status...
docker ps | findstr redis-server
if %errorlevel%==0 (
    echo Redis is running!
    docker exec redis-server redis-cli ping
) else (
    echo Redis is not running. Starting Redis...
    docker run -d --name redis-server -p 6379:6379 redis:alpine
)
goto menu

:install
echo Installing Python requirements...
pip install -r requirements.txt
echo Requirements installed!
pause
goto menu

:exit
echo Goodbye!
exit