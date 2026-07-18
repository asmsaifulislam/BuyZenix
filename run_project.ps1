#powershell
# Run the Django project locally using PowerShell with the virtual environment

$ErrorActionPreference = "Stop"

# Set the app directory path
$appDir = "app"
$venvPath = "$appDir\.venv\Scripts"

# First install dependencies using virtual environment pip
Write-Host "Installing dependencies..."
& "$venvPath\pip.exe" install -r "..\requirements.txt"

# Check if manage.py exists
if (Test-Path -LiteralPath "manage.py") {
    Write-Host "Running database migrations..."
    & "$venvPath\python.exe" manage.py migrate

    Write-Host "Seeding data..."
    & "$venvPath\python.exe" manage.py seed

    Write-Host "Setting RUN_LOCAL environment variable..."
    $env:RUN_LOCAL = "1"

    Write-Host "Creating superuser..."
    & "$venvPath\python.exe" manage.py createsuperuser -e "admin@buyzenix.com" --noinput

    Write-Host "\n"
    Write-Host ""
    Write-Host "Setup complete!"
    Write-Host ""
    Write-Host "Server is running at: http://127.0.0.1:8000/"
    Write-Host ""
    Write-Host "Storefront: http://127.0.0.1:8000/"
    Write-Host "Admin panel: http://127.0.0.1:8000/admin/ - admin/admin12345"
    Write-Host ""
    Write-Host "Dropping into interactive shell..."

    # Start the Django server (run in interactive mode)
    & "$venvPath\python.exe" manage.py runserver 127.0.0.1:8000 --noreload
} else {
    Write-Host "manage.py not found in current directory."
    Write-Host "Please make sure you're in the correct directory."
    exit 1
}
