import os
import sys
import base64
import subprocess
import traceback
import threading
import webbrowser
import requests
from flask import Flask, render_template, request, jsonify, session, make_response

# 尝试导入 MEFrpLib，如果失败则给出明确提示
try:
    from MEFrpLib import MEFrpClient
except ImportError as e:
    print(f"Error importing MEFrpLib: {e}")
    print("Please install: pip install MEFrpLib")
    sys.exit(1)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 禁用模板缓存和静态文件缓存，确保修改立即生效
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['JSON_AS_ASCII'] = False

# ------------------- 页面路由 -------------------
@app.route('/')
def index():
    """返回 Web UI 页面"""
    try:
        response = render_template('index.html')
        resp = make_response(response)
        # 禁用缓存，确保每次都加载最新版本
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp
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
    """从 session 获取 MEFrpClient，若没有 token 但有凭据则自动重新登录"""
    token = session.get('token', None)
    if not token:
        # 尝试用保存的凭据自动重新登录
        username = session.get('_login_username')
        password = session.get('_login_password')
        if username and password:
            try:
                url = "https://api.mefrp.com/api/public/login"
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "MeFrp-GR-Client/1.0.0"
                }
                body = {"username": username, "password": password, "captchaToken": ""}
                resp = requests.post(url, headers=headers, json=body, timeout=15)
                result = resp.json()
                if result.get('code') == 200:
                    data_field = result.get('data')
                    new_token = None
                    if isinstance(data_field, dict):
                        new_token = data_field.get('token') or data_field.get('accessToken')
                    if not new_token:
                        cookies = resp.cookies.get_dict()
                        for name in ('token', 'session', 'auth', 'accessToken'):
                            if name in cookies and cookies[name]:
                                new_token = cookies[name]
                                break
                    if new_token:
                        session['token'] = new_token
                        token = new_token
                        print(f"[自动登录] 已为 {username} 重新获取 token")
            except Exception as e:
                print(f"[自动登录] 失败: {e}")
        if not token:
            return None
    return MEFrpClient(token=token, user_agent='MeFrp-GR-Client/1.0.0')

def safe_api_call(func, *args, **kwargs):
    """统一异常处理包装器"""
    try:
        result = func(*args, **kwargs)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

def decode_captcha(raw_captcha):
    if not raw_captcha:
        return raw_captcha
    try:
        decoded = base64.b64decode(raw_captcha).decode('utf-8')
        if '||' in decoded:
            token = decoded.split('||')[0]
            print(f"[Captcha] Base64 解码成功, 提取 token 前20字符: {token[:20]}...")
            return token
        print(f"[Captcha] Base64 解码后无 || 分隔符，返回原始输入")
        return raw_captcha
    except Exception:
        print(f"[Captcha] 非 Base64 格式，直接使用原始输入")
        return raw_captcha

def get_tunnels_direct():
    """直接通过 API 获取隧道列表，绕过 MEFrpLib 的对象转换问题"""
    token = session.get('token')
    if not token:
        return None, '未登录'
    
    try:
        url = "https://api.mefrp.com/api/auth/proxy/list"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 200 and 'data' in result:
            data = result['data']
            print(f"直接 API 调用成功，共 {len(data.get('proxies', []))} 个隧道")
            return data, None
        
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
    client = MEFrpClient(user_agent='MeFrp-GR-Client/1.0.0')
    return safe_api_call(client.register, username, email, email_code, pwd)

@app.route('/api/send_register_email', methods=['POST'])
def api_send_register_email():
    data = request.json
    email = data.get('email')
    captcha_token = data.get('captcha_token', 'test')
    if not email:
        return jsonify({'error': '邮箱不能为空'}), 400
    client = MEFrpClient(user_agent='MeFrp-GR-Client/1.0.0')
    return safe_api_call(client.get_register_email_code, email, captcha_token)

