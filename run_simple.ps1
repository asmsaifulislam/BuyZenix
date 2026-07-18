# PowerShell script to run BuyZenix locally (Simple and tested approach)

# Navigate to app directory
cd app
Write-Host "Current directory: $(Get-Location)"

# Check if virtual environment exists and has Python
if (Test-Path -LiteralPath ".venv\Scripts\python.exe") {
    $Python = ".venv\Scripts\python.exe"
    Write-Host "✓ Found Python in virtual environment: $Python"
} else {
    Write-Host "Creating virtual environment with System.Python()..."
    python -m venv .venv
    $Python = ".venv\Scripts\python.exe"
}

# Verify Python works
if (-not (Test-Path -LiteralPath $Python)) {
    Write-Host "ERROR: Python executable not found at $Python"
    exit 1
}

# Set environment variable for SQLite development
$env:RUN_LOCAL = "1"

# Install dependencies
try {
    Write-Host "Installing dependencies..."
    & $Python -m pip install -r "..\requirements.txt"
    Write-Host "✓ Dependencies installed"
} catch {
    Write-Host "ERROR: Failed to install dependencies: $($_.Exception.Message)"
    exit 1
}

# Run the project
Write-Host ""
Write-Host "========================================"
Write-Host "🚀 BuyZenix E-commerce Platform"
Write-Host "========================================"
Write-Host ""

# Run migrations
try {
    Write-Host "Step 1: Running database migrations..."
    & $Python manage.py migrate
    Write-Host "✓ Migrations completed"
} catch {
    Write-Host "ERROR: Failed to run migrations: $($_.Exception.Message)"
    exit 1
}

# Seed data
try {
    Write-Host "Step 2: Seeding sample data..."
    & $Python manage.py seed
    Write-Host "✓ Sample data seeded"
} catch {
    Write-Host "ERROR: Failed to seed data: $($_.Exception.Message)"
    exit 1
}

# Create admin user
try {
    Write-Host "Step 3: Creating admin user..."
    $script = "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@buyzenix.com', 'admin12345')"
    & $Python manage.py shell -c $script
    Write-Host "✓ Admin user created"
} catch {
    Write-Host "Note: Admin user creation failed (may already exist)"
}

# Start the server
Write-Host ""
Write-Host "========================================"
Write-Host "✓ Project setup complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "📱 Storefront: http://127.0.0.1:8000/"
Write-Host "🛠  Admin:      http://127.0.0.1:8000/admin/  →  admin/admin12345"
Write-Host ""
Write-Host "🚀 Starting Django development server..."
Write-Host ""
Write-Host "💡 Press Ctrl+C to stop"
Write-Host ""

# Start the server in the current process
& $Python manage.py runserver 127.0.0.1:8000
