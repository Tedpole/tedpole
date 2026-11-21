"""
Trae 每日签到脚本

签到流程：
  1) 激活 Trae 窗口（如果已启动）
  2) 点击左下角头像按钮 → 弹出菜单
  3) 点击菜单里的"签到"按钮
  4) 记录日志、截图

运行方式：
    python trae_checkin.py

依赖：
    pip install pyautogui pygetwindow

自动运行（Windows 任务计划程序，每天 09:00）：
    动作   : pythonw.exe  （或 python.exe）
    参数   : trae_checkin.py
    起始于 : C:\\path\\to\\this\\script\\dir

配置文件（由 calibrate.py 生成）：
    checkin_config.json —— 存放 avatar_button / checkin_button 的坐标
"""

import json
import logging
import os
import sys
import time
from datetime import datetime


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "checkin_config.json")
LOG_PATH = os.path.join(SCRIPT_DIR, "checkin.log")
SCREENSHOT_DIR = os.path.join(SCRIPT_DIR, "screenshots")


# ============================================================
# CONFIG：若 checkin_config.json 存在则自动加载，否则为 None
# ============================================================
CONFIG = {
    "avatar_button": None,    # {"x": int, "y": int}  左下角头像按钮
    "checkin_button": None,   # {"x": int, "y": int}  弹出菜单里的签到按钮
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        logging.warning("未找到 checkin_config.json，CONFIG 保持为 None。请先运行 calibrate.py。")
        return
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data.get("avatar_button"), dict):
            CONFIG["avatar_button"] = data["avatar_button"]
        if isinstance(data.get("checkin_button"), dict):
            CONFIG["checkin_button"] = data["checkin_button"]
        logging.info("已加载配置: avatar_button=%s  checkin_button=%s",
                     CONFIG["avatar_button"], CONFIG["checkin_button"])
    except Exception as e:
        logging.error("读取配置失败: %s", e)


def setup_logging():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format=fmt,
        encoding="utf-8",
    )
    # 同时把日志打到控制台，方便手动运行观察
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(fmt))
    logging.getLogger().addHandler(console)


def activate_trae_window():
    """尝试把 Trae 窗口激活到前台。找不到也不报错，继续执行。"""
    try:
        import pygetwindow as gw
        # Trae 窗口标题通常包含 "Trae"
        wins = [w for w in gw.getAllWindows() if w.title and "Trae" in w.title]
        if not wins:
            logging.warning("未找到标题含 'Trae' 的窗口，跳过窗口激活步骤")
            return
        win = wins[0]
        try:
            win.activate()
        except Exception:
            pass
        # 有些情况下用 moveTo + resize 强制把窗口拉到可见
        if win.isMinimized:
            win.restore()
        time.sleep(1.0)
        logging.info("已激活 Trae 窗口: %s", win.title)
    except ImportError:
        logging.warning("未安装 pygetwindow，跳过窗口激活（pip install pygetwindow）")
    except Exception as e:
        logging.warning("窗口激活异常（可忽略）: %s", e)


def click(btn: dict, label: str):
    """点击一个按钮（带坐标合法性校验）。"""
    if not btn or "x" not in btn or "y" not in btn:
        raise ValueError(f"{label} 坐标未配置")
    import pyautogui
    pyautogui.FAILSAFE = True
    x, y = int(btn["x"]), int(btn["y"])
    logging.info("点击 [%s] → (%d, %d)", label, x, y)
    pyautogui.click(x, y)


def take_screenshot(tag: str):
    try:
        import pyautogui
        fname = f"{datetime.now():%Y%m%d_%H%M%S}_{tag}.png"
        path = os.path.join(SCREENSHOT_DIR, fname)
        pyautogui.screenshot(path)
        logging.info("截图已保存: %s", path)
    except Exception as e:
        logging.warning("截图失败: %s", e)


def do_checkin() -> bool:
    """执行签到主流程。返回 True 表示整体成功。"""
    if CONFIG["avatar_button"] is None or CONFIG["checkin_button"] is None:
        logging.error(
            "CONFIG 未配置完整（avatar_button=%s, checkin_button=%s），"
            "请先在 Windows 上运行 calibrate.py 进行坐标校准。",
            CONFIG["avatar_button"], CONFIG["checkin_button"],
        )
        return False

    try:
        import pyautogui  # noqa: F401  (确保可用)
    except ImportError:
        logging.error("未安装 pyautogui，请先: pip install pyautogui pygetwindow")
        return False

    # 1. 激活 Trae 窗口
    activate_trae_window()
    time.sleep(0.8)

    # 2. 点击头像 → 弹出菜单
    try:
        click(CONFIG["avatar_button"], "头像按钮")
    except Exception as e:
        logging.error("点击头像按钮失败: %s", e)
        take_screenshot("avatar_fail")
        return False
    time.sleep(1.0)
    take_screenshot("after_avatar")

    # 3. 点击签到按钮
    try:
        click(CONFIG["checkin_button"], "签到按钮")
    except Exception as e:
        logging.error("点击签到按钮失败: %s", e)
        take_screenshot("checkin_fail")
        return False
    time.sleep(1.5)
    take_screenshot("after_checkin")

    logging.info("✅ 签到动作已执行完毕")
    return True


def main():
    setup_logging()
    logging.info("=" * 50)
    logging.info("Trae 签到任务启动 @ %s", datetime.now())

    load_config()

    ok = do_checkin()
    if ok:
        logging.info("🟢 本次签到流程正常结束")
    else:
        logging.error("🔴 签到流程遇到问题，请检查上方日志")

    logging.info("=" * 50)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
