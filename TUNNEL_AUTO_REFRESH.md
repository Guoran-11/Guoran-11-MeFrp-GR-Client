# 隧道管理优化说明

## 2026-05-27 更新

### 🎯 本次优化内容

#### 1. 优化节点选择界面

**问题：** 创建隧道表单中，各字段之间的空白区域太大，导致界面不紧凑。

**解决方案：**
- ✅ 减小表单字段之间的间距（从默认改为 0.8rem）
- ✅ 优化标签和输入框的内边距（使用紧凑型样式）
- ✅ 缩小辅助说明文字的字号
- ✅ 调整复选框的布局，使用 flexbox 对齐

**优化前：**
```html
<div class="form-group">
    <label>选择节点</label>
    <select class="form-control" id="createNodeSelect">
        <option>-- 请先加载节点数据 --</option>
    </select>
</div>
```

**优化后：**
```html
<div class="form-group" style="margin-bottom: 0.8rem;">
    <label style="margin-bottom: 0.3rem;">选择节点</label>
    <select class="form-control" id="createNodeSelect" 
            style="height: auto; padding: 0.5rem;">
        <option>-- 请先加载节点数据 --</option>
    </select>
    <button type="button" id="loadCreateDataBtn" 
            style="margin-top: 0.5rem; width: 100%;">
        加载节点数据
    </button>
</div>
```

#### 2. 添加隧道列表自动刷新功能

**新增功能：**
- ✅ **自动刷新**：登录后每 30 秒自动刷新隧道列表
- ✅ **后台静默**：自动刷新不显示通知，不干扰用户
- ✅ **智能控制**：退出登录自动停止刷新
- ✅ **启动触发**：登录成功后立即刷新一次
- ✅ **页面恢复**：刷新浏览器后，如果已登录则自动启动刷新

**功能特点：**

1. **登录联动**
   - 用户登录成功后自动启动自动刷新
   - 自动刷新立即执行一次
   - 刷新间隔：30 秒

2. **登出联动**
   - 用户退出登录自动停止刷新
   - 清理定时器，防止内存泄漏

3. **静默运行**
   - 不显示任何通知
   - 不干扰用户操作
   - 后台日志记录（console）

4. **状态持久化**
   - 使用 sessionStorage 记录登录状态
   - 页面刷新后可恢复自动刷新

### 📝 技术实现

#### 核心代码

```javascript
// 自动刷新定时器
let tunnelRefreshInterval = null;
const TUNNEL_REFRESH_INTERVAL = 30000; // 30秒

// 启动自动刷新
function startAutoRefresh() {
    if (tunnelRefreshInterval) {
        clearInterval(tunnelRefreshInterval);
    }
    
    // 立即刷新一次
    document.getElementById('refreshTunnelsBtn').click();
    
    // 设置定时器
    tunnelRefreshInterval = setInterval(() => {
        if (sessionStorage.getItem('loggedIn') === 'true') {
            document.getElementById('refreshTunnelsBtn').click();
        }
    }, TUNNEL_REFRESH_INTERVAL);
}

// 停止自动刷新
function stopAutoRefresh() {
    if (tunnelRefreshInterval) {
        clearInterval(tunnelRefreshInterval);
        tunnelRefreshInterval = null;
    }
}
```

#### 生命周期管理

**登录流程：**
```
用户登录 → showLoggedIn() → sessionStorage.setItem() → startAutoRefresh()
```

**登出流程：**
```
用户登出 → showLoggedOut() → stopAutoRefresh() → sessionStorage.removeItem()
```

**页面加载：**
```
页面加载 → 检查 sessionStorage → 如果已登录 → 延迟 1 秒启动自动刷新
```

### 🎨 界面优化效果

#### 表单字段优化

**优化前：**
```
标签: 选择节点
[下拉选择框                                            ]
[按钮: 加载节点数据]

（间距较大）
标签: 隧道名称
[输入框                                              ]
```

**优化后：**
```
标签: 选择节点
[下拉选择框]
[按钮: 加载节点数据]（紧凑排列）
标签: 隧道名称
[输入框]（间距紧凑）
```

