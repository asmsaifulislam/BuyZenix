# PowerShell script to deploy BuyZenix to remote server

param(
    [Parameter(Mandatory=$true)]
    [string]$RemoteHost = "144.225.8.129",
    
    [Parameter(Mandatory=$true)]
    [string]$RemoteUser = "root",
    
    [Parameter(Mandatory=$true)]
    [string]$RemotePassword,
    
    [Parameter(Mandatory=$false)]
    [string]$LocalPath = "D:\BuyZenix\app",
    
    [Parameter(Mandatory=$false)]
    [string]$RemotePath = "/opt/web-env/BuyZenix"
)

# Try to locate sshpass
$sshpassCmd = Get-Command "sshpass.exe" -ErrorAction SilentlyContinue
if (-not $sshpassCmd) {
    Write-Host "sshpass not found, please download from: https://github.com/HelixAquila/libsshpass-windows/releases"
    exit 1
}
$sshpassPath = $sshpassCmd.Source

# Clean up the remote directory
Write-Host "Cleaning up remote path: $RemotePath"
& $sshpassPath -p $RemotePassword ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no $RemoteUser@$RemoteHost "mkdir -p $RemotePath; find $RemotePath -mindepth 1 -maxdepth 1 -exec rm -rf {} +; cd $RemotePath; git clone https://github.com/asmsaifulislam/BuyZenix.git ."

# Wait a bit for git clone to complete
Start-Sleep -Seconds 5

# Change to the app directory
$AppPath = "$RemotePath/app"
Write-Host "App path: $AppPath"

# Check Python installation
& $sshpassPath -p $RemotePassword ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no $RemoteUser@$RemoteHost "which python3; python3 --version"

# Install python3.10-venv if needed
& $sshpassPath -p $RemotePassword ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no $RemoteUser@$RemoteHost "apt-get update >/dev/null 2>&1 && apt-get install -y python3.10-venv python3-pip >/dev/null 2>&1; echo 'Python packages installed.'"

# Create virtual environment and install dependencies
Write-Host "Creating virtual environment..."
& $sshpassPath -p $RemotePassword ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no $RemoteUser@$RemoteHost "cd $AppPath; python3 -m venv .venv; . .venv/bin/activate; pip install --upgrade pip >/dev/null 2>&1; pip install -r ../requirements.txt >/dev/null 2>&1; echo 'Dependencies installed.'"

# Generate secret key and create .env file
Write-Host "Generating secret key and creating .env file..."
$SecretKey = & $sshpassPath -p $RemotePassword ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no $RemoteUser@$RemoteHost "cd $AppPath; . .venv/bin/activate; python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"

$EnvContent = @"
SECRET_KEY=$SecretKey
DEBUG=0
RUN_LOCAL=1
ALLOWED_HOSTS=$RemoteHost,localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=buyzenix.settings
"@

$EnvCommand = @"
cd $AppPath
cat > .env <<'EOF'
$EnvContent
EOF
cat .env
"@

& $sshpassPath -p $RemotePassword ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no $RemoteUser@$RemoteHost $EnvCommand

Write-Host ""
Write-Host "Deployment successful!"
Write-Host "Server: $RemoteHost"
Write-Host "Path: $RemotePath"
Write-Host "App path: $AppPath"
