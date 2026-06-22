# -*- coding: utf-8 -*-
"""
MeFrp-GR-Client 原生桌面控制台（PySide6 / Qt WebEngine）
=======================================================
- 原生 Qt 窗口（无浏览器边框/地址栏），内容是 WebUI 的 1:1 复刻
- 通过 QWebEngineView 加载本地 Flask 后端（http://127.0.0.1:5001）
- 自动复用 WebUI 的全部样式、图标、登录方式、启动方式、统计
- 用户体验和 WebUI 完全一致，但启动方式是"双击 .exe"
- 额外原生能力：系统托盘、原生菜单栏、键盘快捷键、自定义标题
"""

import os
import sys
import webbrowser

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QSystemTrayIcon, QMenu, QMessageBox,
    QStatusBar, QLabel, QFileDialog, QStyle,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEngineSettings, QWebEnginePage, QWebEngineProfile,
)

APP_TITLE = "MeFrp-GR-Client v1.0.0"
DEFAULT_API = "http://127.0.0.1:5001"


# ---------------------------------------------------------------------------
# 自定义状态栏
# ---------------------------------------------------------------------------
class _StatusBar(QStatusBar):
    def __init__(self):
        super().__init__()
        self._label = QLabel("● 就绪")
        self.addWidget(self._label)

    def set_text(self, text: str, timeout: int = 5000):
        self._label.setText(f"● {text}")
        if timeout > 0:
            QTimer.singleShot(timeout, lambda: self._label.setText("● 就绪"))


