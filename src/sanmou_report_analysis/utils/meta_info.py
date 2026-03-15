import os
import re
import cv2
import tqdm
import json
import pickle
import numpy as np
import pandas as pd

from tqdm import tqdm
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

#from utils
from sanmou_report_analysis.utils.ocr import ocr_text
from sanmou_report_analysis.utils.image import *
from sanmou_report_analysis.utils.sentence import *
from sanmou_report_analysis.utils.data_structure import *

_troop_type_icon_dict = create_lazy_dict(
    {
        TroopType.盾兵: "./images/troop_type/troop_type_dun_bing.png",
        TroopType.弓兵: "./images/troop_type/troop_type_gong_bing.png",
        TroopType.枪兵: "./images/troop_type/troop_type_qiang_bing.png",
        TroopType.骑兵: "./images/troop_type/troop_type_qi_bing.png",
    }
)

_hero_summary_dict = create_lazy_dict(
    {
        "red_hero": "./images/red_hero.png",
        "red_skill": "./images/red_skill.png",
        "masked_red": "./images/masked_red.png",
    }
)

hero_detail_layout = {
    "country": [0.02, 0.06, 0.13, 0.18],
    #"troop_type": [0.2, 0.09, 0.25, 0.175],
    "troop_type": [0.195, 0.085, 0.255, 0.18],
    "n_red": [0.67, 0.17, 0.78, 0.82], 
    "level_name": [0.77, 0.185, 0.86, 0.825],
    "hp": [0.9, 0.18, 0.98, 0.82],
}

skill_detail_layout = {
    "name": [0.04, 0.05, 0.11, 0.18],
    "level": [0.15, 0.46, 0.21, 0.52],
    "n_red": [0.53, 0.16, 0.6, 0.29],
}

def get_image_from_box(image, box):
    h, w, _ = image.shape
    l = int(box[0] * h)
    t = int(box[1] * w)
    r = int(box[2] * h)
    b = int(box[3] * w)
    box_abs = [l, t, r, b]
    box_region = image[box_abs[0]:box_abs[2], box_abs[1]:box_abs[3]]
    return box_region

def match_hero_country(image):
    box = hero_detail_layout["country"]
    box_region = get_image_from_box(image, box)
    mask = cv2.cvtColor(box_region, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask_bool = mask > 0
    if np.count_nonzero(mask_bool) == 0:
        raise RuntimeError("mask区域为空，无法计算平均颜色")
    avg_color = np.mean(box_region[mask_bool], axis=0)
    b, g, r = avg_color
    if not (b > 100 and g > 100 and r > 100):
        b = b * 2 
        g = g * 2
        r = r * 2
    bgr_arr = np.clip(np.round([b, g, r]), 0, 255).astype(np.uint8)
    bgr_img = bgr_arr.reshape((1, 1, 3))  # 1x1 BGR 图像
    hsv_color = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)[0, 0]
    h, s, v = int(hsv_color[0]), int(hsv_color[1]), int(hsv_color[2])
    
    if h < 135 and h > 115:
        return Country.群
    elif h < 90 and h > 35:
        return Country.蜀
    elif h < 20 or h > 160:
        return Country.吴
    elif h < 115 and h > 100:
        return Country.魏
    else:
        raise RuntimeError("无法识别国家颜色")
    

