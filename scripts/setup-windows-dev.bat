@echo off
echo Setting up NEPL LIMS local development environment for Windows...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js is not installed or not in PATH
    exit /b 1
)

REM Check if PostgreSQL is installed
psql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo PostgreSQL is not installed or not in PATH
    exit /b 1
)

echo Setting up backend...
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo Setting up database...
REM You need to create the database manually first
alembic upgrade head

cd ..\frontend
echo Setting up frontend...
if not exist node_modules (
    npm install
)

cd ..
echo Setup complete! Run start-all-windows.bat to start all services
pause
