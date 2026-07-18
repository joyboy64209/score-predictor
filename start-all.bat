@echo off
echo ========================================
echo Match Predictor - Starting All Services
echo ========================================
echo.

REM Check if PostgreSQL is running
echo Checking PostgreSQL...
pg_isready -U predictor >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PostgreSQL is not running.
    echo Please start PostgreSQL first:
    echo   net start postgresql
    echo.
    pause
    exit /b 1
)
echo PostgreSQL is running.
echo.

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found.
    echo Please run setup.bat first or copy .env.example to .env
    echo.
    pause
    exit /b 1
)

REM Start Backend Service
echo Starting Backend Service (port 3001)...
start "Match Predictor - Backend" cmd /k "cd backend && npm run start:dev"
timeout /t 3 /nobreak >nul

REM Start Frontend Service
echo Starting Frontend Service (port 3000)...
start "Match Predictor - Frontend" cmd /k "cd frontend && npm run dev"
timeout /t 3 /nobreak >nul

REM Start ML Service (optional - may fail if Python dependencies not installed)
echo Starting ML Service (port 8000)...
start "Match Predictor - ML Service" cmd /k "cd ml && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000" || echo ML Service failed to start - Python dependencies may need to be installed

echo.
echo ========================================
echo All services starting...
echo ========================================
echo.
echo Backend:  http://localhost:3001
echo Frontend: http://localhost:3000
echo ML:       http://localhost:8000 (may not be running if Python dependencies failed)
echo.
echo Default login: admin@predictor.io / admin123
echo.
echo Close this window or press any key to exit...
pause >nul