@app.route('/api/login', methods=['POST'])
def api_login():
    """密码登录 - 直接调用官方 API /api/public/login"""
    data = request.json
    username = data.get('email') or data.get('username')
    pwd = data.get('password')
    captcha_token = data.get('captcha') or data.get('captcha_token') or data.get('captchaToken')

    if not username or not pwd:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    try:
        # 按照官方文档调用 POST /api/public/login
        url = "https://api.mefrp.com/api/public/login"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        body = {
            "username": username,
            "password": pwd,
            "captchaToken": captcha_token or ""
        }

        print(f"[登录] 尝试登录用户: {username}")
        response = requests.post(url, headers=headers, json=body, timeout=15)
        result = response.json()
        print(f"[登录] 响应: code={result.get('code')}, msg={result.get('message')}")

        if result.get('code') == 200:
            token = None

            # 方式1：从响应 body 的 data 字段获取 token（API 返回格式）
            data_field = result.get('data')
            if isinstance(data_field, dict):
                if data_field.get('token'):
                    token = data_field['token']
                elif data_field.get('accessToken'):
                    token = data_field['accessToken']
            elif isinstance(data_field, str) and data_field:
                # 某些情况下 data 直接就是 token 字符串
                token = data_field

            # 方式2：从响应的 Set-Cookie 获取 token
            if not token:
                cookies = response.cookies.get_dict()
                print(f"[登录] 响应 cookies: {list(cookies.keys())}")
                # 尝试常见 token cookie 名称
                for name in ('token', 'session', 'sessionid', 'sessionId', 'auth', 'authToken', 'accessToken', 'satoken'):
                    if name in cookies and cookies[name]:
                        token = cookies[name]
                        print(f"[登录] 从 cookie '{name}' 获取到 token")
                        break

            # 方式3：备用 - 使用 MEFrpClient 登录获取内部 token
            if not token:
                try:
                    client = MEFrpClient(user_agent='MeFrp-GR-Client/1.0.0')
                    res = client.login(username, pwd, captcha_token)
                    if res:
                        if isinstance(res, dict) and res.get('token'):
                            token = res['token']
                        elif hasattr(client, 'token') and client.token:
                            token = client.token
                except Exception as inner_err:
                    print(f"[登录] MEFrpClient 备用登录失败: {inner_err}")

            if token:
                session['token'] = token
                print(f"[登录] 用户 {username} 登录成功，token 已保存 (长度: {len(token)})")
                return jsonify({
                    'code': 200,
                    'message': '登录成功',
                    'token': token,
                    'data': result.get('data')
                })
            else:
                # 登录成功但未获取到 token：保存凭据以备后用，并主动用 user_info 验证
                session['_login_username'] = username
                session['_login_password'] = pwd
                print(f"[登录] 用户 {username} 登录成功但未获取到 token，将尝试后续自动重新登录")
                return jsonify({
                    'code': 200,
                    'message': result.get('message', '登录成功'),
                    'data': result.get('data'),
                    'warning': '已登录但未获取到访问令牌，部分功能可能受限'
                })
        else:
            err_msg = result.get('message', '登录失败')
            print(f"[登录] 失败: {err_msg}")
            return jsonify({
                'error': err_msg,
                'code': result.get('code')
            }), (401 if result.get('code') == 403 else 400)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'登录请求失败: {str(e)}'}), 500

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
            "User-Agent": "MeFrp-GR-Client/1.0.0",
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

@app.route('/api/magic_link/send', methods=['POST'])
def api_magic_link_send():
    """发送 Magic Link 登录链接到邮箱"""
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({'error': '邮箱不能为空'}), 400
    try:
        url = "https://api.mefrp.com/api/auth/magic-link/send"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.post(url, headers=headers, json={"email": email}, timeout=15)
        result = response.json()
        print(f"[MagicLink] 发送结果: {result}")
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """清除 session 中的 token"""
    session.pop('token', None)
    session.pop('_login_username', None)
    session.pop('_login_password', None)
    return jsonify({'message': '已退出登录'})

@app.route('/api/user_info', methods=['GET'])
def api_user_info():
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录，请先登录'}), 401
    try:
        url = "https://api.mefrp.com/api/auth/user/info"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') != 200:
            return jsonify({'error': result.get('message', '获取用户信息失败')}), 400
        
        data = result.get('data', {})
        return jsonify({
            'userId': data.get('userId'),
            'username': data.get('username'),
            'email': data.get('email'),
            'userGroup': data.get('friendlyGroup'),
            'traffic': data.get('traffic'),
            'tunnelCount': data.get('usedProxies'),
            'maxTunnels': data.get('maxProxies'),
            'signedToday': data.get('todaySigned'),
            'isRealname': data.get('isRealname'),
            'group': data.get('group'),
            'inBound': data.get('inBound'),
            'outBound': data.get('outBound'),
            'regTime': data.get('regTime'),
            'status': data.get('status')
        })
    except requests.exceptions.RequestException as e:
        traceback.print_exc()
        return jsonify({'error': f'网络请求失败: {str(e)}'}), 500


@app.route('/api/user/frpToken', methods=['GET'])
def api_user_frp_token_uc():
    """获取用户 frpToken（启动令牌）"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录，请先登录'}), 401
    try:
        url = "https://api.mefrp.com/api/auth/user/frpToken"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get('code') != 200:
            return jsonify({'error': result.get('message', '获取 frpToken 失败')}), 400
        return jsonify(result.get('data', {}))
    except requests.exceptions.RequestException as e:
        traceback.print_exc()
        return jsonify({'error': f'网络请求失败: {str(e)}'}), 500


@app.route('/api/user/uc/groups', methods=['GET'])
def api_user_groups_uc():
    """获取用户组信息（用户中心版）"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录，请先登录'}), 401
    try:
        url = "https://api.mefrp.com/api/auth/user/groups"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get('code') != 200:
            return jsonify({'error': result.get('message', '获取用户组信息失败')}), 400
        return jsonify(result.get('data', {}))
    except requests.exceptions.RequestException as e:
        traceback.print_exc()
        return jsonify({'error': f'网络请求失败: {str(e)}'}), 500


@app.route('/api/user/tokenReset', methods=['POST'])
def api_user_token_reset():
    """重置访问密钥（需要 captchaToken）"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录，请先登录'}), 401
    try:
        data = request.json or {}
        captcha_token = data.get('captchaToken', '')
        url = "https://api.mefrp.com/api/auth/user/tokenReset"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MeFrp-GR-Client/1.0.0",
            "Content-Type": "application/json"
        }
        body = {"captchaToken": captcha_token}
        response = requests.post(url, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get('code') != 200:
            return jsonify({'error': result.get('message', '重置访问密钥失败')}), 400
        return jsonify(result.get('data', {}))
    except requests.exceptions.RequestException as e:
        traceback.print_exc()
        return jsonify({'error': f'网络请求失败: {str(e)}'}), 500


@app.route('/api/user/operationLog/stats', methods=['GET'])
def api_user_operation_log_stats():
    """获取用户操作日志统计（今日/本周/本月/总）"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录，请先登录'}), 401
    try:
        url = "https://api.mefrp.com/api/auth/operationLog/stats"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get('code') != 200:
            return jsonify({'error': result.get('message', '获取日志统计失败')}), 400
        return jsonify(result.get('data', {}))
    except requests.exceptions.RequestException as e:
        traceback.print_exc()
        return jsonify({'error': f'网络请求失败: {str(e)}'}), 500


