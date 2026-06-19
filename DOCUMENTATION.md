# MeFrp-GR-Client 完整文档

## 项目概述

MeFrp-GR-Client 是一个基于 MEFrp API 的第三方客户端，提供隧道管理、用户信息查询、签到等功能。

**访问地址：** http://127.0.0.1:5001

**客户端名称：** MeFrp-GR-Client/1.0.0

**API 文档：** https://apidoc.mefrp.com/

---

## 功能特性

### ✅ 已实现功能

- **用户认证**：Token 登录、密码登录、注册、登出
- **用户信息**：查看账户信息、流量、隧道数量等
- **签到系统**：每日签到获取流量奖励（需要人机验证）
- **隧道管理**：创建、删除、启用/禁用、强制下线、更新隧道
- **节点信息**：查看节点列表、节点状态、连接地址
- **系统统计**：用户数量、节点数量、隧道数量统计

---

## API 实现清单

### 1. 公共信息 API

| API 端点 | 方法 | 说明 |
|---------|------|------|
| `/api/public/statistics` | GET | 获取用户/节点/隧道数量统计 |
| `/api/public/store/products` | GET | 获取商城商品列表 |
| `/api/public/announcements/important` | GET | 获取重要公告 |

### 2. 注册/登录 API

| API 端点 | 方法 | 说明 |
|---------|------|------|
| `/api/public/register/send` | POST | 发送注册验证码 |
| `/api/public/register` | POST | 注册账户 |
| `/api/public/login` | POST | 密码登录（需要验证码） |
| `/api/public/reset/send` | POST | 发送重置密码验证码 |
| `/api/public/reset` | POST | 重置密码 |
| `/api/token_login` | POST | Token 登录 |
| `/api/logout` | POST | 登出 |

### 3. 用户相关 API

| API 端点 | 方法 | 说明 |
|---------|------|------|
| `/api/user_info` | GET | 获取用户信息 |
| `/api/user/frp_token` | GET | 获取用户 frpToken |
| `/api/user/group` | GET | 获取用户组信息 |
| `/api/user/reset_token` | POST | 重置访问密钥（需要验证码） |
| `/api/user/change_password` | POST | 修改密码 |
| `/api/user/logs` | GET | 获取用户操作日志 |
| `/api/user/log_stats` | GET | 获取用户日志统计 |
| `/api/sign` | POST | 签到（需要验证码） |
| `/api/refresh_token` | POST | 刷新 Token |

### 4. 隧道相关 API

| API 端点 | 方法 | 说明 |
|---------|------|------|
| `/api/tunnels` | GET | 获取隧道列表 |
| `/api/proxy/list` | GET | 获取隧道列表（官方API） |
| `/api/create_proxy_data` | GET | 获取创建隧道所需数据 |
| `/api/create_tunnel` | POST | 创建隧道 |
| `/api/delete_tunnel/<proxy_id>` | DELETE | 删除隧道 |
| `/api/kick_tunnel/<proxy_id>` | POST | 强制下线隧道 |
| `/api/toggle_tunnel/<proxy_id>` | POST | 启用/禁用隧道 |
| `/api/tunnel/config/<proxy_id>` | GET | 获取单一隧道配置 |
| `/api/tunnels/config` | POST | 获取多个隧道配置 |
| `/api/update_tunnel/<proxy_id>` | POST | 更新隧道 |

### 5. 节点相关 API

| API 端点 | 方法 | 说明 |
|---------|------|------|
| `/api/nodes` | GET | 获取节点列表 |
| `/api/node/list` | GET | 获取节点列表（标准格式） |
| `/api/node/connection` | GET | 获取节点连接地址列表 |
| `/api/node/status/<node_id>` | GET | 获取节点状态 |
| `/api/node/token/<node_id>` | GET | 获取节点 Token |

---

## 快速开始

### 启动方式

#### 方式一：使用启动脚本（推荐）

双击运行 `launch.bat` 文件即可启动 WebUI。

#### 方式二：使用生产模式

双击 `稳定启动.bat` 使用生产模式启动（更稳定）。

#### 方式三：手动启动

```bash
py app.py
```

或使用 waitress 生产服务器：

```bash
py -c "from waitress import serve; from app import app; serve(app, host='0.0.0.0', port=5001)"
```

### 首次使用流程

#### 1. 登录

点击右上角"登录"按钮，进入登录页面。

**Token 登录（推荐）：**
1. 点击"Token 登录"标签
2. 输入您的访问 Token
3. 点击"Token 登录"按钮

**Token 获取方式：**
- 登录 https://www.mefrp.com
- 进入用户设置
- 找到"访问 Token"或"API Token"
- 复制 Token

**密码登录：**
1. 输入邮箱和密码
2. 点击"获取验证码"按钮
3. 在弹出窗口完成人机验证
4. 复制验证码到输入框
5. 点击"登录"按钮

#### 2. 查看控制面板

登录成功后，您将看到用户信息面板，包括：
- 用户名、邮箱
- 用户组、流量使用情况
- 隧道数量统计
- 今日签到状态

---

