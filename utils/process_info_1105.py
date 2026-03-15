import functools
import winsound
import pygetwindow as gw
import psutil
import win32gui
import win32api
import win32con
import win32process
from screeninfo import get_monitors
import mss

def get_process_window_resolution(process_name_or_pid):
    windows_info = []
    
    try:
        # 获取所有窗口
        all_windows = gw.getWindowsWithTitle('')
        
        for window in all_windows:
            if not window.visible:
                continue  # 跳过不可见窗口
            if window.title == '':
                continue
                
            # 获取窗口句柄
            hwnd = window._hWnd
            
            # 获取窗口进程ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # 检查是否匹配目标进程
            match = False
            if isinstance(process_name_or_pid, int):
                match = (pid == process_name_or_pid)
            else:
                try:
                    proc = psutil.Process(pid)
                    match = (proc.name().lower() == process_name_or_pid.lower())
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if match:
                # 确保窗口不是最小化状态
                if win32gui.IsIconic(hwnd):
                    # 如果是最小化状态，先恢复窗口再获取位置
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
                # 获取窗口客户区矩形
                client_rect = win32gui.GetClientRect(hwnd)
                client_left_top = win32gui.ClientToScreen(hwnd, (0, 0))
                client_right_bottom = win32gui.ClientToScreen(hwnd, (client_rect[2], client_rect[3]))
                client_width = client_right_bottom[0] - client_left_top[0]
                client_height = client_right_bottom[1] - client_left_top[1]

                # 确定窗口所在的显示器
                window_center_x = (client_left_top[0] + client_right_bottom[0]) // 2
                window_center_y = (client_left_top[1] + client_right_bottom[1]) // 2

                #monitors = get_monitors()
                with mss.mss() as sct:
                    monitors = sct.monitors
                monitor_info = None
                for monitor in monitors[1:]:
                    if (monitor['left'] <= window_center_x <= monitor['left'] + monitor['width'] and
                        monitor['top'] <= window_center_y <= monitor['top'] + monitor['height']):
                        monitor_info = monitor
                        break
                
                # 如果之前恢复了最小化窗口，现在可以重新最小化
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                
                # 计算相对于显示器的位置
                if monitor_info:
                    relative_x = client_left_top[0] - monitor_info.x
                    relative_y = client_left_top[1] - monitor_info.y

                    windows_info.append({
                        'title': window.title,
                        'pid': pid,
                        'width': client_width,
                        'height': client_height,
                        'absolute_x': client_left_top[0],
                        'absolute_y': client_left_top[1],
                        'monitor': monitor_info,
                        'monitor_width': monitor_info.width,
                        'monitor_height': monitor_info.height,
                        'relative_x': relative_x,
                        'relative_y': relative_y,
                    })
        
        return hwnd, windows_info
    
    except Exception as e:
        print(f"获取窗口信息时出错: {e}")
        return []
    
def get_resolution(process_name="com.bilibili.nslg.exe"):
    hwnd, resolutions = get_process_window_resolution(process_name)
    process = hwnd
    
    if resolutions:
        for i, info in enumerate(resolutions):
            if info['title'] == '':
                continue

            width = info['width']
            height = info['height']

            wh_ratio = width / height if height != 0 else 0
            info['wh_ratio'] = wh_ratio
            info['primary_axis'] = 'height'

            #position_info = info  # 赋值给全局变量
            print(info)
        return info
    else:
        print("未找到匹配的窗口")
        return None