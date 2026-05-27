import os
import sys
import traceback
import requests
from flask import Flask, render_template, request, jsonify, session

# 尝试导入 MEFrpLib，如果失败则给出明确提示
try:
    from MEFrpLib import MEFrpClient
except ImportError as e:
    print(f"Error importing MEFrpLib: {e}")
    print("Please install: pip install MEFrpLib")
    sys.exit(1)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ------------------- 页面路由 -------------------
@app.route('/')
def index():
    """返回 Web UI 页面"""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"<h1>Template file missing</h1><p>Make sure templates/index.html exists</p><pre>{e}</pre>", 500

@app.route('/diagnostic')
def diagnostic():
    """返回诊断工具页面"""
    try:
        return render_template('diagnostic.html')
    except Exception as e:
        return f"<h1>Template file missing</h1><p>Make sure templates/diagnostic.html exists</p><pre>{e}</pre>", 500

# ------------------- 辅助函数 -------------------
def get_client():
    """从 session 获取 MEFrpClient"""
    token = session.get('token', None)
    if not token:
        return None
    # 使用合适的 User-Agent 避免被拦截
    client = MEFrpClient(token=token, user_agent='WebUI/1.0.0')
    return client

def safe_api_call(func, *args, **kwargs):
    """统一异常处理包装器"""
    try:
        result = func(*args, **kwargs)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

def get_tunnels_direct():
    """直接通过 API 获取隧道列表，绕过 MEFrpLib 的对象转换问题"""
    token = session.get('token')
    if not token:
        return None, '未登录'
    
    try:
        url = "https://api.mefrp.com/api/user/proxies"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "WebUI/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        print(f"直接 API 调用成功，共 {len(result.get('proxies', []))} 个隧道")
        return result, None
    except Exception as e:
        print(f"直接 API 调用失败: {str(e)}")
        return None, str(e)

# ------------------- API 接口 -------------------
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    pwd = data.get('password')
    email_code = data.get('email_code', 'test')
    captcha_token = data.get('captcha_token', 'test')
    if not username or not email or not pwd:
        return jsonify({'error': '用户名、邮箱和密码不能为空'}), 400
    client = MEFrpClient(user_agent='WebUI/1.0.0')
    return safe_api_call(client.register, username, email, email_code, pwd)

@app.route('/api/send_register_email', methods=['POST'])
def api_send_register_email():
    data = request.json
    email = data.get('email')
    captcha_token = data.get('captcha_token', 'test')
    if not email:
        return jsonify({'error': '邮箱不能为空'}), 400
    client = MEFrpClient(user_agent='WebUI/1.0.0')
    return safe_api_call(client.get_register_email_code, email, captcha_token)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('email') or data.get('username')
    pwd = data.get('password')
    captcha_token = data.get('captcha_token')
    if not username or not pwd:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    try:
        client = MEFrpClient(user_agent='WebUI/1.0.0')
        res = client.login(username, pwd, captcha_token)
        if res and "token" in res:
            session['token'] = res["token"]
        return jsonify(res)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/token_login', methods=['POST'])
