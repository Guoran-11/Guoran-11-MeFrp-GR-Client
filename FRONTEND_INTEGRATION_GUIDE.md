# MEFrp WebUI 前端集成指南

## 📚 基于 apidoc.mefrp.com 的完整前端 API 调用指南

---

## 🎯 前端 API 调用方式

### 1. GET 请求（无参数）

```javascript
// 使用 apiCall（显示结果）
const result = await apiCall('GET', '/api/public/statistics');

// 使用 apiCallSilent（后台静默）
const result = await apiCallSilent('GET', '/api/public/statistics');
```

### 2. GET 请求（带查询参数）

```javascript
// 获取用户日志（分页）
const result = await apiCall('GET', '/api/user/logs?page=1&pageSize=20');

// 获取节点状态
const result = await apiCallSilent('GET', '/api/node/status/1');
```

### 3. POST 请求（JSON Body）

```javascript
// 创建隧道
const tunnelData = {
    node_id: 1,
    name: 'my-tunnel',
    proxy_type: 'tcp',
    local_ip: '127.0.0.1',
    local_port: 8080,
    use_encryption: false,
    use_compression: false
};

const result = await apiCallSilent('POST', '/api/create_tunnel', tunnelData);
```

### 4. DELETE 请求

```javascript
// 删除隧道
const result = await apiCallSilent('DELETE', `/api/delete_tunnel/${proxyId}`);
```

---

## 📋 新增 API 调用示例

### 1. 公共信息 API

#### 获取统计信息

```javascript
async function loadStatistics() {
    try {
        const result = await apiCallSilent('GET', '/api/public/statistics');
        
        if (result && result.code === 200) {
            const { users, nodes, proxies, traffic } = result.data;
            console.log(`用户数: ${users}`);
            console.log(`节点数: ${nodes}`);
            console.log(`隧道数: ${proxies}`);
            console.log(`总流量: ${traffic} bytes`);
        }
    } catch (error) {
        console.error('获取统计信息失败:', error);
    }
}
```

#### 获取商城商品

```javascript
async function loadStoreProducts() {
    try {
        const result = await apiCallSilent('GET', '/api/public/store/products');
        
        if (result && result.code === 200) {
            const products = result.data;
            products.forEach(product => {
                console.log(`${product.name}: ¥${product.price}/${product.unit}`);
            });
        }
    } catch (error) {
        console.error('获取商城商品失败:', error);
    }
}
```

### 2. 注册相关 API

#### 发送注册验证码

```javascript
async function sendRegisterCaptcha() {
    const email = document.getElementById('email').value;
    const captchaToken = '从验证码弹窗获取的token';
    
    try {
        const result = await apiCallSilent('POST', '/api/public/register/send', {
            email: email,
            captchaToken: captchaToken
        });
        
        if (result.code === 200) {
            showNotification('验证码已发送到邮箱', 'success');
        } else {
            showNotification(result.message || '发送失败', 'error');
        }
    } catch (error) {
        console.error('发送验证码失败:', error);
    }
}
```

#### 注册账户

```javascript
async function registerAccount() {
    const email = document.getElementById('email').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const code = document.getElementById('emailCode').value;
    
    try {
        const result = await apiCall('POST', '/api/public/register', {
            email: email,
            username: username,
            password: password,
            code: code
        });
        
        if (result.code === 200) {
            showNotification('注册成功！', 'success');
            // 自动登录或跳转到登录页
        } else {
            showNotification(result.message || '注册失败', 'error');
        }
    } catch (error) {
        console.error('注册失败:', error);
    }
}
```

### 3. 重置密码相关 API

#### 发送重置密码验证码

```javascript
async function sendResetPasswordCaptcha() {
    const email = document.getElementById('resetEmail').value;
    const captchaToken = '从验证码弹窗获取的token';
    
    try {
        const result = await apiCallSilent('POST', '/api/public/reset/send', {
            email: email,
            captchaToken: captchaToken
        });
        
        if (result.code === 200) {
            showNotification('验证码已发送到邮箱', 'success');
        } else {
            showNotification(result.message || '发送失败', 'error');
        }
    } catch (error) {
        console.error('发送验证码失败:', error);
    }
}
```

#### 重置密码

```javascript
async function resetPassword() {
    const email = document.getElementById('resetEmail').value;
    const code = document.getElementById('resetCode').value;
    const newPassword = document.getElementById('newPassword').value;
    
    try {
        const result = await apiCall('POST', '/api/public/reset', {
            email: email,
            code: code,
            password: newPassword
        });
        
        if (result.code === 200) {
            showNotification('密码重置成功！', 'success');
            // 跳转到登录页
        } else {
            showNotification(result.message || '重置失败', 'error');
        }
    } catch (error) {
        console.error('密码重置失败:', error);
    }
}
```