@app.route('/api/user/operationLog/list', methods=['GET'])
def api_user_operation_log_list():
    """获取用户操作日志列表（分页）"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录，请先登录'}), 401
    try:
        page = request.args.get('page', '1')
        page_size = request.args.get('pageSize', '20')
        start_time = request.args.get('startTime', '')
        end_time = request.args.get('endTime', '')

        params = {'page': page, 'pageSize': page_size}
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time

        url = "https://api.mefrp.com/api/auth/operationLog/list"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get('code') != 200:
            return jsonify({'error': result.get('message', '获取操作日志失败')}), 400
        return jsonify(result.get('data', {}))
    except requests.exceptions.RequestException as e:
        traceback.print_exc()
        return jsonify({'error': f'网络请求失败: {str(e)}'}), 500

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
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    data = request.json
    captcha_token = data.get('captcha_token', '')
    
    print(f"[签到] 收到签到请求, 原始 captcha_token 长度: {len(captcha_token)}, 前20字符: {captcha_token[:20] if captcha_token else '(空)'}")
    
    if not captcha_token:
        return jsonify({
            'error': '请先获取验证码',
            'message': '点击"打开验证码"按钮完成人机验证，然后将验证码粘贴到输入框',
            'need_captcha': True
        }), 400
    
    captcha_token = decode_captcha(captcha_token)
    print(f"[签到] 解码后 captcha_token 长度: {len(captcha_token)}, 前20字符: {captcha_token[:20]}")
    
    try:
        url = "https://api.mefrp.com/api/auth/user/sign"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        payload = {"captchaToken": captcha_token}
        
        print(f"[签到] 请求 URL: {url}")
        print(f"[签到] Token: {token[:15] if token else '(空)'}...")
        
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        result = response.json()
        
        print(f"[签到] 响应状态码: {response.status_code}")
        print(f"[签到] 完整响应: {result}")
        
        if result.get('code') == 200:
            print(f"[签到] 签到成功!")
            return jsonify(result.get('data', result))
        else:
            error_msg = result.get('message', '未知错误')
            error_code = result.get('code', -1)
            print(f"[签到] API返回错误, code={error_code}, message={error_msg}")
            
            if '验证码' in error_msg or 'captcha' in error_msg.lower() or '验证' in error_msg:
                return jsonify({
                    'error': '人机验证失败: ' + error_msg,
                    'message': '验证码无效或已过期，请重新获取验证码',
                    'need_captcha': True,
                    'api_message': error_msg,
                    'api_code': error_code
                }), 400
            elif '已签到' in error_msg or 'already' in error_msg.lower() or 'repeat' in error_msg.lower():
                return jsonify({
                    'error': '今日已签到',
                    'message': '您今天已经签到过了，明天再来吧',
                    'already_signed': True,
                    'api_message': error_msg,
                    'api_code': error_code
                }), 400
            elif 'Token' in error_msg or 'token' in error_msg.lower() or '401' in str(error_code):
                return jsonify({
                    'error': '登录已过期: ' + error_msg,
                    'api_message': error_msg,
                    'api_code': error_code
                }), 401
            else:
                return jsonify({
                    'error': error_msg,
                    'message': '请稍后重试或联系管理员',
                    'api_message': error_msg,
                    'api_code': error_code
                }), 400
    except Exception as e:
        error_msg = str(e)
        print(f"[签到] 异常: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'签到失败: {error_msg}',
            'message': '请稍后重试或联系管理员'
        }), 500

# ------------------- 抽奖相关 API -------------------
@app.route('/api/lottery/remaining', methods=['GET'])
def api_lottery_remaining():
    """获取剩余抽奖次数"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    try:
        url = "https://api.mefrp.com/api/auth/user/luckydraw"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        print(f"[抽奖] 查询剩余次数响应: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"[抽奖] 查询异常: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/lottery/draw', methods=['POST'])
def api_lottery_draw():
    """执行单次抽奖"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    try:
        url = "https://api.mefrp.com/api/auth/user/luckydraw"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.post(url, headers=headers, json={}, timeout=15)
        result = response.json()
        print(f"[抽奖] 执行抽奖响应: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"[抽奖] 异常: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/store/products', methods=['GET'])
def api_store_products():
    """获取奖品池信息（抽奖池配置）"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录，请先登录'}), 401
    try:
        # 调用官方 API /api/auth/user/luckydraw/pool
        url = "https://api.mefrp.com/api/auth/user/luckydraw/pool"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        print(f"[奖品池] API响应: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"[奖品池] 获取异常: {e}")
        return jsonify({'error': str(e), 'data': []}), 200

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
        print(f"[隧道] 正在创建隧道: {req_data}")
        result = client.create_proxy(req_data)
        print(f"[隧道] 创建结果: {result}")

        # 检查创建是否成功（兼容多种返回格式）
        create_ok = False
        if result:
            if isinstance(result, dict):
                # MEFrpLib 返回格式: {code: 200, data: {...}} 或 {success: True, ...}
                create_ok = (result.get('code') == 200 or result.get('success') is True or
                           result.get('status') == 'ok' or 'proxyId' in result or 'data' in result)
            elif hasattr(result, 'code'):
                create_ok = result.code == 200

        if not create_ok:
            err_msg = '未知错误'
            if isinstance(result, dict):
                err_msg = result.get('message') or result.get('error') or result.get('msg') or str(result)
            return jsonify({'error': f'创建隧道失败: {err_msg}', 'raw': result}), 400
        
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

@app.route('/api/toggle_tunnel', methods=['POST'])
def api_toggle_tunnel():
    """启用/禁用隧道 - 直接调用官方 API /api/auth/proxy/toggle"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录，请先登录'}), 401

    data = request.json
    proxy_id = data.get('proxyId') or data.get('id')
    is_disabled = data.get('isDisabled', False)

    if not proxy_id:
        return jsonify({'error': '缺少隧道ID'}), 400

    try:
        # 按照官方文档: POST /api/auth/proxy/toggle
        url = "https://api.mefrp.com/api/auth/proxy/toggle"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MeFrp-GR-Client/1.0.0",
            "Authorization": f"Bearer {token}"
        }
        body = {
            "proxyId": int(proxy_id),
            "isDisabled": bool(is_disabled)
        }

        action = "禁用" if is_disabled else "启用"
        print(f"[隧道] {action}隧道 proxyId={proxy_id}, isDisabled={is_disabled}")

        response = requests.post(url, headers=headers, json=body, timeout=15)
        result = response.json()
        print(f"[隧道] {action}结果: code={result.get('code')}, msg={result.get('message')}")

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        # 备用：使用 MEFrpClient 的 toggle_proxy 方法（仅传 proxyId）
        try:
            client = get_client()
            if client:
                print(f"[隧道] 使用备用方案 MEFrpClient.toggle_proxy")
                result = client.toggle_proxy(int(proxy_id))
                return jsonify(result)
            return jsonify({'error': str(e)}), 500
        except Exception as e2:
            traceback.print_exc()
            return jsonify({'error': f'操作失败: {str(e2)}'}), 500

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
            "User-Agent": "MeFrp-GR-Client/1.0.0"
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
            "User-Agent": "MeFrp-GR-Client/1.0.0"
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
        client = MEFrpClient(user_agent='MeFrp-GR-Client/1.0.0')
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
        client = MEFrpClient(user_agent='MeFrp-GR-Client/1.0.0')
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
        client = MEFrpClient(user_agent='MeFrp-GR-Client/1.0.0')
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
        client = MEFrpClient(user_agent='MeFrp-GR-Client/1.0.0')
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
            "User-Agent": "MeFrp-GR-Client/1.0.0"
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
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        return jsonify(result)
    except requests.exceptions.RequestException as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== 完整 API 功能 ====================

@app.route('/api/user/groups', methods=['GET'])
def api_user_groups():
    """获取用户组信息"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    try:
        url = "https://api.mefrp.com/api/auth/user/groups"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/operation_logs', methods=['GET'])
def api_user_operation_logs():
    """获取用户操作日志"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 20, type=int)
        start_time = request.args.get('startTime', '')
        end_time = request.args.get('endTime', '')
        
        url = f"https://api.mefrp.com/api/auth/operationLog/list?page={page}&pageSize={page_size}"
        if start_time:
            url += f"&startTime={start_time}"
        if end_time:
            url += f"&endTime={end_time}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/operation_logs/stats', methods=['GET'])
def api_user_operation_logs_stats():
    """获取用户日志统计"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    try:
        url = "https://api.mefrp.com/api/auth/operationLog/stats"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy/list', methods=['GET'])
def api_proxy_list():
    """获取隧道列表（官方API）"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    try:
        url = "https://api.mefrp.com/api/auth/proxy/list"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy/create_data', methods=['GET'])
def api_proxy_create_data():
    """获取创建隧道所需的所有数据"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    try:
        url = "https://api.mefrp.com/api/auth/createProxyData"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy/create', methods=['POST'])
def api_proxy_create():
    """创建隧道（新版本）"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    data = request.json
    if not data.get('nodeId') or not data.get('proxyName'):
        return jsonify({'error': '节点ID和隧道名称不能为空'}), 400
    try:
        url = "https://api.mefrp.com/api/auth/proxy/create"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        payload = {
            "nodeId": data.get('nodeId'),
            "proxyName": data.get('proxyName'),
            "localIp": data.get('localIp', '127.0.0.1'),
            "localPort": data.get('localPort', 80),
            "remotePort": data.get('remotePort', 0),
            "domain": data.get('domain', ''),
            "proxyType": data.get('proxyType', 'tcp'),
            "accessKey": data.get('accessKey', ''),
            "hostHeaderRewrite": data.get('hostHeaderRewrite', ''),
            "httpPlugin": data.get('httpPlugin', ''),
            "requestHeaders": data.get('requestHeaders', {}),
            "httpUser": data.get('httpUser', ''),
            "httpPassword": data.get('httpPassword', ''),
            "crtPath": data.get('crtPath', ''),
            "keyPath": data.get('keyPath', ''),
            "proxyProtocolVersion": data.get('proxyProtocolVersion', ''),
            "useEncryption": data.get('useEncryption', False),
            "useCompression": data.get('useCompression', False)
        }
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        result = response.json()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy/delete', methods=['POST'])
def api_proxy_delete():
    """删除隧道"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    data = request.json
    if not data.get('proxyId'):
        return jsonify({'error': '隧道ID不能为空'}), 400
    try:
        url = "https://api.mefrp.com/api/auth/proxy/delete"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        payload = {"proxyId": data.get('proxyId')}
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy/kick', methods=['POST'])
def api_proxy_kick():
    """强制下线隧道"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    data = request.json
    if not data.get('proxyId'):
        return jsonify({'error': '隧道ID不能为空'}), 400
    try:
        url = "https://api.mefrp.com/api/auth/proxy/kick"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        payload = {"proxyId": data.get('proxyId')}
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy/toggle', methods=['POST'])
def api_proxy_toggle():
    """启用/禁用隧道"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    data = request.json
    if not data.get('proxyId'):
        return jsonify({'error': '隧道ID不能为空'}), 400
    try:
        url = "https://api.mefrp.com/api/auth/proxy/toggle"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        payload = {
            "proxyId": data.get('proxyId'),
            "isDisabled": data.get('isDisabled', True)
        }
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy/config/single', methods=['POST'])
def api_proxy_config_single():
    """获取单一隧道配置"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    data = request.json
    if not data.get('proxyId'):
        return jsonify({'error': '隧道ID不能为空'}), 400
    try:
        url = "https://api.mefrp.com/api/auth/proxy/config/single"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        payload = {
            "proxyId": data.get('proxyId'),
            "format": data.get('format', 'ini')
        }
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy/update', methods=['POST'])
def api_proxy_update():
    """更新隧道"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    data = request.json
    if not data.get('proxyId'):
        return jsonify({'error': '隧道ID不能为空'}), 400
    try:
        url = "https://api.mefrp.com/api/auth/proxy/update"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        payload = {
            "proxyId": data.get('proxyId'),
            "proxyName": data.get('proxyName'),
            "localIp": data.get('localIp'),
            "localPort": data.get('localPort'),
            "remotePort": data.get('remotePort'),
            "domain": data.get('domain'),
            "proxyType": data.get('proxyType'),
            "accessKey": data.get('accessKey'),
            "hostHeaderRewrite": data.get('hostHeaderRewrite'),
            "httpPlugin": data.get('httpPlugin'),
            "requestHeaders": data.get('requestHeaders', {}),
            "httpUser": data.get('httpUser'),
            "httpPassword": data.get('httpPassword'),
            "crtPath": data.get('crtPath'),
            "keyPath": data.get('keyPath'),
            "proxyProtocolVersion": data.get('proxyProtocolVersion'),
            "useEncryption": data.get('useEncryption', False),
            "useCompression": data.get('useCompression', False)
        }
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        result = response.json()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== FRPC 隧道启动管理 ====================

frpc_process = None
frpc_logs = []

def get_mefrpc_base_dir():
    """获取 mefrp 目录路径"""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), 'mefrp')
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mefrp')

