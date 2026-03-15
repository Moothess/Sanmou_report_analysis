import sys

import mss
import numpy as np
import pytest

if sys.platform != "win32":
    pytest.skip("Windows-only test", allow_module_level=True)

import win32gui

from sanmou_report_analysis.utils.image import save_image

process_name = "三国：谋定天下"

hwnd = win32gui.FindWindow(None, process_name)
_, _, w, h = win32gui.GetClientRect(hwnd)
# print(client_rect)
left, top = win32gui.ClientToScreen(hwnd, (0, 0))
right, bottom = win32gui.ClientToScreen(hwnd, (w, h))
width = right - left
height = bottom - top

print(f"截图全局游戏界面0: left={left}, top={top}, width={width}, height={height}")
with mss.mss() as sct:
    screenshot = np.array(sct.grab({"left": left, "top": top, "width": width, "height": height}))
    save_image(screenshot, "temp/global000.png")
