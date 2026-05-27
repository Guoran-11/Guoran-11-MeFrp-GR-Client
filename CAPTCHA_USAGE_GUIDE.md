# MEFrp WebUI 人机验证使用指南

## 验证码地址

**正确地址**：
```
https://www.mefrp.com/3rdparty/captcha?client=CODENAME
```

**错误地址（已废弃）**：
```
https://captcha.mefrp.com/captcha.html?appId=657e7dd0e6d4d30001a7c7c5
```

## 需要验证码的 API

根据 MEFrpLib 源码，以下 API 需要人机验证码（captchaToken）：

### 1. 登录 API
```python
client.login(username, password, captcha_token)
```
- **路由**：`POST /api/login`
- **用途**：用户登录
- **是否需要验证码**：是（可选，但建议使用）

### 2. 注册发送邮箱验证码
```python
client.get_register_email_code(email, captcha_token)
```
- **路由**：`POST /api/send_register_email`
- **用途**：注册时获取邮箱验证码
- **是否需要验证码**：是

### 3. 用户签到
```python
client.sign(captcha_token)
```
- **路由**：`POST /api/sign`
- **用途**：每日签到获取奖励
- **是否需要验证码**：是

### 4. Token 刷新
```python
client.reset_token(captcha_token)
```
- **路由**：`POST /api/refresh_token`
- **用途**：刷新用户 Token
- **是否需要验证码**：是

## 验证码使用流程

### Step 1: 打开验证码页面
用户点击"获取验证码"按钮，弹出验证码窗口：
```
https://www.mefrp.com/3rdparty/captcha?client=CODENAME
```

### Step 2: 完成人机验证
用户在弹出的窗口中完成验证码挑战（可能是滑动验证、点选验证等）

### Step 3: 获取验证码 Token
验证成功后，页面会返回一个 token，通常是：
- 直接在页面上显示 token
- 或者通过 URL 参数传递
- 或者通过 JavaScript 回调函数返回

### Step 4: 填写验证码
用户将获取的 token 复制到输入框中

### Step 5: 提交操作
用户点击提交按钮（如"登录"、"签到"等）

## 在 WebUI 中的使用

### 登录验证码
- **位置**：登录模态框中的"获取验证码"按钮
- **Token 输入**：`loginCaptcha` 输入框
- **提交**：登录表单提交时一起发送

### 签到验证码
- **位置**：控制面板中的签到区域
- **Token 输入**：`signCaptcha` 输入框
- **提交**："确认签到"按钮

## 注意事项

1. **每个验证码只能用一次**
2. **验证码有时效性**，获取后应尽快使用
3. **不要频繁请求验证码**，可能被风控
4. **CODENAME 是客户端标识符**，用于标识第三方客户端
5. **验证失败或取消**，Token 为空或无效

## 错误处理

如果验证码相关操作失败，可能的原因：

1. **验证码已过期** - 需要重新获取
2. **验证码已使用** - 每个验证码只能用一次
3. **验证未完成** - 用户取消了验证流程
4. **风控拦截** - 请求过于频繁
5. **Token 格式错误** - 验证码格式不正确

## 示例代码

### 前端（JavaScript）
```javascript
// 打开验证码
document.getElementById('getCaptchaBtn').addEventListener('click', () => {
    window.open(
        'https://www.mefrp.com/3rdparty/captcha?client=CODENAME',
        'captcha',
        'width=400,height=500'
    );
});

// 提交操作
document.getElementById('submitBtn').addEventListener('click', async () => {
    const captchaToken = document.getElementById('captchaInput').value;
    
    const result = await apiCall('POST', '/api/sign', {
        captcha_token: captchaToken
    });
    
    if (result.error) {
        alert('操作失败：' + result.error);
    } else {
        alert('操作成功！');
    }
});
```

### 后端（Python/Flask）
```python
@app.route('/api/sign', methods=['POST'])
def api_sign():
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    data = request.json
    captcha_token = data.get('captcha_token', 'test')
    
    try:
        result = client.sign(captcha_token)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## 总结

人机验证是 MEFrp API 的重要安全机制，主要用于：
- 防止自动化脚本滥用 API
- 保护用户账户安全
- 减少恶意请求

在使用需要验证码的 API 时，务必：
1. 先让用户完成验证
2. 获取有效的验证码 Token
3. 在请求中携带正确的 Token
4. 处理验证失败的错误情况
