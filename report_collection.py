# Author: Mian Qin
# Date Created: 2024/10/27
from pathlib import Path
import time
import functools
import winsound

import numpy as np
import pyautogui
import cv2
import keyboard

from utils.data_structure import MatchResult, TextColor, BoundingBox, create_lazy_dict
from utils.image import *
from utils.process_info import get_resolution
from utils.collect_battle_image import get_battle_images
from utils.stitch import stitch_images
from report_analysis import main_phase2

def collect_report(stage1):
    root_dir = Path("./data")
    idx_list = [int(path.name) for path in root_dir.iterdir()]
    current_idx = max(idx_list) + 1 if stage1 else max(idx_list)
    save_dir = root_dir / str(current_idx)
    if stage1:
        print("按s开始。按q退出。")
        stop = True
        while stop:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == "s":
                    position_info = get_resolution()
                    image_list = get_battle_images(save_dir, position_info)
                    stitch_images(image_list, save_dir, repaint=False)

                    current_idx += 1
                    stop = False
                    print("按s开始。按q退出。")
                    #winsound.Beep(300, 1000)
                if event.name == "q":
                    break
        keyboard.unhook_all()
    else:
        stitch_images([], save_dir, repaint=False)

def main():
    # 两个步骤：1.实时截图，2.截图拼接
    # stage1设置是否重新获取截图，为False的话只会拼接已经截好的图
    stage1 = True
    collect_report(stage1)
    main_phase2()

if __name__ == "__main__":
    main()


