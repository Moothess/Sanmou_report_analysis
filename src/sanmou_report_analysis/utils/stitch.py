from pathlib import Path
import time
import functools
import winsound

import numpy as np
import cv2
import keyboard

from sanmou_report_analysis.utils.data_structure import MatchResult, TextColor, BoundingBox, create_lazy_dict
from sanmou_report_analysis.utils.image import *
from sanmou_report_analysis.utils.process_info import get_resolution
from sanmou_report_analysis.utils.collect_battle_image import get_battle_images

color_map = {
    TextColor.WHITE: (255, 255, 255),
    TextColor.BLUE: (255, 0, 0),
    TextColor.RED: (92, 92, 255),
    TextColor.MAROON: (255, 0, 255),
    TextColor.GREEN: (0, 255, 0),
    TextColor.YELLOW: (0, 255, 255),
    TextColor.ORANGE: (0, 128, 255),
    TextColor.ICON: (255, 100, 166),
}

def get_image_mask_by_color_new(image_hsv, color: TextColor):
    if color == TextColor.WHITE:
        # 白色 (Saturation < 50, value > 75)
        lower_white = np.array([0, 0, 75])
        upper_white = np.array([180, 20, 255])
        mask = cv2.inRange(image_hsv, lower_white, upper_white)
    elif color == TextColor.BLUE:
        # 蓝色 (Hue 90-110, Saturation 125-165)
        lower_blue = np.array([90, 110, 108])
        upper_blue = np.array([110, 255, 255])
        mask = cv2.inRange(image_hsv, lower_blue, upper_blue)
        
        #kernel = np.ones((3, 3), np.uint8)
        #mask = cv2.erode(mask, kernel, iterations=1)
        #mask = cv2.dilate(mask, kernel, iterations=1)
    elif color == TextColor.RED:
        # 深红色 (Hue 170-180, Saturation 50-255, Value 50-255)
        lower_red1 = np.array([0, 60, 60])
        upper_red1 = np.array([10, 180, 255])
        lower_red2 = np.array([170, 60, 60])
        upper_red2 = np.array([180, 180, 255])
        #mask_red = cv2.inRange(image_hsv, lower_red1, upper_red1)
        mask_red1 = cv2.inRange(image_hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(image_hsv, lower_red2, upper_red2)
        #mask = cv2.bitwise_or(mask_red1, mask_red2)
        
        bgr = cv2.cvtColor(image_hsv, cv2.COLOR_HSV2BGR)
        lower_red3 = np.array([55, 55, 100])
        upper_red3 = np.array([120, 120, 255])
        mask_red3 = cv2.inRange(bgr, lower_red3, upper_red3)
        #print("light red", np.sum(mask_red3 > 0))
        
        mask = cv2.bitwise_and(cv2.bitwise_or(mask_red1, mask_red2), mask_red3)
    elif color == TextColor.MAROON:
        # 浅红色 (Hue 0-10, Saturation 100-200, Value 150-255)
        lower_red1 = np.array([0, 180, 60])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 180, 60])
        upper_red2 = np.array([180, 255, 255])
        #mask_red = cv2.inRange(image_hsv, lower_red1, upper_red1)
        mask_red1 = cv2.inRange(image_hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(image_hsv, lower_red2, upper_red2)
        #mask = cv2.bitwise_or(mask_red1, mask_red2)
        
        bgr = cv2.cvtColor(image_hsv, cv2.COLOR_HSV2BGR)
        lower_red3 = np.array([0, 0, 100])
        upper_red3 = np.array([55, 55, 255])
        mask_red3 = cv2.inRange(bgr, lower_red3, upper_red3)
        #print("dark red", np.sum(mask_red3 > 0))

        mask = cv2.bitwise_and(cv2.bitwise_or(mask_red1, mask_red2), mask_red3)
    elif color == TextColor.GREEN:
        # 绿色 (Hue 50-75, Saturation 100-255)
        lower_green = np.array([50, 23, 60])
        upper_green = np.array([80, 255, 255])
        mask = cv2.inRange(image_hsv, lower_green, upper_green)
    elif color == TextColor.ORANGE:
        # 橙色 (Hue 10-30, Saturation 75-165)
        #lower_orange = np.array([10, 50, 0])
        #upper_orange = np.array([30, 255, 255])
        lower_orange = np.array([10, 0, 0])
        upper_orange = np.array([19, 180, 255])
        mask = cv2.inRange(image_hsv, lower_orange, upper_orange)
    elif color == TextColor.YELLOW:
        # 黄色 (Hue 10-30, Saturation 75-165)
        lower_yellow = np.array([20, 62, 0])
        upper_yellow = np.array([30, 180, 255])
        mask = cv2.inRange(image_hsv, lower_yellow, upper_yellow)
    elif color == TextColor.ICON:
        lower_icon = np.array([10, 10, 0])
        upper_icon = np.array([70, 75, 255])
        mask = cv2.inRange(image_hsv, lower_icon, upper_icon)
    else:
        raise RuntimeError(f"Unsupported color {color}")
    return mask


def get_image_mask_by_color(image_hsv, color: TextColor):
    if color == TextColor.WHITE:
        # 白色 (Saturation < 50, value > 75)
        lower_white = np.array([0, 0, 75])
        upper_white = np.array([180, 20, 255])
        mask = cv2.inRange(image_hsv, lower_white, upper_white)
    elif color == TextColor.BLUE:
        # 蓝色 (Hue 90-110, Saturation 125-165)
        lower_blue = np.array([90, 110, 100])
        upper_blue = np.array([110, 255, 255])
        mask = cv2.inRange(image_hsv, lower_blue, upper_blue)
        
        #kernel = np.ones((3, 3), np.uint8)
        #mask = cv2.erode(mask, kernel, iterations=1)
        #mask = cv2.dilate(mask, kernel, iterations=1)
    elif color == TextColor.RED:
        # 深红色 (Hue 170-180, Saturation 50-255, Value 50-255)
        lower_red1 = np.array([0, 60, 60])
        upper_red1 = np.array([10, 180, 255])
        lower_red2 = np.array([170, 60, 60])
        upper_red2 = np.array([180, 180, 255])
        #mask_red = cv2.inRange(image_hsv, lower_red1, upper_red1)
        mask_red1 = cv2.inRange(image_hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(image_hsv, lower_red2, upper_red2)
        
        bgr = cv2.cvtColor(image_hsv, cv2.COLOR_HSV2BGR)
        lower_red3 = np.array([55, 55, 100])
        upper_red3 = np.array([120, 120, 255])
        mask_red3 = cv2.inRange(bgr, lower_red3, upper_red3)
        #print("light red", np.sum(mask_red3 > 0))
        
        mask = cv2.bitwise_and(cv2.bitwise_or(mask_red1, mask_red2), mask_red3)
    elif color == TextColor.MAROON:
        # 浅红色 (Hue 0-10, Saturation 100-200, Value 150-255)
        lower_red1 = np.array([0, 180, 60])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 180, 60])
        upper_red2 = np.array([180, 255, 255])
        #mask_red = cv2.inRange(image_hsv, lower_red1, upper_red1)
        mask_red1 = cv2.inRange(image_hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(image_hsv, lower_red2, upper_red2)
        
        bgr = cv2.cvtColor(image_hsv, cv2.COLOR_HSV2BGR)
        lower_red3 = np.array([0, 0, 100])
        upper_red3 = np.array([55, 55, 255])
        mask_red3 = cv2.inRange(bgr, lower_red3, upper_red3)
        #print("dark red", np.sum(mask_red3 > 0))

        mask = cv2.bitwise_and(cv2.bitwise_or(mask_red1, mask_red2), mask_red3)
    elif color == TextColor.GREEN:
        # 绿色 (Hue 50-75, Saturation 100-255)
        lower_green = np.array([50, 26, 0])
        upper_green = np.array([80, 255, 255])
        mask = cv2.inRange(image_hsv, lower_green, upper_green)
    elif color == TextColor.ORANGE:
        # 橙色 (Hue 10-30, Saturation 75-165)
        #lower_orange = np.array([10, 50, 0])
        #upper_orange = np.array([30, 255, 255])
        lower_orange = np.array([10, 100, 0])
        upper_orange = np.array([19, 180, 255])
        mask = cv2.inRange(image_hsv, lower_orange, upper_orange)
    elif color == TextColor.YELLOW:
        # 黄色 (Hue 10-30, Saturation 75-165)
        lower_yellow = np.array([20, 62, 0])
        upper_yellow = np.array([30, 180, 255])
        mask = cv2.inRange(image_hsv, lower_yellow, upper_yellow)
    elif color == TextColor.ICON:
        lower_icon = np.array([20, 25, 0])
        upper_icon = np.array([70, 65, 255])
        mask = cv2.inRange(image_hsv, lower_icon, upper_icon)
    else:
        raise RuntimeError(f"Unsupported color {color}")
    return mask

def stitch_images_by_matching_row(images, match_rows=35):
    if not images:
        raise ValueError("图像列表不能为空")

    result = images[0].copy()
    for i in range(1, len(images)):
        prev_img = result
        curr_img = images[i]
        h_prev = prev_img.shape[0]
        h_curr = curr_img.shape[0]
        
        curr_head = curr_img[10:10+match_rows]
        current_min = 1e10
        current_match = -1
        #print(h_prev, h_curr)
        stop = h_prev - h_curr // 2 if i < len(images) - 2 else h_prev - h_curr - match_rows
        for offset in range(h_prev - match_rows, stop, -1):
            prev_tail = prev_img[offset:offset + match_rows]
            if prev_tail.shape[0] != match_rows:
                continue
            diff = np.abs(prev_tail.astype(np.int16) - curr_head.astype(np.int16))
            max_diff = np.mean(diff) + np.max(diff)
            if current_min > max_diff:
                current_min = max_diff
                current_match = offset
        
        result = np.vstack([prev_img[:current_match], curr_img[10:]])
    return result

def enhance_image(image_bgr, repaint=True):
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
    image_bgr = image_bgr * (binary > 0)[..., None].astype(image_bgr.dtype)
    image_hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    color2mask: dict[TextColor, np.ndarray] = {color: get_image_mask_by_color(image_hsv, color) for color in TextColor if color != TextColor.OTHER}
    mask = functools.reduce(lambda x, y: x + y, color2mask.values())

    if repaint:
        enhanced_image = np.zeros_like(image_bgr)
        for color, mask_c in color2mask.items():
            #print(color)
            enhanced_image[mask_c > 0] = color_map[color]
    else:
        enhanced_image = cv2.bitwise_and(image_bgr, image_bgr, mask=mask)
    return enhanced_image

def stitch_images_old(image_list, save_dir):
    if image_list == []:
        save_images_dir = save_dir / "images_to_stitch"
        for img_path in sorted(save_images_dir.glob("*.png")):
            img = cv2.imread(str(img_path))
            if img is not None:
                image_list.append(img)
    
    images_to_stitch = []
    for idx, image in enumerate(image_list):
        image_to_stitch = enhance_image(image)

        if idx + 1 < len(image_list):
            h = int(image_to_stitch.shape[0] * 0.85)
            image_to_stitch = image_to_stitch[:h]
        images_to_stitch.append(image_to_stitch)
    
    panorama = stitch_images_by_matching_row(images_to_stitch)
    save_image(panorama, save_dir / "panorama.png")


def stitch_images(image_list, save_dir, repaint=True):
    if image_list == []:
        save_images_dir = save_dir / "images_to_stitch"
        for img_path in sorted(save_images_dir.glob("*.png")):
            img = cv2.imread(str(img_path))
            if img is not None:
                image_list.append(img)

    mean_image = cv2.imread("images/mean_image.png")
    images_to_stitch = []
    for idx, image in enumerate(image_list):
        mimg = cv2.resize(mean_image, (image.shape[1], image.shape[0]))
        image_to_stitch = cv2.absdiff(image, mimg)
        
        gray = cv2.cvtColor(image_to_stitch, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.dilate(binary, kernel, iterations=1)
        image_to_stitch = image * (binary > 0)[..., None].astype(image.dtype)
        
        image_hsv = cv2.cvtColor(image_to_stitch, cv2.COLOR_BGR2HSV)
        color2mask: dict[TextColor, np.ndarray] = {color: get_image_mask_by_color(image_hsv, color) for color in TextColor if color != TextColor.OTHER}
        mask = functools.reduce(lambda x, y: x + y, color2mask.values())

        if repaint:
            enhanced_image = np.zeros_like(image_to_stitch)
            for color, mask_c in color2mask.items():
                enhanced_image[mask_c > 0] = color_map[color]
        else:
            enhanced_image = cv2.bitwise_and(image_to_stitch, image_to_stitch, mask=mask)
            
        
        if idx + 1 < len(image_list):
            h = int(enhanced_image.shape[0] * 0.85)
            enhanced_image = enhanced_image[:h]
        images_to_stitch.append(enhanced_image)
    
    panorama = stitch_images_by_matching_row(images_to_stitch)
    save_image(panorama, save_dir / "panorama.png")