def match_hero_troop_type(image):
    box = hero_detail_layout["troop_type"]
    box_region = get_image_from_box(image, box)
    box_region = cv2.cvtColor(box_region, cv2.COLOR_BGR2GRAY)
    _, box_region = cv2.threshold(box_region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    coords = cv2.findNonZero(box_region)
    if coords is not None:
        x, y, w, h = cv2.boundingRect(coords)
        box_region = box_region[y:y+h, x:x+w]

    #save_image(box_region, f"./temp/hero_troop_type.png")

    matched_type = None
    max_match = 255
    for target_name, target_img in _troop_type_icon_dict.items():
        conv_img = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
        _, conv_img = cv2.threshold(conv_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        coords = cv2.findNonZero(conv_img)
        if coords is not None:
            x0, y0, w0, h0 = cv2.boundingRect(coords)
            conv_img = conv_img[y0:y0+h0, x0:x0+w0]
            
            conv_img = cv2.resize(conv_img, (box_region.shape[1], box_region.shape[0]), interpolation=cv2.INTER_LINEAR)

            #print(conv_img.shape, box_region.shape)
            diff = np.mean(np.abs(conv_img - box_region))
            if diff < max_match:
                #save_image(conv_img, f"./temp/n_{target_name}_2.png")
                max_match = diff
                matched_type = target_name
    if matched_type is None:
        raise RuntimeError("没有匹配到兵种。")
    return matched_type

def match_n_red(image, target) -> int:
    if target == "hero":
        box = hero_detail_layout["n_red"]
    elif target == "skill":
        box = skill_detail_layout["n_red"]
    else:
        raise NotImplementedError()
    
    grey = False
    if target == "hero":
        r, g, b = np.mean(image, axis=(0,1))
        if r < 50 and g < 60 and b < 65:
            grey = True
    
    box_region = get_image_from_box(image, box)
    icon = _hero_summary_dict["masked_red"]
    icon_gray = cv2.cvtColor(icon, cv2.COLOR_BGR2GRAY)
    coords = cv2.findNonZero(icon_gray)
    if coords is not None:
        x, y, w, h = cv2.boundingRect(coords)
        icon = icon[y:y+h, x:x+w]
    
    if grey:
        box_region = box_region * 2
    
    mask = np.ones(box_region.shape[:2], dtype=bool)
    box_region_hsv = cv2.cvtColor(box_region, cv2.COLOR_BGR2HSV)
    icon_hsv = cv2.cvtColor(icon, cv2.COLOR_BGR2HSV)
    mask = np.all([
        (box_region_hsv[..., c] >= np.min(icon_hsv[..., c][icon_hsv[..., c] > 0])) &
        (box_region_hsv[..., c] <= np.max(icon_hsv[..., c]))
        for c in range(3)
    ], axis=0)
    mask = np.expand_dims(mask.astype(np.uint8), axis=-1)
    box_region = mask * box_region
    
    icon_h, icon_w = icon.shape[:2]
    box_h = box_region.shape[0]
    scale = box_h / icon_h
    new_w = int(icon_w * scale)
    icon_resized = cv2.resize(icon, (new_w, box_h), interpolation=cv2.INTER_LINEAR)
    icon = icon_resized

    match_results = count_template_matches(icon, box_region, threshold=0.6)
    #print(match_results)
    return len(match_results)

def match_hp(image):
    box = hero_detail_layout["hp"]
    box_region = get_image_from_box(image, box)
    
    # 在R通道使用otsu算法得到mask
    r_channel = box_region[:, :, 2]
    _, mask = cv2.threshold(r_channel, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask_orig = np.pad(mask, ((7, 7), (7, 7)), mode='constant', constant_values=0)
    
    matched = False
    match_times = 0
    while not matched:
        match_times += 1
        if match_times > 5:
            print("HP识别失败")
            break

        factor = 2.8 + match_times * 0.2
        h, w = mask_orig.shape[:2]
        mask = cv2.resize(mask_orig, (int(w * factor), int(h * factor)), interpolation=cv2.INTER_LINEAR)
        
        ocr_result = ocr_text(mask)
        if ocr_result:
            hp_str = ocr_result[0].text
            hp_str = hp_str.strip().replace('／', '/')
            hp_str = hp_str.replace('O', '0').replace('o', '0')
            hp_str = re.sub(r'\s+', '', hp_str)
            #print(f"识别到的HP字符串: {hp_str}")
            if not re.fullmatch(r'\d+/\d+', hp_str):
                continue
            final_hp, initial_hp = [int(x) for x in hp_str.split("/")]
            if final_hp < initial_hp and final_hp < 10000 and initial_hp <= 10000:
                matched = True
                return final_hp, initial_hp


    return 0, 0

def ocr_hero_level_name(image) -> tuple[int, str]:
    box = hero_detail_layout["level_name"]
    box_region = get_image_from_box(image, box)
    
    r, g, b = np.mean(image, axis=(0,1))
    # 武将阵亡导致rgb过暗，放大亮度
    if r < 50 and g < 60 and b < 65:
        box_region = box_region * 2
        
    mask = cv2.cvtColor(box_region, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    h, w = box_region.shape[:2]
    factor = 3
    matched = False
    while not matched:
        box_region = cv2.resize(box_region, (w * factor, h * factor), interpolation=cv2.INTER_LINEAR)
        ocr_results = ocr_text(box_region)
        if len(ocr_results) == 0:
            raise RuntimeError("未识别到等级和武将名")
        elif len(ocr_results) == 1:
            text = ocr_results[0].text
            if text[1].isdigit():
                level = int(text[:2])
                name = text[2:]
            else:
                level = int(text[:1])
                name = text[1:]
        elif len(ocr_results) == 2:
            #print(ocr_results)
            if ocr_results[0].box.l < ocr_results[1].box.l:
                level = int(''.join(filter(str.isdigit, ocr_results[0].text)))
                name = ocr_results[1].text
            else:
                level = int(''.join(filter(str.isdigit, ocr_results[1].text)))
                name = ocr_results[0].text
            #level = int(ocr_results[0].text)
            #name = ocr_results[1].text
        else:
            raise RuntimeError(f"识别到过多结果: {ocr_results}")
        
        if level >=0 and level <=50:
            matched = True
        else:
            factor += 0.2
            if factor > 5:
                raise RuntimeError(f"无法识别武将等级: {level} {name}")
    return level, name

def ocr_skill_name(image) -> str:
    box = skill_detail_layout["name"]
    box_region = get_image_from_box(image, box)
    
    box_region = cv2.cvtColor(box_region, cv2.COLOR_BGR2GRAY)
    _, box_region = cv2.threshold(box_region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    #print("Skill Name OCR Result:", ocr_text(box_region))
    name = ocr_text(box_region)[0].text
    #name = correct_text(name)
    return name

def ocr_skill_level(image) -> int:
    box = skill_detail_layout["level"]
    box_region = get_image_from_box(image, box)
    box_region = cv2.cvtColor(box_region, cv2.COLOR_BGR2GRAY)
    _, box_region = cv2.threshold(box_region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    #utils.save_image(box_region, f"./n_red_.png")
    
    text = ocr_text(box_region)[0].text
    if text[-1] != "级":
        raise RuntimeError("最后一个字不是“级”")
    return int(text[:-1])

def extract_info_from_hero_image(image):
    country = match_hero_country(image)
    troop_type = match_hero_troop_type(image)
    n_red = match_n_red(image, "hero")
    level, name = ocr_hero_level_name(image)
    final_hp, initial_hp = match_hp(image)

    hero_info = {
        "country": country,
        "troop_type": troop_type,
        "level": level,
        "name": name.strip(),
        "n_red": n_red,
        "final_hp": final_hp,
        "initial_hp": initial_hp,
    }
    return hero_info

def extract_info_from_skill_image(image):
    skill_name = ocr_skill_name(image)
    skill_level = ocr_skill_level(image)
    n_red = match_n_red(image, "skill")
    
    skill_info = {
        "skill_name": skill_name,
        "skill_level": skill_level,
        "n_red": n_red,
    }
    return skill_info

def print_meta_info(meta_info):
    info_str = []
    hero_info = meta_info[0]
    hero_name = hero_info['name'].rjust(6-len(hero_info['name']))
    level_str = f"Lv.{hero_info['level']}".rjust(5)
    troop_type_str = hero_info['troop_type'].name
    country_str = hero_info['country'].name
    red_str = ("★" * hero_info['n_red']).ljust(5)
    hp_str = f"{hero_info['final_hp']:>5}/{hero_info['initial_hp']:>5}"
    #print(len(f"{hero_name} ({level_str}级{troop_type_str}, {country_str})， 红度: {red_str} 生命: {hp_str}"))
    hero_str = f"{hero_name}({level_str}{troop_type_str}, {country_str}) {red_str}  兵力:{hp_str}"
    #print(len(hero_str))
    #info_str.append(hero_str)

    for skill_info in meta_info[1:]:
        skill_name = skill_info['skill_name'].rjust(8-len(skill_info['skill_name']))
        level_str = f"Lv.{skill_info['skill_level']}".rjust(5)
        red_str = ("★" * skill_info['n_red']).ljust(5)
        info_str.append(f"{skill_name}({level_str}) {red_str}")

    print(f"  {hero_str} || " + " | ".join(info_str))
    
def extract_meta_info(battle_report_dir):
    data_dir = battle_report_dir / "hero_detail"
    meta_info_path = battle_report_dir / "meta_info.json"
    
    all_info = {'left': {}, 'right': {}}
    for team in all_info.keys():
        print('蓝队：' if team == 'left' else '红队：')
        for hero_idx in range(1, 4):
            hero_image_path = data_dir / f"{team}{hero_idx}.png"
            if not hero_image_path.exists():
                continue
            image = read_image(hero_image_path)
            
            hero_info = []
            hero_info.append(extract_info_from_hero_image(image))
            
            for skill_idx in range(1, 4):
                skill_image_path = data_dir / f"{team}{hero_idx}_skill{skill_idx}.png"
                if not skill_image_path.exists():
                    continue
                image = read_image(skill_image_path)
                if image is None:
                    continue
                hero_info.append(extract_info_from_skill_image(image))
            
            print_meta_info(hero_info)
            all_info[team][hero_idx] = hero_info
            
    with open(meta_info_path, "w", encoding="utf-8") as f:
        json.dump(all_info, f, indent=4, ensure_ascii=False)
    return all_info