def get_mefrpc_path():
    """获取 mefrpc.exe 路径"""
    mefrpc_path = os.path.join(get_mefrpc_base_dir(), 'mefrpc.exe')
    if not os.path.exists(mefrpc_path):
        raise FileNotFoundError(f"未找到 mefrpc.exe: {mefrpc_path}")
    return mefrpc_path

def get_frpc_config_path():
    """获取 FRPC 配置文件路径"""
    return os.path.join(get_mefrpc_base_dir(), 'frpc.toml')

def _read_frpc_output(pipe, prefix):
    """读取子进程输出到日志列表"""
    global frpc_logs
    try:
        for line in iter(pipe.readline, ''):
            if line:
                # 处理可能的 \r 回车符
                clean = line.replace('\r', '').rstrip()
                if clean:
                    frpc_logs.append(f"[{prefix}] {clean}")
                    if len(frpc_logs) > 500:
                        frpc_logs = frpc_logs[-500:]
    except Exception as e:
        frpc_logs.append(f'[{prefix}] 读取输出异常: {e}')
    finally:
        try:
            pipe.close()
        except Exception:
            pass

@app.route('/api/frpc/start', methods=['POST'])
def api_frpc_start():
    """启动 FRPC 隧道"""
    global frpc_process, frpc_logs

    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录，请先登录'}), 401

    data = request.json
    proxy_ids = data.get('proxyIds', [])

    if not proxy_ids:
        return jsonify({'error': '请先在隧道列表中勾选要启动的隧道'}), 400

    try:
        mefrpc_path = get_mefrpc_path()
        config_path = get_frpc_config_path()

        print(f"[FRPC] 使用路径: {mefrpc_path}")
        print(f"[FRPC] 配置文件: {config_path}")

        # 检查配置文件是否存在且非空
        if not os.path.exists(config_path):
            return jsonify({'error': f'配置文件不存在: {config_path}\n请先生成配置（勾选隧道后点击"启动隧道"按钮会自动生成）'}), 400

        file_size = os.path.getsize(config_path)
        if file_size == 0:
            return jsonify({'error': '配置文件为空！请检查隧道是否已正确创建和启用'}), 400

        # 如果已有进程在运行，先停止
        if frpc_process and frpc_process.poll() is None:
            print(f"[FRPC] 检测到旧进程 PID={frpc_process.pid}，正在停止...")
            try:
                frpc_process.terminate()
                frpc_process.wait(timeout=5)
            except:
                try:
                    frpc_process.kill()
                    frpc_process.wait(timeout=3)
                except:
                    pass
            frpc_logs.append('[系统] 已停止旧的 FRPC 进程')

        frpc_logs = [f"[系统] 启动 mefrpc.exe -c {config_path} ({len(proxy_ids)} 个隧道)"]
        print(f"[FRPC] 工作目录: {os.path.dirname(mefrpc_path)}")

        # 使用列表形式传参，避免 shell 转义和中文路径问题
        creation_flags = 0
        if os.name == 'nt':
            # Windows 下隐藏控制台窗口闪烁
            creation_flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)

        try:
            frpc_process = subprocess.Popen(
                [mefrpc_path, '-c', config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=os.path.dirname(mefrpc_path),
                creationflags=creation_flags
            )
        except Exception as popen_err:
            # 备用方案：通过 cmd shell 启动
            print(f"[FRPC] 直接启动失败，回退到 cmd 启动: {popen_err}")
            frpc_logs.append(f'[系统] 直接启动失败: {popen_err}，尝试通过 cmd 启动')
            cmd = f'cd /d "{os.path.dirname(mefrpc_path)}" && "{mefrpc_path}" -c "{config_path}"'
            frpc_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                shell=True,
                cwd=os.path.dirname(mefrpc_path),
                creationflags=creation_flags
            )

        threading.Thread(target=_read_frpc_output, args=(frpc_process.stdout, '输出'), daemon=True).start()
        threading.Thread(target=_read_frpc_output, args=(frpc_process.stderr, '错误'), daemon=True).start()

        print(f"[FRPC] 启动成功, PID: {frpc_process.pid}")

        # 启动监控线程：3秒后检查进程是否还存活
        def _monitor_startup():
            import time
            time.sleep(3)
            if frpc_process and frpc_process.poll() is not None:
                exit_code = frpc_process.poll()
                err_detail = '\n'.join([l for l in frpc_logs[-20:] if '错误' in l or 'error' in l.lower() or 'fail' in l.lower()])
                frpc_logs.append(f'[系统] ⚠️ mefrpc.exe 已退出 (exit code={exit_code})')
                if err_detail:
                    frpc_logs.append(f'[系统] 错误详情: {err_detail[:200]}')
                frpc_logs.append('[系统] 请查看上方错误日志了解原因，或尝试重新生成配置')
                print(f"[FRPC] 进程已退出, exit code={exit_code}")

        threading.Thread(target=_monitor_startup, daemon=True).start()

        return jsonify({
            'message': 'FRPC 启动成功',
            'pid': frpc_process.pid,
            'tunnel_count': len(proxy_ids)
        })

    except FileNotFoundError as e:
        return jsonify({'error': f'找不到客户端程序: {str(e)}\n请先下载 mefrpc.exe（客户端控制面板 -> 下载客户端）'}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'启动失败: {str(e)}'}), 500

