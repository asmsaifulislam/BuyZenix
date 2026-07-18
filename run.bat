@echo off
setlocal

REM Navigate to app directory
cd /d app
echo Current directory: %cd%

REM Check if virtual environment exists
if exist ".venv\Scripts\python.exe" (
    echo Virtual environment exists: .venv\Scripts\python.exe
    set PYTHON=.venv\Scripts\python.exe
) else (
    echo Creating virtual environment...
    python -m venv .venv
    set PYTHON=.venv\Scripts\python.exe
    if not exist "%PYTHON%" (
        echo ERROR: Failed to create virtual environment
        exit /b 1
    )
)

REM Set environment variable for SQLite development
SET RUN_LOCAL=1
echo Environment: RUN_LOCAL=%RUN_LOCAL%

REM Install dependencies
echo Installing dependencies...
"%PYTHON%" -m pip install -r "..\requirements.txt"
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)
echo ✓ Dependencies installed

REM Run migrations
echo.
echo Running database migrations...
"%PYTHON%" manage.py migrate
if errorlevel 1 (
    echo ERROR: Failed to run migrations
    exit /b 1
)
echo ✓ Migrations completed

REM Seed data
echo.
echo Seeding sample data...
"%PYTHON%" manage.py seed
if errorlevel 1 (
    echo ERROR: Failed to seed data
    exit /b 1
)
echo ✓ Sample data seeded

REM Create admin user
echo.
echo Creating admin user...
"%PYTHON%" manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@buyzenix.com', 'admin12345')"
if errorlevel 1 (
    echo Note: Admin user creation failed (may already exist)
)
echo ✓ Admin user created/verified

REM Display project information
echo.
echo ==========================================
echo ✅ Project setup complete!
echo ==========================================
echo.
echo 🌐 Storefront URL: http://127.0.0.1:8000/
echo 👤 Admin panel:    http://127.0.0.1:8000/admin/
echo 🔑 Admin credentials: admin / admin12345
echo.
echo 🚀 Starting Django development server...
echo.
echo 💡 Press Ctrl+C to stop the server
echo.
echo ==========================================

REM Start the server
echo Starting server...
"%PYTHON%" manage.py runserver 127.0.0.1:8000
