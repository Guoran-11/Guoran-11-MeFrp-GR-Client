# MEFrp WebUI 隧道管理功能说明

## 概述

MEFrp WebUI 现在提供了完整的隧道管理功能，包括：
- 查看用户的所有隧道列表
- 创建新的隧道
- 管理和操作现有隧道

## 功能列表

### 1. 隧道列表

**位置**：左侧菜单 → 隧道管理

**功能**：
- 查看所有隧道的信息
- 显示隧道的基本信息（ID、名称、类型、节点等）
- 实时显示隧道在线状态
- 刷新隧道列表

**显示信息**：
- `ID`：隧道唯一标识
- `名称`：隧道名称
- `类型`：TCP / UDP / HTTP / HTTPS
- `节点`：隧道所在的节点名称
- `本地地址`：本地服务地址和端口
- `远程端口`：分配的远程端口
- `状态`：在线（🟢）/ 离线（🔴）
- `操作`：启用/禁用、删除

### 2. 创建新隧道

**位置**：左侧菜单 → 隧道管理 → 创建新隧道

**前置条件**：
1. 点击"加载节点数据"按钮获取可用节点列表
2. 从下拉菜单选择目标节点

**配置选项**：

#### 必填项
- **选择节点**：从可用节点中选择
- **隧道名称**：英文或数字，如 `my-tunnel`
- **隧道类型**：
  - `TCP`：通用 TCP 隧道
  - `UDP`：UDP 隧道
  - `HTTP`：HTTP 隧道（需要额外配置）
  - `HTTPS`：HTTPS 隧道（需要额外配置）
- **本地 IP**：本地服务地址，默认 `127.0.0.1`
- **本地端口**：本地服务端口，如 `8080`

#### 可选项
- **远程端口**：留空则自动分配
- **子域名**：HTTP/HTTPS 隧道专用
- **HTTP 插件**：
  - 无
  - `http2https`：将本地 HTTPS 服务通过 HTTP 隧道穿透
  - `https2http`：将本地 HTTP 服务通过 HTTPS 隧道穿透
  - `https2https`：将本地 HTTPS 服务通过 HTTPS 隧道穿透
- **访问密码**：HTTP Basic 认证
- **启用加密**：启用隧道加密
- **启用压缩**：启用 gzip 压缩

### 3. 节点监控

**位置**：左侧菜单 → 节点监控

**功能**：
- 查看所有可用节点列表
- 显示节点状态（在线/离线）
- 显示节点配置信息

**显示信息**：
- `节点ID`：节点唯一标识
- `名称`：节点名称
- `地区`：节点所在地区
- `带宽`：节点带宽限制
- `允许端口`：允许使用的端口范围
- `允许类型`：允许的隧道类型
- `状态`：在线（🟢）/ 离线（🔴）

## API 接口

### 获取隧道列表
```
GET /api/tunnels
```
**返回数据**：
```json
{
  "proxies": [
    {
      "proxyId": 1,
      "proxyName": "test",
      "proxyType": "tcp",
      "localIp": "127.0.0.1",
      "localPort": 8080,
      "remotePort": 12345,
      "nodeId": 1,
      "isOnline": true,
      "isDisabled": false,
      ...
    }
  ],
  "nodes": [
    {
      "nodeId": 1,
      "name": "月球 ①"
    }
  ]
}
```

### 获取创建隧道所需数据
```
GET /api/create_proxy_data
```
**返回数据**：
```json
{
  "nodes": [
    {
      "nodeId": 1,
      "name": "月球 ①",
      "description": "测试节点",
      "allowPort": "40000-65535",
      "allowType": "tcp;udp",
      "region": "cn",
      "bandwidth": "200Mbps",
      "isOnline": true
    }
  ],
  "groups": [
    {
      "name": "default",
      "friendlyName": "正式用户",
      "maxProxies": 10,
      "baseTraffic": 16384
    }
  ],
  "currentGroup": "default"
}
```

### 创建隧道
```
POST /api/create_tunnel
Content-Type: application/json

{
  "node_id": 1,
  "name": "my-tunnel",
  "proxy_type": "tcp",
  "local_ip": "127.0.0.1",
  "local_port": 8080,
  "remote_port": 12345,
  "use_encryption": false,
  "use_compression": false
}
```

### 删除隧道
```
POST /api/delete_tunnel
Content-Type: application/json

{
  "id": 1
}
```

### 切换隧道状态
```
POST /api/close_tunnel
Content-Type: application/json

{
  "id": 1
}
```

### 获取节点列表
```
GET /api/nodes
```
**返回数据**：
```json
{
  "nodes": [
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
  ]
}
```

## 使用流程

### 创建 TCP 隧道示例

1. **登录 WebUI**
2. **进入隧道管理**：点击左侧菜单"隧道管理"
3. **加载节点数据**：点击"加载节点数据"按钮
4. **填写表单**：
   - 选择节点：如"月球 ①"
   - 隧道名称：`my-tcp-tunnel`
   - 隧道类型：`TCP`
   - 本地 IP：`127.0.0.1`
   - 本地端口：`8080`
   - 远程端口：（留空自动分配）
5. **创建隧道**：点击"创建隧道"按钮
6. **查看结果**：隧道将出现在上方的隧道列表中

### 创建 HTTP 隧道示例

1. **登录 WebUI**
2. **进入隧道管理**
3. **加载节点数据**
4. **填写表单**：
   - 选择节点：选择一个支持 HTTP 的节点
   - 隧道名称：`my-http-tunnel`
   - 隧道类型：`HTTP`
   - 本地 IP：`127.0.0.1`
   - 本地端口：`3000`
   - 子域名：`myapp`
5. **额外配置**：
   - HTTP 插件：选择需要的插件
   - 访问密码：（可选）设置 HTTP Basic 认证
6. **创建隧道**

## 注意事项

1. **端口范围**：不同节点有不同的允许端口范围，请查看节点信息
2. **隧道限制**：不同用户组有不同的最大隧道数量限制
3. **流量限制**：注意查看用户的剩余流量
4. **隧道类型**：确保选择的节点支持您需要的隧道类型
5. **在线状态**：隧道需要 MEFrp 客户端连接才能显示为"在线"
6. **HTTP/HTTPS**：HTTP 和 HTTPS 隧道需要额外配置证书（crtPath/keyPath）

## 常见问题

### Q: 创建隧道失败？
**A**: 检查以下内容：
- 是否已登录
- 节点是否在线
- 端口是否在允许范围内
- 是否超过隧道数量限制
- 是否超过流量限制

### Q: 隧道显示离线？
**A**: 
- 确保 MEFrp 客户端正在运行
- 确保客户端配置正确
- 检查本地服务是否正常运行

### Q: 无法选择某个节点？
**A**: 
- 该节点可能已禁用（isDisabled: true）
- 您可能不在该节点允许的用户组中

### Q: HTTP/HTTPS 隧道创建失败？
**A**: 
- 检查是否需要配置 SSL 证书
- 检查子域名是否已被占用
- 查看节点是否支持 HTTP/HTTPS 类型