@app.route('/api/frpc/stop', methods=['POST'])
def api_frpc_stop():
    """停止 FRPC 隧道"""
    global frpc_process, frpc_logs
    
    if not frpc_process or frpc_process.poll() is not None:
        frpc_logs.append('[系统] FRPC 未在运行')
        return jsonify({'message': 'FRPC 未在运行', 'running': False})
    
    try:
        frpc_logs.append('[系统] 正在停止 FRPC...')
        frpc_process.terminate()
        frpc_process.wait(timeout=5)
        frpc_logs.append('[系统] FRPC 已停止')
        print(f"[FRPC] 进程已停止")
        return jsonify({'message': 'FRPC 已停止', 'running': False})
    except Exception as e:
        try:
            frpc_process.kill()
            frpc_logs.append('[系统] FRPC 已强制停止')
        except:
            pass
        return jsonify({'message': 'FRPC 已强制停止', 'running': False})


@app.route('/api/frpc/offlineAll', methods=['POST'])
def api_frpc_offline_all():
    """下线所有隧道（停止本地 frpc 进程）"""
    global frpc_process, frpc_logs
    if not frpc_process or frpc_process.poll() is not None:
        return jsonify({'message': '本地没有运行中的 FRPC 进程', 'running': False})
    try:
        frpc_logs.append('[系统] 正在下线所有隧道...')
        frpc_process.terminate()
        frpc_process.wait(timeout=5)
        frpc_logs.append('[系统] 所有隧道已下线')
        return jsonify({'message': '所有隧道已下线', 'running': False})
    except Exception:
        try:
            frpc_process.kill()
            frpc_logs.append('[系统] FRPC 已强制停止（所有隧道下线）')
        except Exception:
            pass
        return jsonify({'message': '所有隧道已强制下线', 'running': False})


