"""
PowerShell script to run BuyZenix locally
Follows the instructions from README.md
"""

# Navigate to the app directory
cd app
Write-Host "Current directory: $(Get-Location)"

# Check if Python is available
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "Python found"
} else {
    Write-Host "ERROR: Python not found. Please install Python."
    exit 1
}

# Create virtual environment if not exists
if (Test-Path -LiteralPath ".\.venv") {
    Write-Host "Virtual environment already exists ✓"
} else {
    Write-Host "Creating virtual environment..."
    python -m venv .\.venv
    Write-Host "Virtual environment created"
}

# Check if python.exe exists in virtual environment
$PythonExe = ".\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $PythonExe)) {
    Write-Host "ERROR: Python executable not found at $PythonExe"
    exit 1
}

Write-Host "Python executable: $PythonExe"

# Install dependencies
Write-Host "Installing dependencies..."
& $PythonExe -m pip install -r "..\requirements.txt"

# Set environment variable for SQLite development
$env:RUN_LOCAL = "1"
Write-Host "Environment: RUN_LOCAL=$env:RUN_LOCAL"

# Run database migrations
Write-Host "Running database migrations..."
& $PythonExe manage.py migrate

# Seed sample data
Write-Host "Seeding sample data..."
& $PythonExe manage.py seed

# Create superuser
Write-Host "Creating superuser..."
& $PythonExe manage.py createsuperuser

# Display project info
Write-Host ""
Write-Host "=========================================="
Write-Host "✅ Project setup complete!"
Write-Host "=========================================="
Write-Host ""
Write-Host "Storefront: http://127.0.0.1:8000/"
Write-Host "Admin:      http://127.0.0.1:8000/admin/  →  admin/admin12345"
Write-Host ""
Write-Host "Starting Django development server..."
Write-Host ""
Write-Host "💡 Press Ctrl+C to stop"
Write-Host ""

# Start Django server
& $PythonExe manage.py runserver 127.0.0.1:8000
