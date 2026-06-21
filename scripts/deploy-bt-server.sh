#!/usr/bin/env bash
# ============================================================================
# MeFrp-GR-Client 宝塔面板部署脚本（服务器侧）
# 用法：ssh user@server "bash deploy-bt-server.sh" 或 scp 上传后 bash 执行
# ============================================================================
set -euo pipefail

# ---------- 参数（由 deploy-bt.ps1 远程调用时传入，或手动导出） ----------
SITE_DOMAIN="${BT_SITE_DOMAIN:-mefrp.example.com}"
SITE_ROOT="${BT_SITE_ROOT:-/www/wwwroot/${SITE_DOMAIN}}"
BT_PANEL="${BT_PANEL:-}"
BT_KEY="${BT_KEY:-}"
NGINX_RELOAD_CMD="${NGINX_RELOAD_CMD:-nginx -s reload}"
KEEP_BACKUPS="${KEEP_BACKUPS:-5}"

# ---------- 颜色 ----------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()    { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $*"; }
ok()     { echo -e "${GREEN}[✓]${NC} $*"; }
warn()   { echo -e "${YELLOW}[!]${NC} $*"; }
err()    { echo -e "${RED}[✗]${NC} $*" >&2; }
die()    { err "$*"; exit 1; }

# ---------- 权限检查 ----------
[[ $EUID -eq 0 ]] || die "请用 root 运行：sudo bash $0"

# ---------- 1. 准备站点目录 ----------
log "准备站点目录：${SITE_ROOT}"
mkdir -p "${SITE_ROOT}"
mkdir -p "${SITE_ROOT}/.backups"

# ---------- 2. 备份现有站点（如果存在） ----------
if [[ -f "${SITE_ROOT}/index.html" ]]; then
  TS=$(date +%Y%m%d-%H%M%S)
  BACKUP_FILE="${SITE_ROOT}/.backups/site-${TS}.tar.gz"
  log "备份现有站点 → ${BACKUP_FILE}"
  tar -czf "${BACKUP_FILE}" \
      -C "${SITE_ROOT}" \
      --exclude='.backups' \
      . || warn "备份失败（继续部署）"

  # 清理旧备份
  cd "${SITE_ROOT}/.backups"
  ls -t site-*.tar.gz 2>/dev/null | tail -n +$((KEEP_BACKUPS + 1)) | xargs -r rm -f
  ok "备份完成（保留最近 ${KEEP_BACKUPS} 份）"
fi

# ---------- 3. 清理旧文件（保留 .backups） ----------
log "清理站点根目录..."
find "${SITE_ROOT}" -mindepth 1 -maxdepth 1 \
     ! -name '.backups' \
     -exec rm -rf {} +

# ---------- 4. 接收部署包 ----------
# 部署包路径（PowerShell 脚本会 scp 上传到此路径）
PKG_FILE="${SITE_ROOT}/.deploy-pkg.zip"

# 如果 PKG_FILE 不存在，尝试从 /tmp 拉取
if [[ ! -f "${PKG_FILE}" ]]; then
  if [[ -f "/tmp/mefrp-site.zip" ]]; then
    PKG_FILE="/tmp/mefrp-site.zip"
  else
    die "未找到部署包。请先上传 docs.zip 到 ${SITE_ROOT}/.deploy-pkg.zip 或 /tmp/mefrp-site.zip"
  fi
fi

# ---------- 5. 解压部署包 ----------
log "解压部署包 → ${SITE_ROOT}"
which unzip >/dev/null 2>&1 || die "缺少 unzip，请先安装：apt install -y unzip"
unzip -oq "${PKG_FILE}" -d "${SITE_ROOT}"
rm -f "${PKG_FILE}"
ok "解压完成"

# ---------- 6. 设置权限（宝塔规范） ----------
log "设置文件权限（www:www）"
chown -R www:www "${SITE_ROOT}"
find "${SITE_ROOT}" -type d -exec chmod 755 {} \;
find "${SITE_ROOT}" -type f -exec chmod 644 {} \;
ok "权限已设置"

# ---------- 7. （可选）通过宝塔 API 注册站点 ----------
if [[ -n "${BT_PANEL}" && -n "${BT_KEY}" ]]; then
  log "通过宝塔 API 注册/更新站点..."
  bash "$(dirname "$0")/bt-api.sh" \
      --panel "${BT_PANEL}" \
      --key "${BT_KEY}" \
      --domain "${SITE_DOMAIN}" \
      --root "${SITE_ROOT}" \
      --ssl-auto || warn "宝塔 API 调用失败，请到面板手动检查"
else
  warn "未配置 BT_PANEL/BT_KEY，跳过 API 注册（请到宝塔面板手动添加站点 ${SITE_DOMAIN}）"
fi

# ---------- 8. 写入/更新 Nginx 伪静态配置 ----------
NGINX_CONF="/www/server/panel/vhost/nginx/${SITE_DOMAIN}.conf"
if [[ -f "${NGINX_CONF}" ]]; then
  log "注入伪静态 + 静态资源缓存规则"
  cat > /tmp/mefrp-include.conf <<'EOF'
    # ===== MeFrp 静态资源优化（脚本自动注入） =====
    location ~* \.(css|js|svg|png|jpg|jpeg|gif|ico|woff2?)$ {
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
        access_log off;
    }
    gzip on;
    gzip_types text/css application/javascript image/svg+xml application/json;
    gzip_min_length 1000;
    location / {
        try_files $uri $uri/ /index.html;
    }
EOF
  # 在 server { 后插入
  sed -i '/server {/r /tmp/mefrp-include.conf' "${NGINX_CONF}"
  rm -f /tmp/mefrp-include.conf
  ok "Nginx 配置已更新"
else
  warn "未找到 ${NGINX_CONF}，请先在宝塔面板添加站点"
fi

# ---------- 9. 测配置并重载 Nginx ----------
log "测试 Nginx 配置..."
if nginx -t 2>&1 | grep -q "successful"; then
  log "重载 Nginx..."
  ${NGINX_RELOAD_CMD}
  ok "Nginx 已重载"
else
  err "Nginx 配置测试失败："
  nginx -t
  exit 1
fi

# ---------- 10. 输出部署结果 ----------
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "  域名：  ${SITE_DOMAIN}"
echo -e "  路径：  ${SITE_ROOT}"
echo -e "  备份：  ${SITE_ROOT}/.backups/ (保留 ${KEEP_BACKUPS} 份)"
echo -e "${GREEN}========================================${NC}"
