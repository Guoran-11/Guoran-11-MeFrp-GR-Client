# 隧道创建问题修复

## 🐛 问题描述

**错误信息：**
```
MEFrpClient.create_proxy() got an unexpected keyword argument 'node_id'
```

**问题原因：**
MEFrpLib 库期望使用**驼峰命名格式**（`camelCase`）的参数，但代码中错误地使用了下划线命名格式（`snake_case`）。

## 🔧 修复方案

### 参数名称映射

**修复前（错误）：**
```python
req_data = {
    'node_id': int(data['node_id']),     # ❌ 错误
    'name': data['name'],                # ❌ 错误
    'local_ip': data['local_ip'],        # ❌ 错误
    'local_port': int(data['local_port']),# ❌ 错误
    'proxy_type': data.get('proxy_type'), # ❌ 错误
    # ... 其他参数
}
```

**修复后（正确）：**
```python
req_data = {
    'nodeId': int(data['node_id']),      # ✅ 正确
    'proxyName': data['name'],           # ✅ 正确
    'localIp': data['local_ip'],         # ✅ 正确
    'localPort': int(data['local_port']),# ✅ 正确
    'proxyType': data.get('proxy_type'), # ✅ 正确
    # ... 其他参数
}
```

### 完整参数列表

| 参数名称（驼峰） | 类型 | 说明 |
|-----------------|------|------|
| `nodeId` | int | 节点ID |
| `proxyName` | str | 隧道名称 |
| `localIp` | str | 本地IP地址 |
| `localPort` | int | 本地端口 |
| `proxyType` | str | 隧道类型（TCP/UDP/HTTP/HTTPS） |
| `remotePort` | int | 远程端口（可选） |
| `domain` | str | 子域名（HTTP/HTTPS） |
| `httpPlugin` | str | HTTP插件（可选） |
| `httpUser` | str | HTTP认证用户名（可选） |
| `httpPassword` | str | HTTP认证密码（可选） |
| `crtPath` | str | SSL证书路径（可选） |
| `keyPath` | str | SSL密钥路径（可选） |
| `accessKey` | str | 访问密钥（可选） |
| `hostHeaderRewrite` | str | Host头重写（可选） |
| `useEncryption` | bool | 是否启用加密 |
| `useCompression` | bool | 是否启用压缩 |

## ✅ 修复内容

**文件：** `app.py`

**修改位置：** `/api/create_proxy` 接口（第268-306行）

**修改内容：**
1. 将 `node_id` 改为 `nodeId`
2. 将 `name` 改为 `proxyName`
3. 将 `local_ip` 改为 `localIp`
4. 将 `local_port` 改为 `localPort`
5. 将 `proxy_type` 改为 `proxyType`
6. 将 `remote_port` 改为 `remotePort`
7. 将 `http_plugin` 改为 `httpPlugin`
8. 将 `http_user` 改为 `httpUser`
9. 将 `http_password` 改为 `httpPassword`
10. 将 `crt_path` 改为 `crtPath`
11. 将 `key_path` 改为 `keyPath`
12. 将 `access_key` 改为 `accessKey`
13. 将 `host_header_rewrite` 改为 `hostHeaderRewrite`
14. 将 `use_encryption` 改为 `useEncryption`
15. 将 `use_compression` 改为 `useCompression`

## 🔍 验证依据

从 MEFrpLib 的模型定义中可以看到，API 期望使用驼峰命名格式：

```python
@dataclass
class Proxy:
    proxyId: int
    proxyName: str
    proxyType: str
    localIp: str
    localPort: int
    remotePort: int
    nodeId: int
    useEncryption: bool
    useCompression: bool
    httpPlugin: str
    httpUser: str
    httpPassword: str
    crtPath: str
    keyPath: str
    accessKey: str
    hostHeaderRewrite: str
```

## 🚀 测试建议

1. **重启服务**：关闭并重新启动 WebUI
2. **登录**：确保已登录
3. **进入隧道管理**：点击左侧"隧道管理"
4. **加载节点数据**：点击"加载节点数据"按钮
5. **创建隧道**：填写表单并点击"创建隧道"按钮
6. **验证结果**：检查是否成功创建

## 📝 注意事项

- ✅ 参数名称必须使用驼峰命名格式（camelCase）
- ✅ 确保所有参数名称与 MEFrpLib 模型定义一致
- ✅ 如果遇到类似错误，检查参数名称是否正确

## 📞 技术支持

如果问题仍然存在：
1. 查看服务器日志
2. 检查 MEFrpLib 版本
3. 联系 MEFrp 交流群

---

**修复日期：** 2026-05-27
**修复版本：** v1.1.2
