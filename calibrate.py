# -*- coding: utf-8 -*-
"""
Trae 签到坐标校准工具 (Windows)
================================

运行: python calibrate.py

使用说明:
  1. 打开 Trae 桌面端，让它显示在屏幕前方
  2. 运行本脚本
  3. 把鼠标移到「左下角头像按钮」上，按 F1 记录
  4. 点击头像弹出菜单，把鼠标移到「签到按钮」上，按 F2 记录
  5. 如果签到后有弹窗，把鼠标移到关闭按钮上，按 F3 记录（可选）
  6. 按 ESC 退出
  7. 脚本会输出完整的 CONFIG 配置，复制到 trae_checkin.py 中即可
"""

import sys
import time
import threading

try:
    import pyautogui
except ImportError:
    print("[错误] 缺少 pyautogui，请先运行: pip install pyautogui pillow")
    sys.exit(1)

try:
    import keyboard
except ImportError:
    print("[错误] 缺少 keyboard，请先运行: pip install keyboard")
    sys.exit(1)


# 存储坐标
recorded = {
    "avatar_button": None,
    "checkin_button": None,
    "confirm_close_button": None,
}


def record_point(key, name):
    """记录当前鼠标位置"""
    x, y = pyautogui.position()
    recorded[key] = (x, y)
    print(f"  ✅ {name}: ({x}, {y})")


def listener():
    """键盘监听器"""
    print("\n请按以下快捷键记录坐标:")
    print("  F1 - 左下角头像按钮")
    print("  F2 - 菜单中的签到按钮")
    print("  F3 - 签到后弹窗关闭按钮 (可选)")
    print("  ESC - 完成，退出")
    print("-" * 40)

    keyboard.add_hotkey("f1", lambda: record_point("avatar_button", "头像按钮"))
    keyboard.add_hotkey("f2", lambda: record_point("checkin_button", "签到按钮"))
    keyboard.add_hotkey("f3", lambda: record_point("confirm_close_button", "关闭按钮"))

    # 实时显示坐标
    try:
        while True:
            x, y = pyautogui.position()
            status = []
            for k, v in recorded.items():
                if v:
                    status.append(f"{k}=({v[0]},{v[1]})")
            status_str = " | ".join(status) if status else "未记录"
            print(f"\r当前鼠标: ({x}, {y})  [{status_str}]", end="", flush=True)
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass


def main():
    print("=" * 50)
    print("  Trae 签到坐标校准工具")
    print("=" * 50)
    print()
    print("⚠️  注意：请在运行本脚本前，先打开 Trae 桌面端")
    print()
    print("即将开始监听... 请切换到 Trae 窗口准备好")
    time.sleep(2)

    # 启动监听
    listener()


if __name__ == "__main__":
    main()