## 人机验证系统

### 验证码 URL

```
https://www.mefrp.com/3rdparty/captcha?client=MeFrp-GR-Client
```

### 需要验证码的接口

1. **获取邮件注册验证码** - `/public/register/emailCode`
2. **密码登录** - `/public/login`
3. **签到** - `/auth/user/sign`
4. **重置访问密钥** - `/auth/user/tokenReset`

### 验证码使用流程

1. 点击"获取验证码"按钮
2. 在新窗口中完成人机验证
3. 页面会返回 Base64 编码的字符串
4. 解码后格式为 `token||client`
5. 提取 `token` 部分作为 `captchaToken`

### 注意事项

1. **每个验证码只能用一次**
2. **验证码有时效性**，建议立即使用
3. **不要缓存或重用验证码**
4. **客户端名称不要使用中文**

---

## 创建隧道

### API 端点

**POST** `/api/create_tunnel`

### 请求参数

#### 必填参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `node_id` | int | 节点ID |
| `name` | string | 隧道名称 |
| `proxy_type` | string | 隧道类型：`TCP`、`UDP`、`HTTP`、`HTTPS` |
| `local_ip` | string | 本地服务 IP 地址 |
| `local_port` | int | 本地服务端口 |

#### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `remote_port` | int | 远程端口（留空自动分配） |
| `domain` | string | 子域名（HTTP/HTTPS 专用） |
| `http_plugin` | string | HTTP 插件 |
| `http_user` | string | HTTP Basic 认证用户名 |
| `http_password` | string | HTTP Basic 认证密码 |
| `use_encryption` | bool | 是否启用加密 |
| `use_compression` | bool | 是否启用压缩 |

### 响应示例

```json
{
    "code": 200,
    "data": {
        "proxyId": 12345,
        "proxyName": "my-tunnel",
        "proxyType": "TCP",
        "nodeId": 1,
        "localIp": "127.0.0.1",
        "localPort": 8080,
        "remotePort": 12345,
        "isDisabled": false,
        "isBanned": false,
        "isOnline": false
    },
    "message": "创建成功"
}
```

---

## 常见问题

### 1. 关于 WARNING 警告

当您看到以下警告时：
```
WARNING: This is a development server. Do not use it in production deployment.
```

**这是正常的！不是错误！**

- WebUI 可以正常运行
- 所有功能正常工作
- 只是提醒不要用于商业生产环境

如需消除警告，请使用生产模式启动（`稳定启动.bat`）

### 2. TCP 建站规定

- 中国大陆节点禁止 TCP 建站
- 如使用 TCP 穿透 NAS 等内容需尽快整改
- 80/443 端口建站需要备案域名过白
- 其他地区节点不受影响

### 3. 端口冲突

如果遇到端口冲突（5000/5001 被占用），可以：
1. 关闭占用端口的程序
2. 或修改 `app.py` 中的端口号

### 4. 签到失败

如果签到失败，请检查：
1. 验证码是否有效（每个验证码只能用一次）
2. 验证码是否过期（建议获取后立即使用）
3. 是否已经签到过

### 5. 隧道无法获取

如果无法获取隧道列表：
1. 检查是否已登录
2. 尝试重新登录
3. 检查网络连接

---

## 更新日志

### 2026-05-27 最新更新

#### 新增重要公告系统
- 添加醒目的红色渐变背景重要公告板块
- 突出显示节点下线通知
- 地图模式新功能介绍

#### 功能修复
- API 响应处理优化
- 签到验证码流程优化
- 隧道管理优化

### 2026-05-27 功能完善

- 完成所有 API 接口实现
- 添加用户组信息获取
- 添加用户操作日志
- 添加隧道配置管理

### 早期更新

- 实现 Token 登录和密码登录
- 实现隧道 CRUD 操作
- 实现节点列表和状态查询
- 实现签到功能
- 实现人机验证集成

---

## 文件结构

```
e:\桌面\1\
├── app.py                      # 主程序
├── templates/
│   └── index.html             # 前端界面
├── README.md                   # 启动说明
├── PROJECT_SUMMARY.md          # 功能总结
├── FULL_API_DOCUMENTATION.md   # API 文档
├── CAPTCHA_GUIDE.md            # 验证码指南
├── API_CREATE_TUNNEL.md        # 创建隧道文档
├── STARTUP_GUIDE.md           # 启动指南
├── CHANGELOG.md               # 更新日志
└── 启动脚本.bat               # 启动脚本
```

---

## 技术栈

- **后端**：Python + Flask
- **前端**：HTML + CSS + JavaScript
- **HTTP 服务器**：waitress
- **API 库**：MEFrpLib
- **第三方服务**：MEFrp API

---

## 注意事项

1. 本客户端为第三方开发，使用时请遵守 MEFrp 服务条款
2. 请保护好您的账户 Token，不要泄露给他人
3. 验证码系统仅用于人机验证，请勿滥用
4. 虚拟商品不支持退款

---

**文档版本：** 1.0.0
**更新日期：** 2026-05-29
**客户端名称：** MeFrp-GR-Client
