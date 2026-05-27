# MEFrp 创建隧道 API 文档规范

## 参考文档

[创建隧道 API 文档](https://apidoc.mefrp.com/%E5%88%9B%E5%BB%BA%E9%9A%A7%E9%81%93-416605311e0)

## API 端点

**POST** `/auth/proxy/create`

## 请求参数

### 必填参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `nodeId` | int | 节点ID |
| `proxyName` | string | 隧道名称（字母、数字、下划线、连字符） |
| `proxyType` | string | 隧道类型：`TCP`、`UDP`、`HTTP`、`HTTPS` |
| `localIp` | string | 本地服务 IP 地址 |
| `localPort` | int | 本地服务端口 |

### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `remotePort` | int | 远程端口（留空自动分配） |
| `domain` | string | 子域名（HTTP/HTTPS 专用） |
| `httpPlugin` | string | HTTP 插件：`http2https`、`https2http`、`https2https` |
| `httpUser` | string | HTTP Basic 认证用户名 |
| `httpPassword` | string | HTTP Basic 认证密码 |
| `crtPath` | string | SSL 证书路径 |
| `keyPath` | string | SSL 密钥路径 |
| `accessKey` | string | 访问密钥 |
| `hostHeaderRewrite` | string | Host 头重写 |
| `useEncryption` | bool | 是否启用加密（默认 false） |
| `useCompression` | bool | 是否启用压缩（默认 false） |

## 响应格式

### 成功响应

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
    "success": true,
    "message": "创建成功"
}
```

### 失败响应

```json
{
    "code": 400,
    "success": false,
    "message": "参数错误"
}
```

## 代码实现

### 后端处理（app.py）

```python
@app.route('/api/create_tunnel', methods=['POST'])
def api_create_tunnel():
    client = get_client()
    data = request.json
    
    # 验证必填参数（前端发送的是下划线格式）
    required = ['node_id', 'name', 'proxy_type', 'local_ip', 'local_port']
    if not client or any(k not in data for k in required):
        return jsonify({'error': '缺少必要参数或未登录'}), 400
    
    # 构建请求数据（转换为驼峰命名格式）
    req_data = {
        'nodeId': int(data['node_id']),
        'proxyName': data['name'],
        'proxyType': data['proxy_type'].upper(),
        'localIp': data['local_ip'],
        'localPort': int(data['local_port']),
    }
    
    # 添加可选参数
    if data.get('remote_port'):
        req_data['remotePort'] = int(data['remote_port'])
    
    if data.get('domain'):
        req_data['domain'] = data['domain']
    
    if data.get('http_plugin'):
        req_data['httpPlugin'] = data['http_plugin']
    
    if data.get('http_user'):
        req_data['httpUser'] = data['http_user']
    
    if data.get('http_password'):
        req_data['httpPassword'] = data['http_password']
    
    if data.get('crt_path'):
        req_data['crtPath'] = data['crt_path']
    
    if data.get('key_path'):
        req_data['keyPath'] = data['key_path']
    
    if data.get('access_key'):
        req_data['accessKey'] = data['access_key']
    
    if data.get('host_header_rewrite'):
        req_data['hostHeaderRewrite'] = data['host_header_rewrite']
    
    req_data['useEncryption'] = data.get('use_encryption', False)
    req_data['useCompression'] = data.get('use_compression', False)
    
    try:
        result = client.create_proxy(req_data)
        
        if result and (result.get('code') == 200 or result.get('success')):
            # 创建成功后自动启用隧道
            proxy_id = result.get('data', {}).get('proxyId')
            if proxy_id:
                client.toggle_proxy(proxy_id)
            return jsonify(result)
        
        return jsonify({'error': result.get('message', '创建失败')}), 400
    
    except Exception as e:
        print(f"创建隧道失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
```

### 前端发送（index.html）

```javascript
const tunnelData = {
    node_id: parseInt(nodeId),
    name: proxyName,
    proxy_type: proxyType,
    local_ip: localIp,
    local_port: parseInt(localPort),
    remote_port: remotePort ? parseInt(remotePort) : undefined,
    domain: document.getElementById('createDomain').value || '',
    http_plugin: document.getElementById('createHttpPlugin').value || '',
    http_user: document.getElementById('createHttpUser').value || '',
    http_password: document.getElementById('createHttpPassword').value || '',
    use_encryption: document.getElementById('createUseEncryption').checked,
    use_compression: document.getElementById('createUseCompression').checked
};

const result = await apiCallSilent('POST', '/api/create_tunnel', tunnelData);
```

## 参数映射表

| 前端参数（下划线） | 后端参数（驼峰） | MEFrpLib 参数 |
|------------------|-----------------|--------------|
| `node_id` | `nodeId` | ✅ |
| `name` | `proxyName` | ✅ |
| `proxy_type` | `proxyType` | ✅ |
| `local_ip` | `localIp` | ✅ |
| `local_port` | `localPort` | ✅ |
| `remote_port` | `remotePort` | ✅ |
| `domain` | `domain` | ✅ |
| `http_plugin` | `httpPlugin` | ✅ |
| `http_user` | `httpUser` | ✅ |
| `http_password` | `httpPassword` | ✅ |
| `crt_path` | `crtPath` | ✅ |
| `key_path` | `keyPath` | ✅ |
| `access_key` | `accessKey` | ✅ |
| `host_header_rewrite` | `hostHeaderRewrite` | ✅ |
| `use_encryption` | `useEncryption` | ✅ |
| `use_compression` | `useCompression` | ✅ |

## 注意事项

1. **参数命名**：前端使用下划线命名，后端转换为驼峰命名
2. **类型转换**：端口号需要转换为整数类型
3. **可选参数**：只有在有值时才添加到请求中
4. **错误处理**：需要捕获并处理 API 异常
5. **自动启用**：创建成功后自动启用隧道

## 测试建议

### 测试用例 1：创建 TCP 隧道

```bash
curl -X POST http://localhost:5000/api/create_tunnel \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": 1,
    "name": "test-tcp",
    "proxy_type": "tcp",
    "local_ip": "127.0.0.1",
    "local_port": 8080
  }'
```

### 测试用例 2：创建 HTTP 隧道

```bash
curl -X POST http://localhost:5000/api/create_tunnel \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": 2,
    "name": "test-http",
    "proxy_type": "http",
    "local_ip": "127.0.0.1",
    "local_port": 80,
    "domain": "myapp",
    "http_plugin": "http2https"
  }'
```

### 测试用例 3：创建带加密压缩的隧道

```bash
curl -X POST http://localhost:5000/api/create_tunnel \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": 1,
    "name": "test-encrypted",
    "proxy_type": "tcp",
    "local_ip": "127.0.0.1",
    "local_port": 22,
    "use_encryption": true,
    "use_compression": true
  }'
```

## 常见错误

### 错误 1：参数缺失

**错误信息**：`缺少必要参数或未登录`

**解决方案**：确保所有必填参数都已提供

### 错误 2：节点 ID 无效

**错误信息**：`节点不存在`

**解决方案**：使用有效的节点 ID，可通过 `/api/create_proxy_data` 获取可用节点列表

### 错误 3：隧道名称重复

**错误信息**：`隧道名称已存在`

**解决方案**：使用唯一的隧道名称

### 错误 4：端口被占用

**错误信息**：`端口已被占用`

**解决方案**：选择其他端口或留空自动分配

---

**文档版本**：v1.0  
**最后更新**：2026-05-27  
**参考文档**：https://apidoc.mefrp.com/%E5%88%9B%E5%BB%BA%E9%9A%A7%E9%81%93-416605311e0
