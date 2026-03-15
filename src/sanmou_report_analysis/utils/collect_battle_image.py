import time
import winsound

import cv2
import mss
import numpy as np
import pyautogui
import pygetwindow as gw
import win32gui
from pynput.mouse import Controller as MouseController

from sanmou_report_analysis.utils.control import human_like_move
from sanmou_report_analysis.utils.data_structure import (
    BoundingBox,
    create_lazy_dict,
)
from sanmou_report_analysis.utils.image import (
    are_images_matching,
    is_image_similar_sift,
    read_image,
    save_image,
)

# from sanmou_report_analysis.utils.ocr import ocr_text

process_name = "三国：谋定天下"

# 初始化鼠标控制器
_mouse = MouseController()

process_info = None

_region_dict = {
    "global": [-0.5, 0.08, 0.5, 0.98],
    "战报详情": [0.5, 0.5],
    "战报界面": [-0.4, 0.22, 0.48, 0.88],
    "战报详情按钮": [0.32, 0.95],
    "列队布阵图标": [0.5, 0.1, 0.59, 0.15],
}

_icon_dict = create_lazy_dict(
    {
        "列队布阵": "./images/列队布阵.png",
        "普攻": "./images/normal_attack.png",
    },
    loader=read_image,
)


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
            # windows_info = {
            #    'hwnd': all_windows[0]._hWnd,
            #    'title': process_name,
            # }
            hWnd = all_windows[0]._hWnd
    except Exception as e:
        print(f"获取窗口信息时出错: {e}")
    return hWnd


def convert_relative_xy_to_absolute(x, y):
    if process_info["primary_axis"] == "width":
        absolute_x = process_info["absolute_x"] + x * process_info["width"]
        absolute_y = (
            process_info["absolute_y"] + y * process_info["width"] / process_info["wh_ratio"]
        )
    else:
        absolute_x = (
            process_info["absolute_x"]
            + process_info["width"] / 2
            + x * process_info["height"] * 1.75
        )
        absolute_y = process_info["absolute_y"] + y * process_info["height"]
    return absolute_x, absolute_y


def convert_relative_xy_to_absolute_wrt_bottom(x, y):
    absolute_x = process_info["absolute_x"] + x * process_info["width"]
    absolute_y = process_info["absolute_y"] + y * process_info["height"]
    return absolute_x, absolute_y


def list_to_bbox(box):
    left, top, right, bottom = box
    new_l, new_t = convert_relative_xy_to_absolute(left, top)
    new_r, new_b = convert_relative_xy_to_absolute(right, bottom)
    return BoundingBox((new_l, new_t, new_r, new_b))


def scroll_down():
    dy = np.random.uniform(-0.05, 0.05)
    x0 = np.random.uniform(0.45, 0.55)
    y0 = 0.75 + dy
    x1 = np.random.uniform(0.45, 0.55)
    y1 = 0.35 + dy

    x0, y0 = convert_relative_xy_to_absolute_wrt_bottom(x0, y0)
    x1, y1 = convert_relative_xy_to_absolute_wrt_bottom(x1, y1)

    human_like_move(x0, y0, x1, y1)
    time.sleep(0.5)


def game_global_image(save_dir):
    hwnd = win32gui.FindWindow(None, process_name)
    _, _, w, h = win32gui.GetClientRect(hwnd)
    print(w, h)
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    right, bottom = win32gui.ClientToScreen(hwnd, (w, h))
    width = right - left
    height = bottom - top

    print(f"截图全局游戏界面0: left={left}, top={top}, width={width}, height={height}")
    with mss.mss() as sct:
        screenshot = np.array(
            sct.grab({"left": left, "top": top, "width": width, "height": height})
        )
        # save_image(screenshot, save_dir / "hero_detail" / "global000.png")
        cv2.imshow("Global Game Image", screenshot)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    return screenshot


