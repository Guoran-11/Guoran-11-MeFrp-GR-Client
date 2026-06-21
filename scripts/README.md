# MeFrp-GR-Client 宝塔面板部署脚本

## 文件说明

| 文件 | 用途 | 运行位置 |
|---|---|---|
| `deploy-bt.ps1` | 本地打包 + 上传 + 触发部署 | Windows / PowerShell |
| `deploy-bt-server.sh` | 服务器侧：解压、设置权限、刷新 Nginx | Linux 服务器 |
| `bt-api.sh` | 宝塔面板 API 集成（自动建站/SSL） | Linux 服务器 |
| `deploy-bt.config.example.json` | 配置文件模板 | Windows |

## 快速开始（Windows 用户）

### 1. 准备 SSH 免密登录（推荐）

```powershell
# 生成 SSH 密钥（如果还没有）
ssh-keygen -t ed25519

# 上传公钥到服务器
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh root@你的服务器IP "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### 2. 获取宝塔 API Key

1. 登录宝塔面板
2. 左侧 **设置** → **API 接口**
3. 开启 API，复制 Key
4. **注意**：需要在面板「安全设置」中**放行你本地的 IP**，否则 API 调用会被拦截

### 3. 首次部署

在项目根目录打开 PowerShell：

```powershell
cd E:\桌面\MeFrp-GR-Client
.\scripts\deploy-bt.ps1
```

按提示输入：
- 部署域名（如 `mefrp.yourdomain.com`）
- SSH 地址（如 `root@1.2.3.4`）
- 宝塔面板地址（可选）
- 宝塔 API Key（可选）

完成后会自动保存到 `scripts/deploy-bt.config.json`，下次直接运行 `.\scripts\deploy-bt.ps1` 即可。

### 4. 日常更新

修改 `docs/` 下任何文件后：

```powershell
.\scripts\deploy-bt.ps1
```

30 秒内完成全量更新 + 自动备份 + Nginx 刷新。

## 命令行参数

```powershell
# 指定参数（跳过交互）
.\scripts\deploy-bt.ps1 `
    -Domain mefrp.example.com `
    -Server root@1.2.3.4 `
    -SshKey C:\Users\me\.ssh\id_rsa
```

## 部署流程

```
Windows PowerShell                Linux Server (宝塔)
─────────────────                 ──────────────────
1. 打包 docs/ → zip          ───►
2. scp zip 到 /tmp                /tmp/mefrp-site.zip
3. scp deploy-bt-server.sh  ───► /tmp/deploy-bt-server.sh
4. ssh 执行                          │
       ▼                             ▼
                                    5. 备份现有站点 → .backups/
                                    6. 解压 zip → 站点根
                                    7. chown www:www
                                    8. 注入伪静态 + gzip + 缓存
                                    9. （可选）宝塔 API 注册/SSL
                                    10. nginx -t && nginx -s reload
```

## 服务器要求

- 宝塔面板 ≥ 7.7
- Nginx ≥ 1.18
- 已安装 `unzip`：`apt install -y unzip` 或 `yum install -y unzip`
- 站点目录权限：`www:www`（宝塔默认）

## 故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `scp` 提示密码 | 没配 SSH 免密 | 按上文生成密钥 |
| `nginx -t` 失败 | 配置文件语法错 | 宝塔面板 → 网站 → 配置文件 手动检查 |
| API 返回 401 | Key 错或 IP 未放行 | 面板 → 设置 → API → 放行本机 IP |
| 上传后 404 | 域名未解析到服务器 | DNS 添加 A 记录 |
| 中文文件名乱码 | Windows zip 编码 | 已在脚本中用 `System.IO.Compression` 解决 |

## 安全建议

- 不要把 `deploy-bt.config.json` 提交到 Git（已在 `.gitignore` 提示）
- API Key 仅在本机使用，不要泄露
- 服务器建议开启宝塔「**SSH 密钥登录**」并禁用密码登录
- 在宝塔「**软件商店 → Nginx 防火墙**」开启 CC 防护
