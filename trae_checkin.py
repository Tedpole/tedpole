# -*- coding: utf-8 -*-
"""
Trae 桌面端每日签到自动化脚本 (Windows)
====================================

使用方法：
  1. 安装依赖: pip install pyautogui pillow pywin32
  2. 运行一次校准脚本获取坐标（推荐）
  3. 配置下方 CONFIG 区域的坐标
  4. 双击运行本脚本，或通过 Windows 任务计划程序每天 7:00 自动运行

作者：AI Assistant
"""

import time
import sys
import os
import logging
from datetime import datetime

# ============ 依赖检查 ============
try:
    import pyautogui
except ImportError:
    print("[错误] 缺少 pyautogui，请先运行: pip install pyautogui pillow")
    sys.exit(1)

try:
    import win32gui
    import win32con
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

# ============ 日志配置 ============
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkin.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("trae_checkin")

# ============ 配置区 ============
# 请先运行 calibrate.py 获取正确的屏幕坐标
# 如果没有校准，请手动设置以下坐标（见文末说明）

CONFIG = {
    # Trae 桌面端可执行文件路径（如果脚本需帮你启动 Trae）
    # 常见路径:
    #   C:\\Users\\<你的用户名>\\AppData\\Local\\Programs\\Trae\\Trae.exe
    #   C:\\Program Files\\Trae\\Trae.exe
    "trae_exe_path": r"C:\Users\%USERNAME%\AppData\Local\Programs\Trae\Trae.exe",

    # 是否自动启动 Trae（如果 Trae 未运行）
    "auto_launch_trae": True,

    # Trae 窗口标题关键词（用于查找 Trae 窗口）
    "window_title_keywords": ["Trae", "TRAE"],

    # ========== 关键坐标 ==========
    # 运行 calibrate.py 获取这些坐标
    # 如果 Trae 窗口位置/大小变了，需要重新校准

    # 左下角头像按钮的屏幕坐标 (x, y)
    "avatar_button": None,  # 示例: (50, 880)

    # 弹出菜单中「签到」按钮的屏幕坐标 (x, y)
    "checkin_button": None,  # 示例: (100, 600)

    # 签到成功后可能出现的确认弹窗关闭按钮（可选）
    "confirm_close_button": None,

    # ========== 行为配置 ==========
    # 每步操作的等待时间（秒）
    "step_delay": 1.5,

    # 操作前延迟（让用户有时间切回 Trae）
    "pre_delay": 2.0,

    # 最大重试次数
    "max_retries": 3,
}

# ============ 工具函数 ============

def find_trae_window():
    """查找 Trae 窗口并返回句柄"""
    if not HAS_WIN32:
        log.warning("pywin32 未安装，跳过窗口查找")
        return None

    results = []

    def _enum_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                for kw in CONFIG["window_title_keywords"]:
                    if kw.lower() in title.lower():
                        results.append((hwnd, title))
                        break

    win32gui.EnumWindows(_enum_callback, None)

    if results:
        log.info(f"找到 Trae 窗口: {results[0][1]}")
        return results[0][0]
    return None


def bring_trae_to_front(hwnd):
    """将 Trae 窗口置于前台"""
    if not HAS_WIN32 or hwnd is None:
        return False

    try:
        # 如果窗口最小化则恢复
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.5)

        # 置于前台
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)

        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        log.info(f"Trae 窗口已激活: 位置=({left},{top}), 大小={width}x{height}")
        return True
    except Exception as e:
        log.error(f"激活窗口失败: {e}")
        return False


def launch_trae():
    """启动 Trae 桌面端"""
    import subprocess

    path = os.path.expandvars(CONFIG["trae_exe_path"])
    if not os.path.exists(path):
        log.warning(f"Trae 可执行文件不存在: {path}")
        log.info("请手动修改 CONFIG['trae_exe_path'] 为正确路径")
        return False

    log.info(f"正在启动 Trae: {path}")
    try:
        subprocess.Popen([path], shell=True)
        log.info("Trae 启动中，等待 15 秒...")
        time.sleep(15)
        return True
    except Exception as e:
        log.error(f"启动 Trae 失败: {e}")
        return False


