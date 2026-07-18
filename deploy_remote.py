#!/usr/bin/env python3

import getpass
import subprocess
import os
import sys
import socket
import shlex

def run_command(cmd, error_msg=None):
    """Run a command and return the output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        redacted_cmd = cmd
        if isinstance(cmd, list):
            redacted_cmd = list(cmd)
            for i, part in enumerate(redacted_cmd[:-1]):
                if part == "-p":
                    redacted_cmd[i + 1] = "***REDACTED***"
                    break
        error = f"Command failed: {redacted_cmd}\nError: {e.stderr}"
        print(error)
        if error_msg:
            print(f"Error: {error_msg}")
        return None

def main():
    print("Starting BuyZenix deployment to remote server...")
    
    # Remote server details
    remote_host = "144.225.8.129"
    remote_user = "root"
    remote_password = os.getenv("REMOTE_PASSWORD") or getpass.getpass("Remote password: ")
    remote_path = "/opt/web-env/BuyZenix"
    app_path = f"{remote_path}/app"
    
    # Step 1: Clean up and clone repository
    print(f"Cleaning up {remote_path}...")
    cmd = (
        f"mkdir -p {shlex.quote(remote_path)} && "
        f"find {shlex.quote(remote_path)} -mindepth 1 -maxdepth 1 -exec rm -rf {{}} + && "
        f"cd {shlex.quote(remote_path)} && git clone https://github.com/asmsaifulislam/BuyZenix.git ."
    )
    run_command(["sshpass", "-p", remote_password, "ssh", "-o", "ConnectTimeout=30", "-o", "StrictHostKeyChecking=no", f"{remote_user}@{remote_host}", cmd])
    print("Repository cloned successfully")
    
    # Step 2: Install required packages
    print("Installing python3-venv and python3-pip...")
    run_command(["sshpass", "-p", remote_password, "ssh", "-o", "ConnectTimeout=30", "-o", "StrictHostKeyChecking=no", f"{remote_user}@{remote_host}", "apt-get update >/dev/null 2>&1 && apt-get install -y python3.10-venv python3-pip >/dev/null 2>&1 && echo 'Python packages installed.'"])
    
    # Step 3: Create virtual environment and install dependencies
    print("Creating virtual environment...")
    cmd = f"cd {shlex.quote(app_path)} && python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip >/dev/null 2>&1 && pip install -r ../requirements.txt >/dev/null 2>&1 && echo 'Dependencies installed.'"
    run_command(["sshpass", "-p", remote_password, "ssh", "-o", "ConnectTimeout=60", "-o", "StrictHostKeyChecking=no", f"{remote_user}@{remote_host}", cmd])
    
    # Step 4: Generate secret key and create .env file
    print("Generating secret key and creating .env file...")
    
    # Generate secret key
    script = f"""
import socket
from django.core.management.utils import get_random_secret_key

secret_key = get_random_secret_key()
hostname = socket.gethostname()
ip = socket.gethostbyname(hostname) if hostname != 'localhost' else 'localhost'

with open('.env', 'w') as f:
    f.write(f"SECRET_KEY={{secret_key}}\n")
    f.write("DEBUG=0\n")
    f.write("RUN_LOCAL=1\n")
    f.write(f"ALLOWED_HOSTS={{ip}},localhost,127.0.0.1\n")
    f.write("DJANGO_SETTINGS_MODULE=buyzenix.settings\n")
print('.env file created')
"""
    
    cmd = f"cd {shlex.quote(app_path)} && . .venv/bin/activate && python3 -c {shlex.quote(script)}"
    run_command(["sshpass", "-p", remote_password, "ssh", "-o", "ConnectTimeout=30", "-o", "StrictHostKeyChecking=no", f"{remote_user}@{remote_host}", cmd])
    
    # Display the .env file
    print("\nEnvironment file contents:")
    run_command(["sshpass", "-p", remote_password, "ssh", "-o", "ConnectTimeout=15", "-o", "StrictHostKeyChecking=no", f"{remote_user}@{remote_host}", f"cat {shlex.quote(app_path + '/.env')}"])
    
    print("\nDeployment complete!")
    print(f"Server URL: http://{remote_host}/")
    print(f"Admin URL: http://{remote_host}/admin/")
    
    # Note about requirements
    print("\nNote: Please ensure PostgreSQL and Redis are running on the server")
    print("Run: sudo systemctl start postgresql redis-server")
    
if __name__ == "__main__":
    main()
