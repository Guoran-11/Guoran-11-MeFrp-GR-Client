# -*- mode: python ; coding: utf-8 -*-
"""
MeFrp-GR-Client PyInstaller 打包配置

打包命令（在项目根目录执行）：
    pyinstaller build.spec --clean --noconfirm

打包产物：
    dist/MeFrp-GR-Client/MeFrp-GR-Client.exe
    dist/MeFrp-GR-Client/  (附带 templates / mefrp / _internal 等)

默认行为：双击 .exe 弹出**原生 tkinter 桌面控制台窗口**（不打开浏览器）。
如需纯 Web 后端模式：在命令行追加  --no-gui
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 项目根目录
PROJECT_ROOT = os.path.abspath(SPECPATH)

# 收集 templates 目录（Flask 模板）
datas = [
    (os.path.join(PROJECT_ROOT, 'templates'), 'templates'),
]

# 收集 mefrp 目录（FRPC 客户端与配置）
mefrp_dir = os.path.join(PROJECT_ROOT, 'mefrp')
if os.path.isdir(mefrp_dir):
    datas.append((mefrp_dir, 'mefrp'))

# 收集 docs 目录（宣传网站，可选）
docs_dir = os.path.join(PROJECT_ROOT, 'docs')
if os.path.isdir(docs_dir):
    datas.append((docs_dir, 'docs'))

# 收集 scripts 目录（部署脚本，可选）
scripts_dir = os.path.join(PROJECT_ROOT, 'scripts')
if os.path.isdir(scripts_dir):
    datas.append((scripts_dir, 'scripts'))

# 隐式导入的子模块
hiddenimports = []
hiddenimports += collect_submodules('flask')
hiddenimports += collect_submodules('werkzeug')
hiddenimports += collect_submodules('jinja2')
hiddenimports += collect_submodules('waitress')
hiddenimports += collect_submodules('requests')
# 桌面 GUI（PySide6 / Qt WebEngine）相关
hiddenimports += collect_submodules('PySide6')
hiddenimports += collect_submodules('PySide6.QtCore')
hiddenimports += collect_submodules('PySide6.QtGui')
hiddenimports += collect_submodules('PySide6.QtWidgets')
hiddenimports += collect_submodules('PySide6.QtNetwork')
hiddenimports += collect_submodules('PySide6.QtWebEngineWidgets')
hiddenimports += collect_submodules('PySide6.QtWebEngineCore')
hiddenimports += collect_submodules('shiboken6')
hiddenimports += [
    'desktop_gui',
    'urllib.request',
    'urllib.parse',
    'http.client',
]

# 不需要打包的常见大模块（保留 PySide6 必需）
excludes = [
    'unittest',
    'pydoc',
    'doctest',
    'matplotlib',
    'numpy',
    'pandas',
    'PyQt5',
    'PyQt6',
    'PySide2',
    'IPython',
    'notebook',
    'pytest',
    'sphinx',
]

a = Analysis(
    [os.path.join(PROJECT_ROOT, 'app.py')],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,   # 配合 COLLECT 实现 onedir
    name='MeFrp-GR-Client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # 窗口模式：不弹黑色控制台，直接显示 Qt WebEngine 桌面控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,               # 如有 .ico 图标可填入路径
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MeFrp-GR-Client',
)