def wait_for_trae():
    """等待 Trae 窗口出现"""
    for i in range(20):
        hwnd = find_trae_window()
        if hwnd:
            return hwnd
        time.sleep(2)
    return None


def click(x, y, description="", clicks=1):
    """点击指定坐标"""
    log.info(f"  点击 {description}: ({x}, {y})")
    pyautogui.click(x=x, y=y, clicks=clicks)
    time.sleep(CONFIG["step_delay"])


# ============ 签到主流程 ============

def do_checkin():
    """执行完整的签到流程"""
    log.info("=" * 50)
    log.info(f"开始 Trae 签到 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 50)

    # 步骤 1: 确保 Trae 窗口存在
    hwnd = find_trae_window()
    if hwnd is None:
        log.info("Trae 未运行")
        if CONFIG["auto_launch_trae"]:
            log.info("尝试启动 Trae...")
            launch_trae()
            hwnd = wait_for_trae()
            if hwnd is None:
                log.error("Trae 启动后仍未找到窗口，请手动启动 Trae 后再试")
                return False
        else:
            log.error("请先手动启动 Trae 桌面端")
            return False

    # 步骤 2: 激活 Trae 窗口
    log.info("激活 Trae 窗口...")
    bring_trae_to_front(hwnd)

    # 步骤 3: 预等待
    log.info(f"等待 {CONFIG['pre_delay']} 秒，确保窗口稳定...")
    time.sleep(CONFIG["pre_delay"])

    # 步骤 4: 点击头像
    avatar = CONFIG["avatar_button"]
    if avatar is None:
        log.error("未配置 avatar_button（头像坐标），请先运行 calibrate.py 获取坐标")
        return False

    click(avatar[0], avatar[1], "左下角头像按钮")

    # 步骤 5: 点击签到
    checkin = CONFIG["checkin_button"]
    if checkin is None:
        log.error("未配置 checkin_button（签到按钮坐标），请先运行 calibrate.py 获取坐标")
        return False

    click(checkin[0], checkin[1], "签到按钮")

    # 步骤 6: 处理可能的确认弹窗
    confirm = CONFIG.get("confirm_close_button")
    if confirm:
        time.sleep(1)
        click(confirm[0], confirm[1], "确认/关闭按钮")

    # 完成
    log.info("签到操作完成！")
    time.sleep(1)
    return True


# ============ 带重试的入口 ============

def main():
    success = False
    for attempt in range(1, CONFIG["max_retries"] + 1):
        log.info(f"--- 尝试 {attempt}/{CONFIG['max_retries']} ---")
        try:
            if do_checkin():
                log.info("✅ 签到成功！")
                success = True
                break
        except Exception as e:
            log.error(f"签到异常: {e}")

        if attempt < CONFIG["max_retries"]:
            log.info("3 秒后重试...")
            time.sleep(3)

    if not success:
        log.error("❌ 签到失败，请检查配置或手动签到")
        sys.exit(1)


if __name__ == "__main__":
    main()


# ============ 坐标获取说明 ============
"""
如何获取坐标：

方法 1 - 运行辅助脚本 calibrate.py（推荐）:
  python calibrate.py
  脚本会显示鼠标当前位置，移到头像上按 F1，移到签到按钮上按 F2。

方法 2 - 手动获取:
  1. 打开 Trae 桌面端
  2. 打开「画图」或任何可以显示鼠标坐标的工具
  3. 移动鼠标到左下角头像上，记录屏幕坐标
  4. 点击头像弹出菜单，移动到「签到」按钮上，记录坐标
  5. 把坐标填入上方 CONFIG 中

方法 3 - PowerShell 查看鼠标坐标:
  Add-Type -AssemblyName System.Windows.Forms;
  [System.Windows.Forms.Cursor]::Position
"""
