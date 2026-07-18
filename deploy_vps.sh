#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${DOMAIN:-buyzenix.com}"
APP_DIR="${APP_DIR:-/opt/web-env/BuyZenix}"
REPO_URL="${REPO_URL:-https://github.com/asmsaifulislam/BuyZenix.git}"
HTTP_PORT="${HTTP_PORT:-80}"

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Run this script as root on the VPS."
  exit 1
fi

install_packages() {
  if command -v dnf >/dev/null 2>&1; then
    dnf install -y git curl ca-certificates openssl
  elif command -v apt-get >/dev/null 2>&1; then
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y git curl ca-certificates openssl
  else
    echo "Unsupported package manager."
    exit 1
  fi
}

install_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    if command -v dnf >/dev/null 2>&1; then
      dnf install -y dnf-plugins-core
      dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
      dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    elif command -v apt-get >/dev/null 2>&1; then
      curl -fsSL https://get.docker.com | sh
    else
      echo "Unsupported package manager for Docker installation."
      exit 1
    fi
  fi
  systemctl enable --now docker
}

prepare_kernel_networking() {
  modprobe overlay >/dev/null 2>&1 || true
  modprobe br_netfilter >/dev/null 2>&1 || true
  modprobe nf_conntrack >/dev/null 2>&1 || true
  modprobe nf_nat >/dev/null 2>&1 || true
  modprobe iptable_nat >/dev/null 2>&1 || true
  modprobe xt_addrtype >/dev/null 2>&1 || true

  cat >/etc/sysctl.d/99-buyzenix-docker.conf <<EOF
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF
  sysctl --system >/dev/null 2>&1 || true

  systemctl enable --now containerd >/dev/null 2>&1 || true
  systemctl reset-failed docker >/dev/null 2>&1 || true
  systemctl restart docker >/dev/null 2>&1 || true
}

open_firewall() {
  if command -v firewall-cmd >/dev/null 2>&1; then
    systemctl enable --now firewalld >/dev/null 2>&1 || true
    firewall-cmd --permanent --add-service=http >/dev/null 2>&1 || true
    firewall-cmd --permanent --add-service=https >/dev/null 2>&1 || true
    firewall-cmd --reload >/dev/null 2>&1 || true
  fi
}

prepare_hostname() {
  hostnamectl set-hostname "$DOMAIN" || true
  if ! grep -qE "^127\.0\.1\.1[[:space:]]+$DOMAIN([[:space:]]|$)" /etc/hosts; then
    echo "127.0.1.1 $DOMAIN" >> /etc/hosts
  fi
}

sync_repo() {
  mkdir -p "$(dirname "$APP_DIR")"
  if [[ -d "$APP_DIR/.git" ]]; then
    git -C "$APP_DIR" pull --ff-only
  else
    git clone "$REPO_URL" "$APP_DIR"
  fi
}

write_env() {
  local secret_key postgres_password server_ip
  secret_key="$(openssl rand -base64 48 | tr -d '\n')"
  postgres_password="$(openssl rand -base64 24 | tr -d '/+=\n' | cut -c1-24)"
  server_ip="$(hostname -I 2>/dev/null | awk '{print $1}')"

  cat > "$APP_DIR/.env" <<EOF
POSTGRES_DB=buyzenix
POSTGRES_USER=buyzenix
POSTGRES_PASSWORD=$postgres_password
DB_HOST=db
DB_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379

SECRET_KEY=$secret_key
DEBUG=0
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost,127.0.0.1${server_ip:+,$server_ip}
DJANGO_SETTINGS_MODULE=buyzenix.settings

EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=no-reply@$DOMAIN

RUN_LOCAL=0
EOF
}

deploy_stack() {
  cd "$APP_DIR"
  HTTP_PORT="$HTTP_PORT" docker compose up -d --build
}

install_packages
install_docker
prepare_kernel_networking
open_firewall
prepare_hostname
sync_repo
write_env
deploy_stack

echo "Deployment finished."
echo "Open: http://$DOMAIN/"