### 4. 用户相关 API

#### 获取 frpToken

```javascript
async function loadFrpToken() {
    try {
        const result = await apiCallSilent('GET', '/api/user/frp_token');
        
        if (result && result.code === 200) {
            const { frpToken, username } = result.data;
            console.log('frpToken:', frpToken);
            console.log('username:', username);
            // 显示到界面上
        }
    } catch (error) {
        console.error('获取 frpToken 失败:', error);
    }
}
```

#### 获取用户组信息

```javascript
async function loadUserGroup() {
    try {
        const result = await apiCallSilent('GET', '/api/user/group');
        
        if (result && result.code === 200) {
            const { name, friendlyName, maxProxies, baseTraffic, outBound, inBound } = result.data;
            console.log('用户组:', friendlyName);
            console.log('最大隧道数:', maxProxies);
            console.log('基础流量:', baseTraffic, 'GB');
            console.log('入站带宽:', inBound, 'Mbps');
            console.log('出站带宽:', outBound, 'Mbps');
        }
    } catch (error) {
        console.error('获取用户组信息失败:', error);
    }
}
```

#### 修改密码

```javascript
async function changePassword() {
    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    
    try {
        const result = await apiCall('POST', '/api/user/change_password', {
            oldPassword: oldPassword,
            newPassword: newPassword
        });
        
        if (result.code === 200) {
            showNotification('密码修改成功！', 'success');
        } else {
            showNotification(result.message || '修改失败', 'error');
        }
    } catch (error) {
        console.error('修改密码失败:', error);
    }
}
```

#### 获取用户操作日志

```javascript
async function loadUserLogs(page = 1, pageSize = 20) {
    try {
        const result = await apiCallSilent('GET', `/api/user/logs?page=${page}&pageSize=${pageSize}`);
        
        if (result && result.code === 200) {
            const { data, total, page: currentPage, totalPages } = result.data;
            console.log(`第 ${currentPage}/${totalPages} 页，共 ${total} 条记录`);
            
            data.forEach(log => {
                console.log(`[${log.createdAt}] ${log.category}: ${log.details} (${log.status})`);
            });
        }
    } catch (error) {
        console.error('获取操作日志失败:', error);
    }
}
```

#### 获取日志统计

```javascript
async function loadLogStats() {
    try {
        const result = await apiCallSilent('GET', '/api/user/log_stats');
        
        if (result && result.code === 200) {
            const { todayCount, weekCount, monthCount, totalCount } = result.data;
            console.log('今日日志:', todayCount);
            console.log('本周日志:', weekCount);
            console.log('本月日志:', monthCount);
            console.log('总日志数:', totalCount);
        }
    } catch (error) {
        console.error('获取日志统计失败:', error);
    }
}
```

### 5. 隧道相关 API

#### 获取单一隧道配置

```javascript
async function loadTunnelConfig(proxyId) {
    try {
        const result = await apiCallSilent('GET', `/api/tunnel/config/${proxyId}`);
        
        if (result && result.code === 200) {
            const { config, type } = result.data;
            console.log('隧道配置:', config);
            console.log('隧道类型:', type);
            // 显示配置内容
        }
    } catch (error) {
        console.error('获取隧道配置失败:', error);
    }
}
```

#### 更新隧道

```javascript
async function updateTunnel(proxyId) {
    const newData = {
        localIp: '127.0.0.1',
        localPort: 9090,
        useEncryption: true,
        useCompression: false
    };
    
    try {
        const result = await apiCall('POST', `/api/update_tunnel/${proxyId}`, newData);
        
        if (result.code === 200) {
            showNotification('隧道更新成功！', 'success');
            // 刷新隧道列表
        } else {
            showNotification(result.message || '更新失败', 'error');
        }
    } catch (error) {
        console.error('更新隧道失败:', error);
    }
}
```

#### 强制下线隧道

```javascript
async function kickTunnel(proxyId) {
    if (!confirm('确定要强制下线该隧道吗？')) {
        return;
    }
    
    try {
        const result = await apiCallSilent('POST', `/api/kick_tunnel/${proxyId}`);
        
        if (result.code === 200) {
            showNotification('隧道已强制下线', 'success');
            // 刷新隧道列表
        } else {
            showNotification(result.message || '操作失败', 'error');
        }
    } catch (error) {
        console.error('强制下线失败:', error);
    }
}
```

### 6. 节点相关 API

#### 获取节点列表

