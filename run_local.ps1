$ErrorActionPreference = "Stop"

# Change to app directory
Set-Location -LiteralPath "app"

# Check if virtual environment exists
if (!(Test-Path -LiteralPath ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

# Activate virtual environment and activate it
$venvPath = "..\.venv"
& "$venvPath\Scripts\Activate.ps1"

# Install dependencies from correct path
Write-Host "Installing dependencies..."
& pip install -r "..\requirements.txt"

# Set environment variable for SQLite
$env:RUN_LOCAL = "1"

# Run Django commands
Write-Host "Running migrations..."
python manage.py migrate

Write-Host "Seeding data..."
python manage.py seed

Write-Host "\nSetup complete!"
Write-Host "Storefront: http://127.0.0.1:8000/"
Write-Host "Admin panel: http://127.0.0.1:8000/admin/ - admin/admin12345"
Write-Host "\nStarting Django development server...\n"

# Run the Django development server
python manage.py runserver 127.0.0.1:8000