# ---------------------------------------------------------------------------
# 主窗口
# ---------------------------------------------------------------------------
class MeFrpDesktopApp(QMainWindow):
    """把 WebUI 嵌进原生 Qt 窗口"""

    def __init__(self, api_base: str = DEFAULT_API):
        super().__init__()
        self.api_base = api_base.rstrip('/')
        self.tray = None

        self.setWindowTitle(APP_TITLE)
        self.resize(1280, 820)
        self.setMinimumSize(1100, 700)

        # 状态栏
        self._statusbar = _StatusBar()
        self.setStatusBar(self._statusbar)

        # WebEngine 视图（先建好，菜单才能引用）
        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)

        # 菜单栏
        self._build_menu_bar()

        # WebEngine 设置
        settings = self.view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.DnsPrefetchEnabled, True)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
        settings.setAttribute(QWebEngineSettings.FocusOnNavigationEnabled, True)

        # 持久化缓存 / Cookie
        profile = self.view.page().profile()
        profile.setHttpCacheType(QWebEngineProfile.DiskHttpCache)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        try:
            cache_dir = os.path.join(os.path.expanduser('~'), '.me_frp_client', 'webengine_cache')
            os.makedirs(cache_dir, exist_ok=True)
            profile.setCachePath(cache_dir)
            profile.setPersistentStoragePath(cache_dir)
        except Exception:
            pass

        # 信号
        self.view.urlChanged.connect(self._on_url_changed)
        self.view.loadStarted.connect(lambda: self._statusbar.set_text("正在加载..."))
        self.view.loadFinished.connect(self._on_load_finished)
        self.view.titleChanged.connect(self._on_title_changed)
        self.view.page().windowCloseRequested.connect(lambda: self.close())

        # 下载请求
        try:
            profile.downloadRequested.connect(self._on_download)
        except Exception:
            pass

        # 外部链接拦截
        try:
            self.view.page().setLinkDelegationPolicy(QWebEnginePage.DelegateAllLinks)
            self.view.page().linkClicked.connect(self._on_link_clicked)
        except Exception:
            pass

        # 系统托盘
        self._build_tray_icon()

        # 延迟加载（等窗口显示完）
        QTimer.singleShot(150, self._load_app)

    # ===========================================================
    # 菜单栏
    # ===========================================================
    def _build_menu_bar(self):
        mb = self.menuBar()

        m_home = mb.addMenu("主页(&H)")

        act_refresh = QAction("🔄 刷新(&R)", self)
        act_refresh.setShortcut(QKeySequence.Refresh)
        act_refresh.triggered.connect(self.view.reload)
        m_home.addAction(act_refresh)

        act_open_browser = QAction("🌐 在浏览器中打开(&O)", self)
        act_open_browser.setShortcut("Ctrl+Shift+O")
        act_open_browser.triggered.connect(lambda: webbrowser.open(self.api_base + '/'))
        m_home.addAction(act_open_browser)

        m_home.addSeparator()

        act_back = QAction("← 后退", self)
        act_back.setShortcut(QKeySequence.Back)
        act_back.triggered.connect(self.view.back)
        m_home.addAction(act_back)

        act_fwd = QAction("→ 前进", self)
        act_fwd.setShortcut(QKeySequence.Forward)
        act_fwd.triggered.connect(self.view.forward)
        m_home.addAction(act_fwd)

        m_home.addSeparator()

        act_quit = QAction("退出(&Q)", self)
        act_quit.setShortcut(QKeySequence.Quit)
        act_quit.triggered.connect(self._quit_app)
        m_home.addAction(act_quit)

        m_tool = mb.addMenu("工具(&T)")

        act_clear_cache = QAction("🧹 清理缓存", self)
        act_clear_cache.triggered.connect(self._clear_cache)
        m_tool.addAction(act_clear_cache)

        act_clear_cookies = QAction("🍪 清理 Cookie", self)
        act_clear_cookies.triggered.connect(self._clear_cookies)
        m_tool.addAction(act_clear_cookies)

        m_help = mb.addMenu("帮助(&A)")

        act_about = QAction(f"ℹ 关于 {APP_TITLE}", self)
        act_about.triggered.connect(self._show_about)
        m_help.addAction(act_about)

    # ===========================================================
    # 系统托盘
    # ===========================================================
    def _build_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip(APP_TITLE)
        self.tray.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        menu = QMenu()
        a_show = QAction("显示主窗口", self)
        a_show.triggered.connect(self._show_and_raise)
        menu.addAction(a_show)
        a_refresh = QAction("刷新", self)
        a_refresh.triggered.connect(self.view.reload)
        menu.addAction(a_refresh)
        menu.addSeparator()
        a_quit = QAction("退出", self)
        a_quit.triggered.connect(self._quit_app)
        menu.addAction(a_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self._show_and_raise()

    def _show_and_raise(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit_app(self):
        QApplication.instance().quit()

    # ===========================================================
    # 加载与状态
    # ===========================================================
    def _load_app(self):
        target = self.api_base + '/'
        self.view.load(QUrl(target))
        self._statusbar.set_text(f"已连接后端: {self.api_base}")

    def _on_load_finished(self, ok: bool):
        if ok:
            self._statusbar.set_text(f"✅ 已加载 {self.view.url().toString()}")
        else:
            self._statusbar.set_text(
                f"❌ 加载失败，请确认后端 {self.api_base} 是否运行（HTTP 服务是否启动）",
                timeout=15000,
            )

    def _on_url_changed(self, url: QUrl):
        self._statusbar.set_text(f"→ {url.toString()}")

    def _on_title_changed(self, title: str):
        if title and title.strip():
            self.setWindowTitle(f"{title} — {APP_TITLE}")

    def _on_link_clicked(self, url: QUrl):
        url_str = url.toString()
        if url_str.startswith(self.api_base) or url_str.startswith('/') or url_str.startswith('#'):
            self.view.load(url)
            return
        webbrowser.open(url_str)

    def _on_download(self, download):
        path, _ = QFileDialog.getSaveFileName(self, "保存文件", download.suggestedFileName())
        if path:
            download.setPath(path)
            download.accept()
            self._statusbar.set_text(f"⬇ 下载中: {path}")

    def _clear_cache(self):
        try:
            self.view.page().profile().clearHttpCache()
            QMessageBox.information(self, "完成", "WebEngine 缓存已清理。")
        except Exception as e:
            QMessageBox.warning(self, "失败", f"清理失败: {e}")

    def _clear_cookies(self):
        try:
            self.view.page().profile().cookieStore().deleteAllCookies()
            QMessageBox.information(self, "完成", "Cookie 已清理。")
        except Exception as e:
            QMessageBox.warning(self, "失败", f"清理失败: {e}")

    def _show_about(self):
        QMessageBox.about(
            self,
            f"关于 {APP_TITLE}",
            f"<h3>{APP_TITLE}</h3>"
            f"<p>MeFrp 内网穿透的原生桌面客户端</p>"
            f"<p>本窗口嵌入了 WebUI 完整功能：</p>"
            f"<ul>"
            f"<li>📊 控制面板（用户信息 / 流量 / 签到）</li>"
            f"<li>📡 隧道管理（创建 / 启动 / 停止 / 删除）</li>"
            f"<li>🖥 节点监控</li>"
            f"<li>🎁 权益抽奖（单抽 / 十连）</li>"
            f"<li>👤 用户中心</li>"
            f"<li>ℹ 关于面板</li>"
            f"</ul>"
            f"<p style='color:#94a3b8; font-size:9pt;'>样式 / 图标 / 登录方式 / 启动方式 / 统计 与 WebUI 完全一致</p>"
            f"<hr><p style='color:#94a3b8; font-size:9pt;'>后端: {self.api_base}</p>"
        )

    # ===========================================================
    # 关闭行为：最小化到托盘
    # ===========================================================
    def closeEvent(self, event):
        if self.tray and self.tray.isVisible():
            event.ignore()
            self.hide()
            self.tray.showMessage(
                APP_TITLE,
                "已最小化到系统托盘，双击图标可恢复窗口",
                QSystemTrayIcon.Information,
                2000,
            )
        else:
            event.accept()


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def run_gui(api_base: str = DEFAULT_API):
    """启动桌面控制台（会阻塞直到窗口关闭）"""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setOrganizationName("MeFrp-GR-Client")
    app.setQuitOnLastWindowClosed(True)

    win = MeFrpDesktopApp(api_base=api_base)
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run_gui()