@app.route('/api/frpc/status', methods=['GET'])
def api_frpc_status():
    """获取 FRPC 状态"""
    global frpc_process
    
    if frpc_process:
        if frpc_process.poll() is None:
            return jsonify({'running': True, 'pid': frpc_process.pid, 'exit_code': None})
        else:
            return jsonify({'running': False, 'pid': None, 'exit_code': frpc_process.poll()})
    return jsonify({'running': False, 'pid': None, 'exit_code': None})

@app.route('/api/frpc/logs', methods=['GET'])
def api_frpc_logs():
    """获取 FRPC 运行日志"""
    global frpc_logs
    return jsonify({'logs': frpc_logs[-200:]})

def _clean_toml_config(toml_content):
    """清理 TOML 配置，移除可能会导致 mefrpc 崩溃的 plugin 段（仅移除 plugin 字段和 plugin section，保留其他以 plugin 开头的字段）"""
    if not toml_content:
        return toml_content
    lines = toml_content.split('\n')
    result = []
    in_plugin_section = False
    for line in lines:
        stripped = line.strip()
        # 检查是否进入 [proxies.plugin] 或 [proxies.transport.plugin] 段
        if stripped.startswith('[proxies.plugin]') or stripped.startswith('[proxies.transport.plugin]'):
            in_plugin_section = True
            continue
        # 如果在 plugin 段内，遇到新的 section 则退出
        if in_plugin_section:
            if stripped.startswith('['):
                in_plugin_section = False
                result.append(line)
            continue
        # 仅当是 "plugin = ..." 形式（紧跟空格或等号）才移除，避免误删 pluginLocalPath 等字段
        if (stripped == 'plugin' or stripped.startswith('plugin ') or stripped.startswith('plugin=')) and '=' in stripped:
            continue
        result.append(line)
    return '\n'.join(result)