**优势：**
- ✅ 界面更紧凑
- ✅ 减少滚动
- ✅ 提升填写效率
- ✅ 更现代的视觉体验

### 🚀 使用说明

#### 自动刷新功能

**无需手动操作！**

1. **登录后自动启动**
   - 登录成功后立即刷新一次隧道列表
   - 每 30 秒自动刷新一次
   - 完全后台运行，不打扰用户

2. **退出后自动停止**
   - 退出登录时停止刷新
   - 节省系统资源
   - 防止不必要的请求

3. **手动刷新按钮**
   - 仍保留手动刷新按钮
   - 可随时手动刷新
   - 有加载动画提示

**示例场景：**

**场景 1：用户登录**
```
1. 用户打开 WebUI
2. 输入 Token 登录
3. 立即显示最新的隧道列表
4. 每 30 秒自动更新一次
```

**场景 2：用户创建隧道**
```
1. 用户登录后创建新隧道
2. 30 秒内自动刷新列表
3. 新隧道自动显示在列表中
4. 无需手动点击刷新按钮
```

**场景 3：用户退出**
```
1. 用户点击退出登录
2. 自动刷新立即停止
3. 界面显示未登录状态
```

### 🔧 配置选项

#### 修改刷新间隔

如果需要调整刷新间隔，修改以下常量：

```javascript
const TUNNEL_REFRESH_INTERVAL = 30000; // 毫秒
// 30000 = 30秒
// 60000 = 1分钟
// 120000 = 2分钟
```

#### 禁用自动刷新

如果需要禁用自动刷新功能，可以注释掉相关代码：

```javascript
// 在 showLoggedIn() 函数中注释掉这两行：
// sessionStorage.setItem('loggedIn', 'true');
// startAutoRefresh();
```

### 📊 性能优化

#### 优势

1. **减少手动操作**
   - 无需频繁点击刷新按钮
   - 提高用户体验
   - 实时获取最新数据

2. **节省系统资源**
   - 使用 setInterval 定时器
   - 退出时自动清理
   - 避免内存泄漏

3. **降低服务器压力**
   - 30 秒刷新间隔合理
   - 使用后台静默请求
   - 不影响页面渲染

#### 注意事项

1. **网络流量**
   - 30 秒刷新会产生少量请求
   - 不影响正常使用
   - 适合个人用户

2. **并发场景**
   - 自动刷新会覆盖手动编辑
   - 建议重要操作后手动刷新
   - 防止数据不一致

3. **性能考虑**
   - 定时器会有轻微性能开销
   - 退出登录会自动清理
   - 适合常规使用场景

### 🐛 已知问题

#### 无

本次优化未发现已知问题。

### 🔄 后续计划

#### 计划中功能

1. **自定义刷新间隔**
   - 用户可自行设置刷新频率
   - 提供设置面板
   - 支持关闭自动刷新

2. **智能刷新**
   - 根据隧道状态智能调整刷新频率
   - 异常状态时提高刷新频率
   - 稳定状态时降低刷新频率

3. **刷新历史**
   - 记录最近的刷新结果
   - 支持查看历史状态
   - 便于问题排查

4. **通知选项**
   - 可选择是否显示刷新通知
   - 仅在异常时通知
   - 减少干扰

### 📞 技术支持

如果遇到问题：
1. 查看浏览器控制台（F12）
2. 检查网络请求
3. 联系 MEFrp 交流群

### ✅ 总结

本次更新带来了以下改进：

1. ✅ **界面优化**
   - 紧凑型表单设计
   - 减少空白区域
   - 更现代的视觉体验

2. ✅ **自动刷新**
   - 智能后台刷新
   - 免手动操作
   - 提高效率

3. ✅ **性能优化**
   - 合理刷新间隔
   - 资源自动释放
   - 静默运行不打扰

---

**最后更新：** 2026-05-27
**版本号：** v1.1.0
**维护者：** MEFrp WebUI Team
