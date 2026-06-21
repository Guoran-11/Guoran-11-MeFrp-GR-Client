#!/usr/bin/env bash
# ============================================================================
# 宝塔面板 API 集成脚本
# 用法：bash bt-api.sh --panel URL --key KEY --domain DOMAIN --root PATH [选项]
# 功能：通过宝塔公开 API 自动建站、申请 SSL、应用伪静态
# ============================================================================
set -euo pipefail

PANEL=""
KEY=""
DOMAIN=""
ROOT=""
SSL_AUTO="false"
PSEUDO_FILE=""

usage() {
  cat <<EOF
宝塔面板 API 集成脚本

用法:
  bash $0 --panel <面板URL> --key <API密钥> --domain <域名> --root <站点根目录> [选项]

必填:
  --panel     宝塔面板地址（含端口），例如 https://1.2.3.4:8888
  --key       宝塔 API Key（面板 → 设置 → API 接口）
  --domain    要添加的域名
  --root      站点根目录绝对路径

可选:
  --ssl-auto  申请 Let's Encrypt 证书（true/false，默认 false）
  --pseudo    自定义伪静态文件路径（默认注入 MeFrp 静态资源缓存规则）
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --panel)   PANEL="$2"; shift 2 ;;
    --key)     KEY="$2"; shift 2 ;;
    --domain)  DOMAIN="$2"; shift 2 ;;
    --root)    ROOT="$2"; shift 2 ;;
    --ssl-auto) SSL_AUTO="$2"; shift 2 ;;
    --pseudo)  PSEUDO_FILE="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数：$1"; usage; exit 1 ;;
  esac
done

[[ -z "$PANEL"  ]] && { echo "缺少 --panel";  usage; exit 1; }
[[ -z "$KEY"    ]] && { echo "缺少 --key";    usage; exit 1; }
[[ -z "$DOMAIN" ]] && { echo "缺少 --domain"; usage; exit 1; }
[[ -z "$ROOT"   ]] && { echo "缺少 --root";   usage; exit 1; }

# 去掉尾部斜杠
PANEL="${PANEL%/}"

# 时间戳
NOW=$(date +%s)

# 签名：md5(timestamp + md5(key))
KEY_MD5=$(echo -n "$KEY" | md5sum | awk '{print $1}')
SIGN=$(echo -n "${NOW}${KEY_MD5}" | md5sum | awk '{print $1}')

# ---------- 公共函数 ----------
bt_call() {
  local endpoint="$1"
  shift
  # 将剩余参数转成 p1=v1&p2=v2
  local args=""
  for kv in "$@"; do
    local k="${kv%%=*}"
    local v="${kv#*=}"
    [[ -n "$args" ]] && args+="&"
    # urlencode
    v=$(printf '%s' "$v" | jq -sRr @uri 2>/dev/null || python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.stdin.read().rstrip()))" <<< "$v")
    args+="${k}=${v}"
  done

  local url="${PANEL}${endpoint}?${args}&timestamp=${NOW}&sign=${SIGN}"
  echo "→ $endpoint" >&2
  curl -sk -X POST "$url"
  echo
}

# ---------- 1. 检查站点是否已存在 ----------
echo "==> 检查站点 ${DOMAIN} 是否存在"
SITE_LIST=$(bt_call "/site?action=get_site_list" "limit=100" "p=1")
EXISTING=$(echo "$SITE_LIST" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    sites = d.get('data', []) or []
    for s in sites:
        if s.get('name') == '$DOMAIN':
            print(s.get('id')); break
except: pass
" 2>/dev/null)

if [[ -n "$EXISTING" ]]; then
  echo "   站点已存在（ID=$EXISTING），跳过创建"
else
  echo "==> 创建站点 ${DOMAIN}"
  bt_call "/site?action=AddSite" \
    "webname=${DOMAIN}" \
    "path=${ROOT}" \
    "type_id=0" \
    "type=PHP" \
    "version=00" \
    "port=80" \
    "ps=MeFrp 宣传站" >/dev/null

  # 强制改为纯静态：删除默认 PHP 配置，添加空 index.html
  mkdir -p "$ROOT"
  touch "$ROOT/index.html"
  echo "   站点创建完成"
fi

# ---------- 2. 写入伪静态 ----------
if [[ -n "$PSEUDO_FILE" && -f "$PSEUDO_FILE" ]]; then
  PSEUDO_CONTENT=$(cat "$PSEUDO_FILE")
else
  PSEUDO_CONTENT='location ~* \.(css|js|svg|png|jpg|jpeg|gif|ico|woff2?)$ {
    expires 30d;
    add_header Cache-Control "public, max-age=2592000";
    access_log off;
}
gzip on;
gzip_types text/css application/javascript image/svg+xml application/json;
gzip_min_length 1000;
location / {
    try_files $uri $uri/ /index.html;
}'
fi

echo "==> 应用伪静态规则"
bt_call "/site?action=SetSiteRewrite" \
  "siteName=${DOMAIN}" \
  "data=$(printf '%s' "$PSEUDO_CONTENT" | base64 -w0)" >/dev/null

# ---------- 3. 申请 SSL（可选） ----------
if [[ "$SSL_AUTO" == "true" ]]; then
  echo "==> 申请 Let's Encrypt 证书"
  bt_call "/acme?action=apply_cert_api" \
    "domains=${DOMAIN}" \
    "auth_type=http" \
    "auto_wildcard=0" >/dev/null || echo "   SSL 申请失败，可手动到面板操作"

  echo "==> 开启 HTTPS 强制跳转"
  bt_call "/site?action=SetSSL" \
    "siteName=${DOMAIN}" \
    "keyId=$(echo "$PSEUDO_CONTENT" | md5sum | awk '{print $1}')" >/dev/null || true
fi

# ---------- 4. 重载 Nginx ----------
echo "==> 重载 Nginx"
bt_call "/system?action=ReloadService" "type=nginx" >/dev/null

echo "==> 完成"