def api_token_login():
    """使用 Token 登录 - 直接使用 requests 确保请求头正确传递"""
    data = request.json
    token = data.get('token')
    if not token:
        return jsonify({'error': 'Token 不能为空'}), 400
    
    try:
        # 直接使用 requests 发送请求，确保 Token 在请求头中正确传递
        url = "https://api.mefrp.com/api/auth/user/info"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "WebUI/1.0.0",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("code") == 200:
            # Token 有效，保存到 session
            session['token'] = token
            return jsonify({
                'message': 'Token 登录成功',
                'data': result.get('data')
            })
        else:
            return jsonify({'error': f'Token 无效: {result.get("message", "Unknown error")}'}), 401
            
    except requests.exceptions.RequestException as e:
        traceback.print_exc()
        return jsonify({'error': f'网络请求失败: {str(e)}'}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Token 无效: {str(e)}'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """清除 session 中的 token"""
    session.pop('token', None)
    return jsonify({'message': '已退出登录'})

@app.route('/api/user_info', methods=['GET'])
def api_user_info():
    client = get_client()
    if not client:
        return jsonify({'error': '未登录，请先登录'}), 401
    try:
        user_info = client.get_user_info()
        # 转换 UserInfo 对象为字典，并确保字段名称正确
        return jsonify({
            'userId': user_info.userId,
            'username': user_info.username,
            'email': user_info.email,
            'userGroup': user_info.friendlyGroup,  # 使用 friendlyGroup 作为用户组
            'traffic': user_info.traffic,  # 流量单位为 MB
            'tunnelCount': user_info.usedProxies,
            'maxTunnels': user_info.maxProxies,
            'signedToday': user_info.todaySigned,
            'isRealname': user_info.isRealname,
            'group': user_info.group,
            'inBound': user_info.inBound,
            'outBound': user_info.outBound
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh_token', methods=['POST'])
def api_refresh_token():
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    try:
        client.reset_token('test')
        return jsonify({'message': 'Token refreshed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset_password', methods=['POST'])
def api_reset_password():
    client = get_client()
    data = request.json
    old_pwd = data.get('old_password')
    new_pwd = data.get('new_password')
    if not client or not old_pwd or not new_pwd:
        return jsonify({'error': '缺少必要参数或未登录'}), 400
    return safe_api_call(client.reset_password, old_pwd, new_pwd)

@app.route('/api/forgot_password', methods=['POST'])
def api_forgot_password():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    if not username or not email:
        return jsonify({'error': '用户名和邮箱不能为空'}), 400
    client = MEFrpClient()
    return safe_api_call(client.forgot_password, username, email)

@app.route('/api/sign', methods=['POST'])
def api_sign():
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    data = request.json
    captcha_token = data.get('captcha_token', '')
    
    # 尝试签到，如果需要验证码会返回相应错误
    try:
        result = client.sign(captcha_token)
        return jsonify(result)
    except Exception as e:
        error_msg = str(e)
        # 检查是否是验证码相关错误
        if '验证码' in error_msg or 'captcha' in error_msg.lower() or '验证' in error_msg:
            # 返回友好提示
            return jsonify({
                'error': '签到需要验证码',
                'message': '请先获取验证码，填写后再签到',
                'need_captcha': True
            }), 400
        else:
            return jsonify({'error': error_msg}), 500

@app.route('/api/tunnels', methods=['GET'])
def api_tunnels():
    client = get_client()
    if not client:
        return jsonify({'error': '未登录，请先登录'}), 401
    try:
        print("正在获取隧道列表...")
        
        # 首先尝试使用直接 API 调用获取原始数据（绕过 MEFrpLib 对象转换）
        result, error = get_tunnels_direct()
        if result and 'proxies' in result:
            print(f"获取成功（直接API），共 {len(result.get('proxies', []))} 个隧道")
            return jsonify(result)
        
        # 如果直接调用失败，记录错误并尝试使用 MEFrpLib
        if error:
            print(f"直接 API 调用失败: {error}，尝试使用 MEFrpLib...")
        
        proxies_data = client.get_proxy_list()
        
        # 如果返回的是 Response 对象（requests.Response），直接返回其 JSON
        if hasattr(proxies_data, 'json'):
            result = proxies_data.json()
            print(f"获取成功（MEFrpLib Response），共 {len(result.get('proxies', []))} 个隧道")
            return jsonify(result)
        
        # 如果返回的是自定义对象，尝试转换为字典
        if hasattr(proxies_data, 'proxies'):
            proxies_list = []
            for p in proxies_data.proxies:
                if hasattr(p, '__dict__'):
                    proxies_list.append(p.__dict__)
                else:
                    proxies_list.append(p)
            
            nodes_list = []
            if hasattr(proxies_data, 'nodes'):
                for n in proxies_data.nodes:
                    if hasattr(n, '__dict__'):
                        nodes_list.append(n.__dict__)
                    else:
                        nodes_list.append(n)
            
            print(f"获取成功（MEFrpLib 对象），共 {len(proxies_list)} 个隧道")
            return jsonify({
                'proxies': proxies_list,
                'nodes': nodes_list
            })
        
        # 如果是字典或其他格式，直接返回
        return jsonify(proxies_data)
        
    except Exception as e:
        print(f"获取隧道列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/create_tunnel', methods=['POST'])
def api_create_tunnel():
    client = get_client()
    data = request.json
    required = ['node_id', 'name', 'local_ip', 'local_port']
    if not client or any(k not in data for k in required):
        return jsonify({'error': '缺少必要参数或未登录'}), 400
    
    print(f"创建隧道请求数据: {data}")
    
    # 构建创建隧道请求数据 - 使用 MEFrpLib 期望的格式（驼峰命名）
    req_data = {
        'nodeId': int(data['node_id']),
        'proxyName': data['name'],
        'localIp': data['local_ip'],
        'localPort': int(data['local_port']),
        'proxyType': data.get('proxy_type', 'tcp').upper(),
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
    
    print(f"处理后的请求数据: {req_data}")
    
    try:
        # 创建隧道 - 注意：create_proxy 接收一个字典参数，不是关键字参数
        result = client.create_proxy(req_data)
        print(f"创建隧道结果: {result}")
        
        # 如果创建成功，尝试启用隧道
        if result and (result.get('code') == 200 or result.get('success')):
            # 获取新创建的隧道 ID
            proxy_id = None
            if 'data' in result:
                if isinstance(result['data'], dict):
                    proxy_id = result['data'].get('proxyId')
                elif hasattr(result['data'], 'proxyId'):
                    proxy_id = result['data'].proxyId
            elif isinstance(result, dict) and 'proxyId' in result:
                proxy_id = result.get('proxyId')
            
            # 如果找到了隧道 ID，尝试启用它
            if proxy_id:
                print(f"正在启用新创建的隧道 ID: {proxy_id}")
                try:
                    # 使用 toggle_proxy 方法启用隧道
                    enable_result = client.toggle_proxy(proxy_id)
                    print(f"启用隧道结果: {enable_result}")
                    
                    # 检查启用结果
                    if enable_result and (enable_result.get('code') == 200 or enable_result.get('success')):
                        result['enabled'] = True
                        result['enable_result'] = enable_result
                    else:
                        result['enabled'] = False
                        result['enable_result'] = enable_result
                except Exception as enable_err:
                    print(f"启用隧道失败（不影响创建）: {enable_err}")
                    result['enabled'] = False
                    result['enable_error'] = str(enable_err)
            else:
                print("未找到新创建的隧道 ID，无法自动启用")
            
            return jsonify(result)
        else:
            return jsonify(result)
    except Exception as e:
        print(f"创建隧道失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'details': traceback.format_exc()}), 500

@app.route('/api/delete_tunnel', methods=['POST'])
def api_delete_tunnel():
    client = get_client()
    data = request.json
    proxy_id = data.get('id')
    if not client or not proxy_id:
        return jsonify({'error': '缺少隧道ID或未登录'}), 400
    return safe_api_call(client.delete_proxy, proxy_id)

@app.route('/api/close_tunnel', methods=['POST'])
def api_close_tunnel():
    client = get_client()
    data = request.json
    proxy_id = data.get('id')
    if not client or not proxy_id:
        return jsonify({'error': '缺少隧道ID或未登录'}), 400
    return safe_api_call(client.toggle_proxy, proxy_id)

@app.route('/api/tunnel_info', methods=['GET'])
def api_tunnel_info():
    client = get_client()
    proxy_id = request.args.get('id')
    if not client or not proxy_id:
        return jsonify({'error': '缺少隧道ID或未登录'}), 400
    return safe_api_call(client.get_proxy_config, proxy_id)

@app.route('/api/nodes', methods=['GET'])
def api_nodes():
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    try:
        nodes = client.get_node_list()
        return jsonify({'nodes': [n.__dict__ if hasattr(n, '__dict__') else n for n in nodes]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/free_port', methods=['GET'])
def api_free_port():
    client = get_client()
    node_id = request.args.get('node')
    protocol = request.args.get('protocol', 'tcp')
    if not client or not node_id:
        return jsonify({'error': '缺少节点参数或未登录'}), 400
    return safe_api_call(client.get_free_port, node_id, protocol)

@app.route('/api/create_proxy_data', methods=['GET'])
def api_create_proxy_data():
    """获取创建隧道所需的所有数据（节点列表和用户组信息）"""
    client = get_client()
    if not client:
        return jsonify({'error': '未登录'}), 401
    try:
        data = client.get_create_proxy_data()
        return jsonify({
            'nodes': [n.__dict__ if hasattr(n, '__dict__') else n for n in data.nodes],
            'groups': [g.__dict__ if hasattr(g, '__dict__') else g for g in data.groups],
            'currentGroup': data.currentGroup
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def api_statistics():
    try:
        client = MEFrpClient()
        stats = client.get_statistics()
        return jsonify(stats.__dict__ if hasattr(stats, '__dict__') else stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
def api_delete_tunnel_by_id(proxy_id):
    """删除隧道（通过 URL 参数）"""
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

# ------------------- 启动服务 -------------------
if __name__ == '__main__':
    print("=" * 50)
    print("  ME Frp WebUI Service")
    print("=" * 50)
    print(f"访问地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except OSError as e:
        if "10013" in str(e) or "Address already in use" in str(e):
            print("\nError: Port 5000 is already in use!")
            print("Please close the program using port 5000, or modify the port in app.py")
        else:
            print(f"\nError starting: {e}")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"\nUnknown error: {e}")
        traceback.print_exc()
        input("Press Enter to exit...")