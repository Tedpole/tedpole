"""
坐标校准脚本 —— 在 Windows 上运行，用来采集 Trae 签到所需的两个坐标：
  1) 左下角头像按钮 avatar_button
  2) 弹出菜单里的签到按钮 checkin_button

运行方式：
    python calibrate.py

输出：
    把坐标写入同目录的 checkin_config.json，trae_checkin.py 会自动读取。
"""

import json
import os
import sys
import time

try:
    import pyautogui
except ImportError:
    print("[错误] 未安装 pyautogui，请先执行： pip install pyautogui")
    sys.exit(1)


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkin_config.json")


def wait_for_point(label: str, seconds: int = 8):
    """提示用户把鼠标移到目标位置，倒计时结束后读取当前坐标。"""
    print(f"\n>>> 请把鼠标移动到 [{label}] 上，倒计时 {seconds} 秒后自动记录...")
    for i in range(seconds, 0, -1):
        print(f"    {i}...", end="\r")
        time.sleep(1)
    x, y = pyautogui.position()
    print(f"    ✅ 已记录 ({x}, {y})")
    return {"x": x, "y": y}


def main():
    print("=" * 50)
    print("  Trae 签到坐标校准工具")
    print("=" * 50)
    print("\n准备好后按回车开始（Ctrl+C 可随时退出）...")
    input()

    avatar_button = wait_for_point("Trae 桌面端左下角 头像按钮")
    input("\n✅ 头像按钮已记录，准备好签到按钮后按回车...")
    print("   （先手动点击头像，让菜单弹出来）")
    input()
    checkin_button = wait_for_point("弹出菜单里的 签到按钮")

    config = {
        "avatar_button": avatar_button,
        "checkin_button": checkin_button,
    }

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print(f"  配置已写入 {CONFIG_PATH}")
    print(f"  avatar_button  = {avatar_button}")
    print(f"  checkin_button = {checkin_button}")
    print("  现在可以运行 trae_checkin.py 了 ✨")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已取消校准。")
