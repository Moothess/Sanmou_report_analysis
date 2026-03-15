import win32gui
import win32con
import mss

process_name = "三国：谋定天下"
    
def get_resolution():
    hwnd = win32gui.FindWindow(None, process_name)
        
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    
    _, _, client_width, client_height = win32gui.GetClientRect(hwnd)
    client_left_top = win32gui.ClientToScreen(hwnd, (0, 0))
    client_right_bottom = win32gui.ClientToScreen(hwnd, (client_width, client_height))

    window_center_x = (client_left_top[0] + client_right_bottom[0]) // 2
    window_center_y = (client_left_top[1] + client_right_bottom[1]) // 2

    with mss.mss() as sct:
        monitor = sct.monitors[1]
    
    relative_x = client_left_top[0] - monitor['left']
    relative_y = client_left_top[1] - monitor['top']

    windows_info = {
        'title': process_name,
        'width': client_width,
        'height': client_height,
        'absolute_x': client_left_top[0],
        'absolute_y': client_left_top[1],
        'monitor_width': monitor['width'],
        'monitor_height': monitor['height'],
        'relative_x': relative_x,
        'relative_y': relative_y,
    }

    width = windows_info['width']
    height = windows_info['height']

    wh_ratio = width / height if height != 0 else 0
    windows_info['wh_ratio'] = wh_ratio
    windows_info['primary_axis'] = 'height'

    #position_info = info  # 赋值给全局变量
    print(windows_info)
    return windows_info