def _merge_toml_configs(configs):
    """合并多个 TOML 配置（提取头部 + 所有 [[proxies]] 段）"""
    if not configs:
        return ''
    if len(configs) == 1:
        return configs[0]
    
    # 提取第一个配置的头部（proxies之前的部分）
    first = configs[0]
    header_lines = []
    proxies_sections = []
    in_proxies = False
    current_proxy = []
    
    for line in first.split('\n'):
        if line.strip().startswith('[[proxies]]'):
            if current_proxy:
                proxies_sections.append('\n'.join(current_proxy))
            current_proxy = [line]
            in_proxies = True
        elif in_proxies:
            if line.strip().startswith('[[') or line.strip().startswith('['):
                if current_proxy:
                    proxies_sections.append('\n'.join(current_proxy))
                current_proxy = [line]
            else:
                current_proxy.append(line)
        else:
            header_lines.append(line)
    
    if current_proxy:
        proxies_sections.append('\n'.join(current_proxy))
    
    # 提取其余配置的 [[proxies]] 段
    for cfg in configs[1:]:
        current_proxy = []
        for line in cfg.split('\n'):
            if line.strip().startswith('[[proxies]]'):
                if current_proxy:
                    proxies_sections.append('\n'.join(current_proxy))
                current_proxy = [line]
            elif current_proxy:
                current_proxy.append(line)
        if current_proxy:
            proxies_sections.append('\n'.join(current_proxy))
    
    # 合并
    result = '\n'.join(header_lines).rstrip() + '\n\n'
    result += '\n\n'.join(proxies_sections)
    return result

