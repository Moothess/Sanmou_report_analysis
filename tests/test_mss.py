from pathlib import Path
import sys

import mss
import numpy as np
import pytest

if sys.platform != "win32":
    pytest.skip("Windows-only test", allow_module_level=True)

import win32gui

from sanmou_report_analysis.utils.image import save_image
from sanmou_report_analysis.utils.process_info import get_resolution


def get_global_game(save_dir, process_info):
    hwnd = process_info["hwnd"]
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top

    with mss.mss() as sct:
        screenshot = np.array(
            sct.grab({"left": left, "top": top, "width": width, "height": height})
        )
        save_image(screenshot, save_dir / "global000.png")
    return screenshot


target_process = "三国：谋定天下"

position_info = get_resolution(target_process)
get_global_game(Path("./temp"), position_info)
