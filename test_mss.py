from pathlib import Path
from utils.process_info import get_resolution
import win32gui
import mss
import numpy as np

from utils.image import *



def get_global_game(save_dir, process_info):
    hwnd = process_info['hwnd']
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top

    with mss.mss() as sct:
        screenshot = np.array(sct.grab({'left': left, 'top': top, 'width': width, 'height': height}))
        save_image(screenshot, save_dir / "global000.png")
    return screenshot

target_process = "三国：谋定天下"

position_info = get_resolution(target_process)
get_global_game(Path("./temp"), position_info)