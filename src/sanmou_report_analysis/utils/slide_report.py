from pathlib import Path
import time
import functools
import winsound

import numpy as np
import mss
import cv2
import keyboard
import win32gui
import pyautogui
import pygetwindow as gw

from sanmou_report_analysis.utils.data_structure import MatchResult, TextColor, BoundingBox, create_lazy_dict
from sanmou_report_analysis.utils.image import *
from sanmou_report_analysis.utils.control import human_like_move
from sanmou_report_analysis.utils.collect_battle_image import collect_battle_mainpage

from sanmou_report_analysis.utils.meta_info import extract_meta_info
import pandas as pd
#from sanmou_report_analysis.utils.ocr import ocr_text

process_name = "三国：谋定天下"


process_info = None

_region_dict = { 
    "global": [-0.5, 0.08, 0.5, .98],
    "战报详情": [0.5, 0.5], 
    "战报界面": [-0.4, 0.22, 0.48, 0.88], 
    "战报详情按钮": [0.32, 0.95],
    "列队布阵图标": [0.5, 0.1, 0.59, 0.15],
}

_icon_dict = create_lazy_dict({
    "列队布阵": "./images/fold.png",
    "普攻": "./images/normal_attack.png",
}, loader=read_image)


hero_box_width = 0.1365
_hero_layout = {
    "left": [0.005, 0.165, 0.135, 0.57],
    "right": [0.595, 0.165, 0.725, 0.57],
}

hero_skill_height = 0.1
_hero_detail_layout = {
    "skill": [-0.004, 0.415, 0.07, 0.505],
}

def get_hwnd(process_name="三国：谋定天下"):
    hWnd = None
    try:
        all_windows = gw.getWindowsWithTitle(process_name)
        if all_windows:            
            #windows_info = {
            #    'hwnd': all_windows[0]._hWnd,
            #    'title': process_name,
            #}
            hWnd = all_windows[0]._hWnd
    except Exception as e:
        print(f"获取窗口信息时出错: {e}")
    return hWnd

def convert_relative_xy_to_absolute(x, y):
    if process_info['primary_axis'] == 'width':
        absolute_x = process_info['absolute_x'] + x * process_info['width']
        absolute_y = process_info['absolute_y'] + y * process_info['width'] / process_info['wh_ratio']
    else:
        absolute_x = process_info['absolute_x'] + process_info['width'] / 2 + x * process_info['height'] * 1.75
        absolute_y = process_info['absolute_y'] + y * process_info['height']
    return absolute_x, absolute_y

def convert_relative_xy_to_absolute_wrt_bottom(x, y):
    absolute_x = process_info['absolute_x'] + x * process_info['width']
    absolute_y = process_info['absolute_y'] + y * process_info['height']
    return absolute_x, absolute_y

def list_to_bbox(box):
    l, t, r, b = box
    new_l, new_t = convert_relative_xy_to_absolute(l, t)
    new_r, new_b = convert_relative_xy_to_absolute(r, b)
    return BoundingBox((new_l, new_t, new_r, new_b))


def scroll_down(start, end):
    dy = np.random.uniform(-0.02, 0.02)
    x0 = np.random.uniform(0.45, 0.55)
    y0 = start + dy    
    x1 = np.random.uniform(0.45, 0.55)
    y1 = end + dy
    
    x0, y0 = convert_relative_xy_to_absolute_wrt_bottom(x0, y0)
    x1, y1 = convert_relative_xy_to_absolute_wrt_bottom(x1, y1)
    
    human_like_move(x0, y0, x1, y1)
    time.sleep(0.5)

