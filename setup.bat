@echo off
echo ========================================
echo Match Predictor - Setup Script
echo ========================================
echo.

echo Step 1: Checking PostgreSQL...
pg_isready -U predictor >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PostgreSQL is not running or not accessible.
    echo Please start PostgreSQL service and try again.
    echo.
    echo To start PostgreSQL on Windows:
    echo   net start postgresql
    echo.
    pause
    exit /b 1
)
echo PostgreSQL is running.
echo.

echo Step 2: Setting up Backend...
cd backend
if not exist node_modules (
    echo Installing backend dependencies...
    call npm install
) else (
    echo Backend dependencies already installed.
)

echo.
echo Generating Prisma client...
call npx prisma generate

echo.
echo Running database migrations...
call npx prisma migrate dev --name init

echo.
echo Seeding database...
call npm run prisma:seed

cd ..
echo Backend setup complete.
echo.

echo Step 3: Setting up Frontend...
cd frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
) else (
    echo Frontend dependencies already installed.
)
cd ..
echo Frontend setup complete.
echo.

echo Step 4: Setting up ML Service...
cd ml
if not exist .venv (
    echo Creating Python virtual environment...
    python -m venv .venv
    echo Installing ML dependencies...
    call .venv\Scripts\activate
    pip install -r requirements.txt
) else (
    echo ML dependencies already installed.
)
cd ..
echo ML service setup complete.
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the application, open 3 terminal windows:
echo.
echo Terminal 1 - Backend:
echo   cd backend
echo   npm run start:dev
echo.
echo Terminal 2 - ML Service:
echo   cd ml
echo   .venv\Scripts\activate
echo   uvicorn app.main:app --reload --port 8000
echo.
echo Terminal 3 - Frontend:
echo   cd frontend
echo   npm run dev
echo.
echo Then visit: http://localhost:3000
echo.
pause