```javascript
async function loadNodeList() {
    try {
        const result = await apiCallSilent('GET', '/api/node/list');
        
        if (result && result.code === 200) {
            const nodes = result.data;
            nodes.forEach(node => {
                console.log(`${node.name} - ${node.region} - ${node.bandwidth} - ${node.isOnline ? '在线' : '离线'}`);
            });
        }
    } catch (error) {
        console.error('获取节点列表失败:', error);
    }
}
```

#### 获取节点连接地址

```javascript
async function loadNodeConnection() {
    try {
        const result = await apiCallSilent('GET', '/api/node/connection');
        
        if (result && result.code === 200) {
            const connections = result.data;
            connections.forEach(conn => {
                console.log(`${conn.name}: ${conn.hostname}:${conn.servicePort}`);
            });
        }
    } catch (error) {
        console.error('获取节点连接地址失败:', error);
    }
}
```

#### 获取节点状态

```javascript
async function loadNodeStatus(nodeId) {
    try {
        const result = await apiCallSilent('GET', `/api/node/status/${nodeId}`);
        
        if (result && result.code === 200) {
            const { name, onlineClient, onlineProxy, isOnline, version, uptime, loadPercent } = result.data;
            console.log(`节点: ${name}`);
            console.log(`状态: ${isOnline ? '在线' : '离线'}`);
            console.log(`在线客户端: ${onlineClient}`);
            console.log(`在线隧道: ${onlineProxy}`);
            console.log(`负载: ${loadPercent}%`);
            console.log(`版本: ${version}`);
        }
    } catch (error) {
        console.error('获取节点状态失败:', error);
    }
}
```

#### 获取节点 Token

```javascript
async function loadNodeToken(nodeId) {
    try {
        const result = await apiCallSilent('GET', `/api/node/token/${nodeId}`);
        
        if (result && result.code === 200) {
            const { token } = result.data;
            console.log('节点 Token:', token);
            // 显示到界面上
        }
    } catch (error) {
        console.error('获取节点 Token 失败:', error);
    }
}
```

### 7. 系统相关 API

#### 获取系统状态

```javascript
async function loadSystemStatus() {
    try {
        const result = await apiCallSilent('GET', '/api/system/status');
        
        if (result && result.code === 200) {
            const { status, remark } = result.data;
            console.log(`系统状态: ${status === 1 ? '正常' : '异常'}`);
            console.log(`备注: ${remark}`);
        }
    } catch (error) {
        console.error('获取系统状态失败:', error);
    }
}
```

#### 获取重要公告

```javascript
async function loadAnnouncement() {
    try {
        const result = await apiCallSilent('GET', '/api/system/announcement');
        
        if (result && result.code === 200) {
            const announcements = result.data;
            announcements.forEach(item => {
                console.log(`[${item.id}] ${item.title}`);
                console.log(item.content);
                console.log('---');
            });
        }
    } catch (error) {
        console.error('获取公告失败:', error);
    }
}
```

---

## 🎨 前端界面集成建议

### 1. 统计信息展示

**位置**：控制面板首页

```html
<div class="stats-cards">
    <div class="stat-card">
        <i class="fas fa-users"></i>
        <div class="stat-info">
            <span class="stat-value" id="totalUsers">--</span>
            <span class="stat-label">总用户数</span>
        </div>
    </div>
    <div class="stat-card">
        <i class="fas fa-server"></i>
        <div class="stat-info">
            <span class="stat-value" id="totalNodes">--</span>
            <span class="stat-label">节点总数</span>
        </div>
    </div>
    <div class="stat-card">
        <i class="fas fa-network-wired"></i>
        <div class="stat-info">
            <span class="stat-value" id="totalProxies">--</span>
            <span class="stat-label">隧道总数</span>
        </div>
    </div>
    <div class="stat-card">
        <i class="fas fa-cloud"></i>
        <div class="stat-info">
            <span class="stat-value" id="totalTraffic">--</span>
            <span class="stat-label">总流量</span>
        </div>
    </div>
</div>
```

```javascript
// 页面加载时获取统计信息
async function loadDashboardStats() {
    await loadStatistics();
    await loadSystemStatus();
    await loadAnnouncement();
}

// 页面加载时自动调用
document.addEventListener('DOMContentLoaded', loadDashboardStats);
```

### 2. 用户中心页面

**位置**：左侧菜单 → 用户中心