def check_normal_attack(skill_image):
    gray_patch = cv2.cvtColor(skill_image, cv2.COLOR_BGR2GRAY)
    _, kmask = cv2.threshold(gray_patch, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    nonzero_coords = cv2.findNonZero(kmask)
    kx, ky, kw, kh = cv2.boundingRect(nonzero_coords)
    kmask = kmask[ky : ky + kh, kx : kx + kw]

    template = cv2.cvtColor(_icon_dict["普攻"], cv2.COLOR_BGR2GRAY)
    _, tmask = cv2.threshold(template, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    nonzero_coords = cv2.findNonZero(tmask)
    tx, ty, tw, th = cv2.boundingRect(nonzero_coords)
    tmask = tmask[ty : ty + th, tx : tx + tw]

    tmask = cv2.resize(tmask, (kmask.shape[1], kmask.shape[0]))
    # print(tmask.shape, kmask.shape)

    diff = np.mean(np.abs(tmask - kmask))
    # print('Diff:', diff)
    return diff < 30

    """
    wline = np.sum(mask, axis=0)
    nonzero = np.nonzero(wline)[0]
    if len(nonzero) == 0:
        return False
    start = nonzero[0]
    
    segment_idxs = []
    for i in range(1, len(nonzero)):
        if nonzero[i] != nonzero[i - 1] + 1: 
            end = nonzero[i - 1]
            segment_idxs.append(end - start)
            start = nonzero[i]
    segment_idxs.append((start, nonzero[-1]))
    
    return len(segment_idxs) == 2
    """


def collect_battle_mainpage(save_dir, position_info=None):
    if position_info is not None:
        global process_info
        process_info = position_info
    global_img = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)

    box_full = list_to_bbox(_region_dict["global"])
    image_summary = global_img[box_full.to_slice()]
    save_image(image_summary, save_dir / "hero_detail" / "global.png")

    for team, box_hero in _hero_layout.items():
        for idx in range(3):
            hero_tag = f"{team}{idx + 1}"
            current_box = box_hero.copy()
            current_box[0] = current_box[0] + hero_box_width * idx
            current_box[2] = current_box[2] + hero_box_width * idx

            l2, t2, r2, b2 = current_box
            h, w = image_summary.shape[0:2]
            l_temp = int(l2 * w)
            r_temp = int(r2 * w) + 1
            t_temp = int(t2 * h)
            b_temp = int(b2 * h) + 1
            hero_image = image_summary[t_temp:b_temp, l_temp:r_temp]
            save_image(hero_image, save_dir / "hero_detail" / f"{hero_tag}.png")
            for skill_idx in range(3):
                skill_box = (
                    np.array([l2, t2, l2, t2]) + np.array(_hero_detail_layout["skill"]).copy()
                )
                skill_box[1] = skill_box[1] + hero_skill_height * skill_idx
                skill_box[3] = skill_box[3] + hero_skill_height * skill_idx

                l3, t3, r3, b3 = skill_box
                h, w = image_summary.shape[0:2]
                l_temp = int(l3 * w)
                r_temp = int(r3 * w) + 1
                t_temp = int(t3 * h)
                b_temp = int(b3 * h) + 1

                skill_patch = image_summary[t_temp:b_temp, l_temp:r_temp]
                if check_normal_attack(skill_patch):
                    print(
                        f"{team}队第{idx + 1}个武将的第{skill_idx + 1}个技能检测到普攻，跳过该武将"
                    )
                    break

                save_image(
                    skill_patch, save_dir / "hero_detail" / f"{hero_tag}_{skill_idx + 1}.png"
                )
                l0, t0, _, _ = box_full.to_ltrb()
                x = np.random.uniform(l_temp + l0 + 10, r_temp + l0 - 9)
                y = np.random.uniform(t_temp + t0 + 10, b_temp + t0 - 9)
                pyautogui.click(x=x, y=y)
                time.sleep(0.3)

                current_img = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
                skill_image = current_img[box_full.to_slice()]
                save_image(
                    skill_image, save_dir / "hero_detail" / f"{hero_tag}_skill{skill_idx + 1}.png"
                )

                abs_x = 0.7 * w + l0
                abs_y = -0.03 * h + t0
                pyautogui.click(x=abs_x, y=abs_y)
                time.sleep(0.3)
    return True


def collect_battle_detail(max_n=1000) -> list[np.ndarray]:
    report_box = list_to_bbox(_region_dict["战报界面"])
    report_imgs = []

    abs_x, abs_y = convert_relative_xy_to_absolute_wrt_bottom(*_region_dict["战报详情"])
    pyautogui.click(x=abs_x, y=abs_y)
    time.sleep(0.5)
    for _i in range(max_n):
        global_img = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
        image_summary = global_img[report_box.to_slice()]
        if report_imgs:
            match_result, good_count = is_image_similar_sift(
                image_summary, report_imgs[-1], ratio=0.05, min_match_count=500
            )
            if match_result:
                break
        report_imgs.append(image_summary)
        scroll_down()
    return report_imgs


def get_detail_button_position():
    t = 0.91 * process_info["height"]
    abh = 0.06 * process_info["height"]
    abw = abh * 3.7
    left_offset = abw * 2.22
    # global_img = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
    top = int(process_info["absolute_y"] + t)
    bottom = int(top + abh + 1)
    left = int(process_info["absolute_x"] + left_offset)
    right = int(left + abw + 1)
    return left, top, right, bottom


def get_battle_images(save_dir, position_info):
    global process_info
    process_info = position_info
    collect_battle_mainpage(save_dir)
    for _i in range(3):
        left, top, right, bottom = get_detail_button_position()
        x = np.random.uniform(left + 10, right - 9)
        y = np.random.uniform(top + 10, bottom - 9)
        pyautogui.click(x=x, y=y)
        time.sleep(0.3)

        # Switch to battle report detail page
        global_img = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
        box_full = list_to_bbox(_region_dict["global"])
        global_img = global_img[box_full.to_slice()]

        l2, t2, r2, b2 = _region_dict["列队布阵图标"].copy()
        h, w = global_img.shape[0:2]
        l_temp = int(l2 * w)
        r_temp = int(r2 * w) + 1
        t_temp = int(t2 * h)
        b_temp = int(b2 * h) + 1
        flag_image = global_img[t_temp:b_temp, l_temp:r_temp]
        match_result, good_count = are_images_matching(flag_image, _icon_dict["列队布阵"])
        if match_result:
            time.sleep(2)
            break
    else:
        winsound.Beep(400, 1000)
        raise RuntimeError("未能定位到'列队布阵'")

    image_list = collect_battle_detail()
    for image_idx, image in enumerate(image_list):
        save_path = save_dir / "images_to_stitch" / f"{image_idx:04d}.png"
        save_image(image, save_path)
    print("All image stitches were saved.")
    return image_list
