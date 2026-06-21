# MEFrp WebUI 完整 API 实现
# 基于 https://apidoc.mefrp.com/ 文档

# ==================== 公共信息 API ====================

@app.route('/api/public/statistics', methods=['GET'])
def api_public_statistics():
    """获取用户数量、节点数量、隧道数量、已承载流量"""
    try:
        url = "https://api.mefrp.com/api/public/statistics"
        headers = {
            "User-Agent": "WebUI/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        return jsonify(result)
    except requests.exceptions.RequestException as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/public/store/products', methods=['GET'])
def api_public_store_products():
    """获取商城商品列表"""
    try:
        url = "https://api.mefrp.com/api/public/store/products"
        headers = {
            "User-Agent": "WebUI/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        return jsonify(result)
    except requests.exceptions.RequestException as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== 注册相关 API ====================

@app.route('/api/public/register/send', methods=['POST'])
def api_public_register_send():
    """发送注册验证码"""
    data = request.json
    email = data.get('email')
    captcha_token = data.get('captchaToken')
    
    if not email:
        return jsonify({'error': '邮箱不能为空'}), 400
    if not captcha_token:
        return jsonify({'error': '验证码 token 不能为空'}), 400
    
    try:
        client = MEFrpClient(user_agent='WebUI/1.0.0')
        result = client.get_register_email_code(email, captcha_token)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/public/register', methods=['POST'])
def api_public_register():
    """注册账户"""
    data = request.json
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    code = data.get('code')
    
    if not all([email, username, password, code]):
        return jsonify({'error': '所有字段都不能为空'}), 400
    
    try:
        client = MEFrpClient(user_agent='WebUI/1.0.0')
        result = client.register(username, email, code, password)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== 重置密码相关 API ====================

@app.route('/api/public/reset/send', methods=['POST'])
def api_public_reset_send():
    """发送重置密码验证码"""
    data = request.json
    email = data.get('email')
    captcha_token = data.get('captchaToken')
    
    if not email:
        return jsonify({'error': '邮箱不能为空'}), 400
    if not captcha_token:
        return jsonify({'error': '验证码 token 不能为空'}), 400
    
    try:
        client = MEFrpClient(user_agent='WebUI/1.0.0')
        result = client.get_reset_password_code(email, captcha_token)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/public/reset', methods=['POST'])
def api_public_reset():
    """重置密码"""
    data = request.json
    email = data.get('email')
    code = data.get('code')
    password = data.get('password')
    
    if not all([email, code, password]):
        return jsonify({'error': '所有字段都不能为空'}), 400
    
    try:
        client = MEFrpClient(user_agent='WebUI/1.0.0')
        result = client.reset_password_by_email(email, code, password)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== 用户相关 API ====================

@app.route('/api/user/frp_token', methods=['GET'])
def api_user_frp_token():
    """获取用户 frpToken"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    try:
        result = client.get_frp_token()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/group', methods=['GET'])
def api_user_group():
    """获取用户组信息"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    try:
        result = client.get_user_group()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/reset_token', methods=['POST'])
def api_user_reset_token():
    """重置访问密钥（需要验证码）"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    data = request.json
    captcha_token = data.get('captchaToken')
    
    try:
        result = client.reset_token(captcha_token)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/change_password', methods=['POST'])
def api_user_change_password():
    """修改密码"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    data = request.json
    old_password = data.get('oldPassword')
    new_password = data.get('newPassword')
    
    if not all([old_password, new_password]):
        return jsonify({'error': '旧密码和新密码都不能为空'}), 400
    
    try:
        result = client.change_password(old_password, new_password)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/logs', methods=['GET'])
def api_user_logs():
    """获取用户操作日志"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    
    try:
        result = client.get_operation_logs(page, page_size)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/log_stats', methods=['GET'])
def api_user_log_stats():
    """获取用户日志统计"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    try:
        result = client.get_operation_log_stats()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== 隧道相关 API ====================

@app.route('/api/delete_tunnel/<int:proxy_id>', methods=['DELETE'])
def api_delete_tunnel(proxy_id):
    """删除隧道"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    try:
        result = client.delete_proxy(proxy_id)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/kick_tunnel/<int:proxy_id>', methods=['POST'])
def api_kick_tunnel(proxy_id):
    """强制下线隧道"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    try:
        result = client.kick_proxy(proxy_id)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/tunnel/config/<int:proxy_id>', methods=['GET'])
def api_tunnel_config(proxy_id):
    """获取单一隧道配置"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    try:
        result = client.get_proxy_config(proxy_id)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/tunnels/config', methods=['POST'])
def api_tunnels_config():
    """获取多个隧道配置"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    data = request.json
    proxy_ids = data.get('proxyIds', [])
    
    if not proxy_ids:
        return jsonify({'error': 'proxyIds 不能为空'}), 400
    
    try:
        result = client.get_multiple_proxy_configs(proxy_ids)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_tunnel/<int:proxy_id>', methods=['POST'])
def api_update_tunnel(proxy_id):
    """更新隧道"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    data = request.json
    
    try:
        # 构建更新数据（使用驼峰命名）
        update_data = {}
        if 'proxyName' in data:
            update_data['proxyName'] = data['proxyName']
        if 'localIp' in data:
            update_data['localIp'] = data['localIp']
        if 'localPort' in data:
            update_data['localPort'] = int(data['localPort'])
        if 'remotePort' in data:
            update_data['remotePort'] = int(data['remotePort'])
        if 'useEncryption' in data:
            update_data['useEncryption'] = data['useEncryption']
        if 'useCompression' in data:
            update_data['useCompression'] = data['useCompression']
        if 'httpPlugin' in data:
            update_data['httpPlugin'] = data['httpPlugin']
        if 'httpUser' in data:
            update_data['httpUser'] = data['httpUser']
        if 'httpPassword' in data:
            update_data['httpPassword'] = data['httpPassword']
        if 'domain' in data:
            update_data['domain'] = data['domain']
        
        result = client.update_proxy(proxy_id, update_data)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== 节点相关 API ====================

@app.route('/api/node/list', methods=['GET'])
def api_node_list():
    """获取节点列表"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    try:
        result = client.get_node_list()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/node/connection', methods=['GET'])
def api_node_connection():
    """获取节点连接地址列表"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    try:
        result = client.get_node_connection_list()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/node/status/<int:node_id>', methods=['GET'])
def api_node_status(node_id):
    """获取节点状态"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    try:
        result = client.get_node_status(node_id)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/node/token/<int:node_id>', methods=['GET'])
def api_node_token(node_id):
    """获取节点 Token"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    try:
        result = client.get_node_token(node_id)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== 系统相关 API ====================

@app.route('/api/system/status', methods=['GET'])
def api_system_status():
    """获取系统状态"""
    try:
        url = "https://api.mefrp.com/api/public/system/status"
        headers = {
            "User-Agent": "WebUI/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        return jsonify(result)
    except requests.exceptions.RequestException as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/announcement', methods=['GET'])
def api_system_announcement():
    """获取重要公告"""
    try:
        url = "https://api.mefrp.com/api/public/announcement"
        headers = {
            "User-Agent": "WebUI/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        return jsonify(result)
    except requests.exceptions.RequestException as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== 其他 API ====================

@app.route('/api/create_proxy_data', methods=['GET'])
def api_create_proxy_data():
    """获取创建隧道所需的所有数据"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    
    try:
        result = client.get_create_proxy_data()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
