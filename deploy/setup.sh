#!/usr/bin/env bash
# 在全新的 Ubuntu/Debian 服务器上部署（需要 root）。
# 用法：把整个项目目录上传到服务器后，在项目目录里运行
#   sudo bash deploy/setup.sh game.example.com
# 脚本会：创建专用用户、装依赖、注册 systemd 服务、装 Caddy（自动 HTTPS）、开防火墙 80/443。
set -euo pipefail

DOMAIN="${1:-}"
if [[ -z "$DOMAIN" ]]; then
    echo "用法: sudo bash deploy/setup.sh <域名>" >&2
    exit 1
fi
if [[ $EUID -ne 0 ]]; then
    echo "请用 root 运行（sudo）" >&2
    exit 1
fi

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP=/opt/pixel-hero

apt-get update
apt-get install -y python3 python3-venv ufw debian-keyring debian-archive-keyring apt-transport-https curl gpg

# --- 应用 ---
id pixelhero >/dev/null 2>&1 || useradd --system --home "$APP" --shell /usr/sbin/nologin pixelhero
mkdir -p "$APP"
cp "$SRC"/*.py "$SRC"/*.js "$SRC"/index.html "$SRC"/requirements.txt "$APP"/
python3 -m venv "$APP/venv"
"$APP/venv/bin/pip" install --no-cache-dir -r "$APP/requirements.txt"
chown -R root:pixelhero "$APP"
chmod -R u=rwX,g=rX,o= "$APP"

sed "s#https://game.example.com#https://${DOMAIN}#" "$SRC/deploy/pixel-hero.service" \
    > /etc/systemd/system/pixel-hero.service
systemctl daemon-reload
systemctl enable --now pixel-hero

# --- Caddy（官方源） ---
if ! command -v caddy >/dev/null 2>&1; then
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list
    apt-get update
    apt-get install -y caddy
fi
sed "s/game.example.com/${DOMAIN}/" "$SRC/deploy/Caddyfile" > /etc/caddy/Caddyfile
systemctl reload caddy || systemctl restart caddy

# --- 防火墙：只开 SSH 和 Web，游戏端口 8080 不对外 ---
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo
echo "完成。访问: https://${DOMAIN}/"
echo "状态: systemctl status pixel-hero    日志: journalctl -u pixel-hero -f"
