# MEFrp WebUI API 完整实现

## 基于 https://apidoc.mefrp.com/ 文档的完整 API 实现

---

## 📋 API 列表

### 1. 公共信息 API

#### GET /api/public/statistics
获取用户数量、节点数量、隧道数量、已承载流量

**响应：**
```json
{
  "code": 200,
  "data": {
    "users": 44984,
    "nodes": 57,
    "proxies": 4696,
    "traffic": 76852995417754
  },
  "message": "获取统计信息成功"
}
```

#### GET /api/public/store/products
获取商城商品列表

**响应：**
```json
{
  "code": 200,
  "data": [
    {
      "type": "traffic",
      "name": "流量包",
      "price": 0.1,
      "unit": "GB",
      "description": "无限期有效|无额外限速|支持所有节点",
      "enabled": true
    }
  ],
  "message": "获取成功"
}
```

### 2. 注册/登录 API

#### POST /api/public/register/send
发送注册验证码

**请求：**
```json
{
  "email": "user@example.com",
  "captchaToken": "验证token"
}
```

#### POST /api/public/register
注册账户

**请求：**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password",
  "code": "验证码"
}
```

#### POST /api/public/login
密码登录（需要人机验证）

**请求：**
```json
{
  "username": "username",
  "password": "password",
  "captchaToken": "验证token"
}
```

#### POST /api/public/reset/send
发送重置密码验证码

**请求：**
```json
{
  "email": "user@example.com",
  "captchaToken": "验证token"
}
```

#### POST /api/public/reset
重置密码

**请求：**
```json
{
  "email": "user@example.com",
  "code": "验证码",
  "password": "新密码"
}
```

### 3. 认证 API

#### POST /api/token_login
Token 登录

**请求：**
```json
{
  "token": "访问令牌"
}
```

#### GET /api/logout
登出

**响应：**
```json
{
  "message": "已退出登录",
  "code": 200
}
```

### 4. 用户相关 API

#### GET /api/user/info
获取用户信息

**响应：**
```json
{
  "code": 200,
  "data": {
    "userId": 29688,
    "username": "Test",
    "email": "test@mefrp.com",
    "group": "default",
    "friendlyGroup": "正式用户",
    "traffic": 533504,
    "maxProxies": 13,
    "usedProxies": 0,
    "isRealname": true,
    "todaySigned": false,
    "inBound": 3200,
    "outBound": 3200
  },
  "message": "获取用户信息成功"
}
```

#### POST /api/user/sign
签到（需要人机验证）

**请求：**
```json
{
  "captchaToken": "验证token"
}
```

**响应：**
```json
{
  "code": 200,
  "data": null,
  "message": "签到成功，获得 10 + 10 GB 流量"
}
```

#### GET /api/user/frp_token
获取用户 frpToken

**响应：**
```json
{
  "code": 200,
  "data": {
    "frpToken": "xxx",
    "username": "xxx"
  },
  "message": "获取frpToken成功"
}
```

#### GET /api/user/group
获取用户组信息

**响应：**
```json
{
  "code": 200,
  "data": {
    "name": "default",
    "friendlyName": "正式用户",
    "maxProxies": 13,
    "baseTraffic": 32266,
    "outBound": 3200,
    "inBound": 3200
  },
  "message": "获取用户组信息成功"
}
```

#### POST /api/user/reset_token
重置访问密钥（需要人机验证）

**请求：**
```json
{
  "captchaToken": "验证token"
}
```

#### POST /api/user/change_password
修改密码

**请求：**
```json
{
  "oldPassword": "旧密码",
  "newPassword": "新密码"
}
```

#### GET /api/user/logs
获取用户操作日志

**查询参数：**
- `page`: 页码（默认 1）
- `pageSize`: 每页数量（默认 20）

**响应：**
```json
{
  "code": 200,
  "data": {
    "data": [
      {
        "logId": 1,
        "category": "login",
        "details": "登录成功",
        "ipAddress": "127.0.0.1",
        "status": "success",
        "createdAt": "2026-05-27 12:00:00"
      }
    ],
    "total": 100,
    "page": 1,
    "pageSize": 20,
    "totalPages": 5
  },
  "message": "获取日志成功"
}
```

#### GET /api/user/log_stats
获取用户日志统计

**响应：**
```json
{
  "code": 200,
  "data": {
    "todayCount": 5,
    "weekCount": 20,
    "monthCount": 50,
    "totalCount": 100
  },
  "message": "获取日志统计成功"
}
```

### 5. 隧道相关 API

#### GET /api/tunnels
获取隧道列表

**响应：**
```json
{
  "code": 200,
  "data": {
    "proxies": [...],
    "nodes": [...]
  },
  "message": "获取隧道列表成功"
}
```

#### GET /api/create_proxy_data
获取创建隧道所需的所有数据

**响应：**
```json
{
  "code": 200,
  "data": {
    "nodes": [...],
    "groups": [...],
    "currentGroup": "default"
  },
  "message": "获取成功"
}
```

#### POST /api/create_tunnel
创建隧道

**请求：**
```json
{
  "nodeId": 1,
  "proxyName": "my-tunnel",
  "proxyType": "TCP",
  "localIp": "127.0.0.1",
  "localPort": 8080,
  "remotePort": 12345,
  "domain": "",
  "httpPlugin": "",
  "httpUser": "",
  "httpPassword": "",
  "useEncryption": false,
  "useCompression": false
}
```

#### DELETE /api/delete_tunnel/<proxy_id>
删除隧道

**响应：**
```json
{
  "code": 200,
  "message": "删除成功"
}
```

#### POST /api/kick_tunnel/<proxy_id>
强制下线隧道

**响应：**
```json
{
  "code": 200,
  "message": "强制下线成功"
}
```

#### POST /api/toggle_tunnel/<proxy_id>
启用/禁用隧道

**响应：**
```json
{
  "code": 200,
  "message": "操作成功"
}
```

#### GET /api/tunnel/config/<proxy_id>
获取单一隧道配置

**响应：**
```json
{
  "code": 200,
  "data": {
    "config": "[common]...",
    "type": "tcp"
  },
  "message": "获取成功"
}
```

#### POST /api/update_tunnel/<proxy_id>
更新隧道

**请求：**
```json
{
  "proxyName": "new-name",
  "localIp": "127.0.0.1",
  "localPort": 8080,
  "useEncryption": true,
  "useCompression": false
}
```

### 6. 节点相关 API

#### GET /api/node/list
获取节点列表

**响应：**
```json
{
  "code": 200,
  "data": [
    {
      "nodeId": 1,
      "name": "月球 ①",
      "hostname": "",
      "description": "测试节点",
      "allowGroup": "admin;sponsor;vip",
      "allowPort": "40000-65535",
      "allowType": "tcp;udp",
      "region": "cn",
      "bandwidth": "200Mbps",
      "isOnline": true,
      "isDisabled": false
    }
  ],
  "message": "获取节点成功"
}
```

#### GET /api/node/connection
获取节点连接地址列表

**响应：**
```json
{
  "code": 200,
  "data": [
    {
      "nodeId": 1,
      "name": "月球 ①",
      "hostname": "cn.example.com",
      "servicePort": 7000
    }
  ],
  "message": "获取节点连接地址成功"
}
```

#### GET /api/node/status/<node_id>
获取节点状态

**响应：**
```json
{
  "code": 200,
  "data": {
    "nodeId": 1,
    "name": "月球 ①",
    "totalTrafficIn": 1000000,
    "totalTrafficOut": 2000000,
    "onlineClient": 10,
    "onlineProxy": 25,
    "isOnline": true,
    "version": "0.52.0",
    "uptime": 86400,
    "curConns": 50,
    "loadPercent": 45
  },
  "message": "获取节点状态成功"
}
```

### 7. 系统相关 API

#### GET /api/system/status
获取系统状态

**响应：**
```json
{
  "code": 200,
  "data": {
    "status": 1,
    "remark": "正常"
  },
  "message": "获取系统状态成功"
}
```

#### GET /api/system/announcement
获取重要公告

**响应：**
```json
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "title": "重要公告",
      "content": "公告内容..."
    }
  ],
  "message": "获取公告成功"
}
```

---

## 🚀 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求有误 |
| 401 | 鉴权失败 |
| 403 | 禁止访问/已签到 |
| 404 | 未找到 |
| 500 | 服务器错误 |

---

## 📝 人机验证

需要人机验证的 API：
1. 密码登录 `/api/public/login`
2. 注册发送验证码 `/api/public/register/send`
3. 注册账户 `/api/public/register`
4. 重置密码发送验证码 `/api/public/reset/send`
5. 签到 `/api/user/sign`
6. 重置访问密钥 `/api/user/reset_token`

**验证地址：** `https://www.mefrp.com/3rdparty/captcha?client=CODENAME`

---

**文档版本：** v1.0
**最后更新：** 2026-05-27
**参考文档：** https://apidoc.mefrp.com/
