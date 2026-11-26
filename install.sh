#!/usr/bin/env bash
# RoXeT Emoji Extractor installer (Ubuntu/Debian).
# Usage: ./install.sh                 full setup + systemd service
#        ./install.sh --no-service    setup only
set -euo pipefail
cd "$(dirname "$0")"
DIR="$(pwd)"
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"

echo "==> Installing system packages"
$SUDO apt-get update -y
$SUDO apt-get install -y python3 python3-venv python3-pip

echo "==> Creating virtualenv"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

if [ ! -f .env ]; then
  echo "==> Configuration (saved only in $DIR/.env)"
  read -rsp "Bot token (hidden): " BOT_TOKEN; echo
  read -rp  "Your numeric Telegram user ID: " OWNER_ID
  umask 077
  cat > .env <<ENVEOF
BOT_TOKEN=$BOT_TOKEN
OWNER_ID=$OWNER_ID
ENVEOF
fi
chmod 600 .env

if [ "${1:-}" = "--no-service" ]; then
  echo "Done. Run manually:  .venv/bin/python emojibot.py"
  exit 0
fi

echo "==> Installing systemd service"
sed -e "s|CHANGE_USER|$(id -un)|" -e "s|CHANGE_DIR|$DIR|g" deploy/roxet-emoji.service.example \
  | $SUDO tee /etc/systemd/system/roxet-emoji.service >/dev/null
$SUDO systemctl daemon-reload
$SUDO systemctl enable --now roxet-emoji
sleep 3
$SUDO systemctl --no-pager status roxet-emoji | head -n 12 || true
echo "Logs:  sudo journalctl -u roxet-emoji -f"