```html
<div class="user-center">
    <div class="user-info-section">
        <h3>基本信息</h3>
        <button onclick="loadUserInfo()">刷新信息</button>
        <button onclick="loadFrpToken()">查看 frpToken</button>
        <button onclick="loadUserGroup()">用户组详情</button>
    </div>
    
    <div class="password-section">
        <h3>修改密码</h3>
        <input type="password" id="oldPassword" placeholder="旧密码">
        <input type="password" id="newPassword" placeholder="新密码">
        <button onclick="changePassword()">确认修改</button>
    </div>
    
    <div class="logs-section">
        <h3>操作日志</h3>
        <button onclick="loadUserLogs(1)">查看日志</button>
        <div id="logsContainer"></div>
    </div>
</div>
```

### 3. 节点监控页面

**位置**：左侧菜单 → 节点监控

```html
<div class="node-monitor">
    <div class="node-filters">
        <select id="nodeRegionFilter">
            <option value="">全部地区</option>
            <option value="cn">中国大陆</option>
            <option value="hk">香港</option>
            <option value="us">美国</option>
        </select>
        <button onclick="loadNodeList()">刷新列表</button>
    </div>
    
    <table class="data-table">
        <thead>
            <tr>
                <th>节点名称</th>
                <th>地区</th>
                <th>带宽</th>
                <th>允许端口</th>
                <th>状态</th>
                <th>负载</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody id="nodeTableBody">
            <!-- 动态填充 -->
        </tbody>
    </table>
</div>
```

```javascript
// 加载节点列表并渲染表格
async function loadNodeListAndRender() {
    try {
        const result = await apiCallSilent('GET', '/api/node/list');
        
        if (result && result.code === 200) {
            const tbody = document.getElementById('nodeTableBody');
            tbody.innerHTML = '';
            
            result.data.forEach(node => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${node.name}</td>
                    <td>${node.region}</td>
                    <td>${node.bandwidth}</td>
                    <td>${node.allowPort}</td>
                    <td>${node.isOnline ? '🟢 在线' : '🔴 离线'}</td>
                    <td>${node.loadPercent || '--'}%</td>
                    <td>
                        <button onclick="loadNodeStatus(${node.nodeId})">状态</button>
                        <button onclick="loadNodeToken(${node.nodeId})">Token</button>
                    </td>
                `;
            });
        }
    } catch (error) {
        console.error('加载节点列表失败:', error);
    }
}
```

### 4. 商城页面

**位置**：左侧菜单 → 更多服务 → 商城

```html
<div class="store-page">
    <h2>流量商店</h2>
    <div id="productsGrid" class="products-grid">
        <!-- 动态填充商品 -->
    </div>
</div>
```

```javascript
async function loadStoreProducts() {
    try {
        const result = await apiCallSilent('GET', '/api/public/store/products');
        
        if (result && result.code === 200) {
            const grid = document.getElementById('productsGrid');
            grid.innerHTML = '';
            
            result.data.forEach(product => {
                const card = document.createElement('div');
                card.className = 'product-card';
                card.innerHTML = `
                    <h3>${product.name}</h3>
                    <p class="price">¥${product.price}/${product.unit}</p>
                    <p class="description">${product.description}</p>
                    <button ${!product.enabled ? 'disabled' : ''}>购买</button>
                `;
                grid.appendChild(card);
            });
        }
    } catch (error) {
        console.error('加载商城商品失败:', error);
    }
}
```

---

## 🔐 权限说明

| API 路径 | 权限要求 | 说明 |
|---------|---------|------|
| `/api/public/*` | 无需登录 | 公开接口 |
| `/api/*` (需登录) | 需要 Token | 用户认证接口 |
| `/api/user/*` | 需要登录 | 用户专属接口 |
| `/api/node/*` | 需要登录 | 节点相关接口 |
| `/api/tunnel/*` | 需要登录 | 隧道相关接口 |
| `/api/system/*` | 无需登录 | 系统公开接口 |

---

## 📝 错误处理示例

```javascript
async function safeApiCall(method, endpoint, data = null) {
    try {
        const result = data 
            ? await apiCall(method, endpoint, data)
            : await apiCall(method, endpoint);
        
        if (result.code === 200) {
            return { success: true, data: result };
        } else if (result.code === 401) {
            showNotification('请先登录', 'warning');
            showLoginModal();
            return { success: false, error: '未登录' };
        } else if (result.code === 403) {
            showNotification('权限不足', 'error');
            return { success: false, error: '权限不足' };
        } else {
            showNotification(result.message || '操作失败', 'error');
            return { success: false, error: result.message };
        }
    } catch (error) {
        console.error('API 调用失败:', error);
        showNotification('网络错误，请稍后重试', 'error');
        return { success: false, error: error.message };
    }
}
```

---

**文档版本：** v1.0
**最后更新：** 2026-05-27
**参考文档：** https://apidoc.mefrp.com/
