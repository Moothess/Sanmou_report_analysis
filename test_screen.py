import win32gui
import mss
from utils.image import save_image
import numpy as np

process_name = "三国：谋定天下"

hwnd = win32gui.FindWindow(None, process_name)
_, _, w, h = win32gui.GetClientRect(hwnd)
#print(client_rect)
left, top = win32gui.ClientToScreen(hwnd, (0, 0))
right, bottom = win32gui.ClientToScreen(hwnd, (w, h))
width = right - left
height = bottom - top

print(f"截图全局游戏界面0: left={left}, top={top}, width={width}, height={height}")
with mss.mss() as sct:
    screenshot = np.array(sct.grab({'left': left, 'top': top, 'width': width, 'height': height}))
    save_image(screenshot, "temp/global000.png")