@app.route('/api/frpc/generate_config', methods=['POST'])
def api_frpc_generate_config():
    """生成 FRPC TOML 配置文件"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录，请先登录'}), 401
    
    data = request.json
    proxy_ids = data.get('proxyIds', [])
    
    if not proxy_ids:
        return jsonify({'error': '请选择要启动的隧道'}), 400
    
    try:
        mefrp_dir = get_mefrpc_base_dir()
        if not os.path.exists(mefrp_dir):
            os.makedirs(mefrp_dir)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "MeFrp-GR-Client/1.0.0"
        }
        
        configs = []
        errors = []
        
        for pid in proxy_ids:
            pid_int = int(pid)
            print(f"[FRPC]  处理隧道 {pid_int}")
            
            # 启用隧道
            try:
                print(f"[FRPC]  启用隧道 {pid_int} (isDisabled=false)")
                toggle_resp = requests.post(
                    "https://api.mefrp.com/api/auth/proxy/toggle",
                    headers=headers,
                    json={"proxyId": pid_int, "isDisabled": False},
                    timeout=10
                )
                toggle_data = toggle_resp.json()
                print(f"[FRPC]  启用结果: code={toggle_data.get('code')}, msg={toggle_data.get('message')}")
            except Exception as te:
                print(f"[FRPC]  启用隧道 {pid_int} 失败(可忽略): {te}")
            
            # 获取TOML格式配置
            try:
                print(f"[FRPC]  获取隧道 {pid_int} 配置 (格式: TOML)")
                config_resp = requests.post(
                    "https://api.mefrp.com/api/auth/proxy/config",
                    headers=headers,
                    json={"proxyId": pid_int, "format": "toml"},
                    timeout=30
                )
                config_data = config_resp.json()
                print(f"[FRPC]  配置响应: code={config_data.get('code')}")
                
                if config_data.get('code') != 200:
                    err_msg = config_data.get('message', '未知错误')
                    print(f"[FRPC]  隧道 {pid_int} 配置失败: {err_msg}")
                    errors.append(f"隧道 {pid_int}: {err_msg}")
                    continue
                
                cfg = config_data.get('data', {})
                config_content = cfg.get('config', '')
                
                if not config_content:
                    errors.append(f"隧道 {pid_int}: 返回的配置内容为空")
                    continue
                
                # 清理plugin段，防止mefrpc崩溃
                cleaned_content = _clean_toml_config(config_content)
                if not cleaned_content.strip():
                    errors.append(f"隧道 {pid_int}: 清理后配置为空")
                    continue
                configs.append(cleaned_content)
                print(f"[FRPC]  隧道 {pid_int} 配置获取成功 (TOML)")
                
            except Exception as ce:
                err_msg = str(ce)
                print(f"[FRPC]  隧道 {pid_int} 配置获取异常: {err_msg}")
                errors.append(f"隧道 {pid_int}: {err_msg}")
        
        if not configs:
            return jsonify({'error': '所有隧道配置获取失败: ' + '; '.join(errors)}), 400
        
        # 合并多个TOML配置：提取 [[proxies]] 段合并到同一个文件
        if len(configs) == 1:
            config_content = configs[0]
        else:
            # 提取每个配置的 [[proxies]] 段合并
            merged = _merge_toml_configs(configs)
            config_content = merged
        
        config_path = os.path.join(mefrp_dir, 'frpc.toml')

        # 移除可能存在的 BOM，然后统一用 utf-8 写入（不写 BOM）
        if config_content.startswith('\ufeff'):
            config_content = config_content[1:]
        # 统一换行符为 LF
        config_content = config_content.replace('\r\n', '\n').replace('\r', '\n')

        with open(config_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(config_content)

        # 校验写回文件内容
        with open(config_path, 'r', encoding='utf-8') as f:
            written_content = f.read()
        if not written_content.strip():
            return jsonify({'error': '配置文件写入后为空'}), 500

        print(f"[FRPC] TOML配置文件已生成: {config_path}, 成功 {len(configs)}/{len(proxy_ids)} 个隧道")
        
        result = {
            'message': 'TOML配置文件已生成',
            'config_path': config_path,
            'tunnel_count': len(configs)
        }
        if errors:
            result['warning'] = '; '.join(errors)
        
        return jsonify(result)
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'生成配置失败: {str(e)}'}), 500

@app.route('/api/frpc/check_client', methods=['GET'])
def api_frpc_check_client():
    """检查 mefrpc.exe 是否存在"""
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        mefrpc_path = os.path.join(base_dir, 'mefrp', 'mefrpc.exe')
        exists = os.path.exists(mefrpc_path)
        return jsonify({'exists': exists, 'path': mefrpc_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/frpc/download', methods=['POST'])
def api_frpc_download():
    """自动下载 mefrpc.exe 客户端"""
    token = session.get('token')
    if not token:
        return jsonify({'error': '未登录'}), 401
    
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        mefrp_dir = os.path.join(base_dir, 'mefrp')
        os.makedirs(mefrp_dir, exist_ok=True)
        
        mefrpc_path = os.path.join(mefrp_dir, 'mefrpc.exe')
        if os.path.exists(mefrpc_path):
            return jsonify({'message': '客户端已存在', 'path': mefrpc_path})
        
        download_url = "https://dl.mefrp.com/mefrpc.exe"
        print(f"[下载] 开始下载: {download_url}")
        
        resp = requests.get(download_url, stream=True, timeout=120)
        resp.raise_for_status()
        
        total = int(resp.headers.get('content-length', 0))
        downloaded = 0
        
        with open(mefrpc_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
        
        if total > 0 and downloaded != total:
            os.remove(mefrpc_path)
            return jsonify({'error': f'下载不完整: {downloaded}/{total}'}), 500
        
        print(f"[下载] mefrpc.exe 完成: {downloaded} bytes")
        return jsonify({'message': '客户端下载成功', 'path': mefrpc_path, 'size': downloaded})
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'下载失败: {str(e)}'}), 500

# ------------------- 启动服务 -------------------
def _parse_args():
    """解析命令行参数。打包成 exe 后，PyInstaller 会把这些参数透传"""
    import argparse
    p = argparse.ArgumentParser(add_help=True, description='MeFrp-GR-Client 启动器')
    p.add_argument('--host', default='0.0.0.0', help='监听地址 (默认 0.0.0.0)')
    p.add_argument('--port', type=int, default=5001, help='监听端口 (默认 5001)')
    p.add_argument('--open-browser', dest='open_browser', action='store_true',
                   help='启动后自动打开浏览器（默认不打开）')
    p.add_argument('--no-browser', dest='open_browser', action='store_false',
                   help='不打开浏览器（默认行为）')
    p.set_defaults(open_browser=False)
    return p.parse_args()

if __name__ == '__main__':
    args = _parse_args()
    host = args.host
    port = args.port
    open_browser = args.open_browser

    local_url = f"http://127.0.0.1:{port}"
    print("=" * 56)
    print("  MeFrp-GR-Client v1.0.0  (打包运行模式)")
    print("=" * 56)
    print(f"  访问地址: {local_url}")
    print(f"  局域网地址: http://<本机IP>:{port}")
    if open_browser:
        print("  浏览器将自动打开")
    else:
        print("  浏览器不会自动打开，请手动访问上方地址")
    print("  按 Ctrl+C 停止服务")
    print("=" * 56)

    # 仅当显式指定 --open-browser 时才自动打开浏览器
    if open_browser:
        threading.Timer(1.5, lambda: webbrowser.open(local_url)).start()

    try:
        from waitress import serve
        print("[服务] 使用 waitress 生产模式启动")
        serve(app, host=host, port=port)
    except ImportError:
        print("[服务] waitress 不可用，使用 Flask 调试模式")
        app.run(debug=False, host=host, port=port)