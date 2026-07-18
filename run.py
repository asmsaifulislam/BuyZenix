# Create a PowerShell script to run the project locally
# This script handles the setup process since PowerShell doesn't support bash syntax

# Change to app directory
Set-Location -LiteralPath "app"

# Create virtual environment
if (!(Test-Path -LiteralPath ".venv")) {
    python -m venv .venv
}

# Activate virtual environment and install dependencies
$appPath = "D:\BuyZenix\app"
. "$appPath\venv\scripts\activate.ps1"

# Install Python packages
pip install -r "D:\BuyZenix\requirements.txt"

# Set environment variable for local development
$env:RUN_LOCAL = "1"

# Run Django commands
python manage.py migrate
python manage.py seed
python manage.py createsuperuser

# Create a script file to run server in background
$runServerScript = @"
# Start Django development server
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])
"@"
Write-Host "Starting Django development server..."
" + ""
Execute-DynamicParameter -ScriptBlock {
    python manage.py runserver 127.0.0.1:8000
}

Write-Host "\nServer is running!"
Write-Host "Storefront: http://127.0.0.1:8000/"
Write-Host "Admin: http://127.0.0.1:8000/admin/ - admin/admin12345"