def get_battle_center(save_dir):    
    global_img = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
    
    
    # TODO 如果当前战报有折叠，需要点击一下展开
    check_folded_and_expand(global_img)
    time.sleep(0.5)
        
        
    
    box_full = list_to_bbox([-0.05, 0.17, 0.05, 0.95])
    image_center = global_img[box_full.to_slice()]
    image_center = cv2.cvtColor(image_center, cv2.COLOR_BGR2GRAY)
    _, image_center = cv2.threshold(image_center, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    #save_image(image_center, save_dir / "current_center.png")
    
    img = np.array(image_center).astype(np.uint8)
    max_img = np.max(img, axis=1)
    y_len = max_img.shape[0] # 0.78
    
    nonzero_indices = np.where(max_img > 0)[0]
    if len(nonzero_indices) > 0:
        gaps = np.diff(nonzero_indices) > 1
        regions = np.split(nonzero_indices, np.where(gaps)[0] + 1)
        #print(f"连续非0区域: {regions}")
    
    res = []
    for region in regions:
        len_region = len(region)
        if len_region > y_len * 0.10:
            center = (region[0] + region[-1]) // 2
            cent = center * 1. / y_len * 0.78 + 0.17
            res.append(cent)
            if len(res) >= 2:
                break
        
    #print(regions)
    return res

def format_csv(info_dict, save_dir):
    #print(info_dict)
    all_battle = []
    for battle in info_dict:
        info_dict_row = {}
        for team_name, team_info in battle.items():
            for hero_idx, hero_info in team_info.items():
                country = hero_info[0]['country'].value
                troop_type = hero_info[0]['troop_type'].value
                level = hero_info[0]['level']
                name = hero_info[0]['name']
                red = hero_info[0]['n_red']
                final_hp = hero_info[0]['final_hp']
                initial_hp = hero_info[0]['initial_hp']
                
                new_team_name = '蓝' if team_name == 'left' else '红'
                prefix = new_team_name + '队第' + str(hero_idx) + '个武将'
                
                info_dict_row[prefix] = name
                info_dict_row[prefix + '红度'] = red
                info_dict_row[prefix + '兵种'] = troop_type
                info_dict_row[prefix + '初始兵力'] = initial_hp
                info_dict_row[prefix + '最终兵力'] = final_hp
                
                for i in range(1, len(hero_info)):
                    skill_info = hero_info[i]
                    skill_name = skill_info['skill_name']
                    skill_red = skill_info['n_red']
                    info_dict_row[prefix + '技能'+str(i)+'名称'] = skill_name
                    info_dict_row[prefix + '技能'+str(i)+'红度'] = skill_red
                    
        all_battle.append(info_dict_row)
                
        #print(battle)
    df = pd.DataFrame(all_battle)
    df.to_csv(save_dir / "battle_info.csv", index=False, encoding='utf-8-sig')
    #pass

def check_folded_and_expand(global_img):
    box_button = list_to_bbox([0.46, 0.17, 0.5, 0.95])
    image_button = global_img[box_button.to_slice()]
    
    match_result, good_count = are_images_matching(image_button, _icon_dict["列队布阵"])
    if match_result is not None:
        print('找到列队布阵图标，说明战报被折叠，点击展开')
        #abs_x, abs_y = convert_relative_xy_to_absolute(0.32, 0.95)
        #pyautogui.click(x=abs_x, y=abs_y)
        #time.sleep(0.5)

def collect_battle(save_dir, max_n=3, position_info=None):
    info_dict = []
    
    for i in range(max_n):
        res = get_battle_center(save_dir)
        click_center = max(0.3, res[0])
        
        # 进入战报详细界面
        abs_x, abs_y = convert_relative_xy_to_absolute(0., click_center)
        pyautogui.click(x=abs_x, y=abs_y)
        time.sleep(0.5)
        
        battle_save_dir = save_dir / f"battle_{i:03d}"
        
        collect_battle_mainpage(battle_save_dir, position_info)
        all_info = extract_meta_info(battle_save_dir)
        info_dict.append(all_info)
        
        # 退出战报详细界面
        abs_x, abs_y = convert_relative_xy_to_absolute(-0.45, 0.03)
        pyautogui.click(x=abs_x, y=abs_y)
        time.sleep(0.5)
        
        # 向上滑动战报
        abs_x, abs_y = convert_relative_xy_to_absolute(0, res[1])
        pyautogui.moveTo(x=abs_x, y=abs_y)
        time.sleep(0.3)
        scroll_down(res[1], 0.3)
    
    format_csv(info_dict, save_dir)

def slide_battle_images(save_dir, position_info, max_n=3):    
    global process_info
    process_info = position_info
    
    collect_battle(save_dir, max_n, position_info)
        
    
    #collect_battle_mainpage(save_dir)
    
