import pickle
import re

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm

from sanmou_report_analysis.utils.data_structure import TextColor
from sanmou_report_analysis.utils.image import read_image, save_image
from sanmou_report_analysis.utils.ocr import ocr_text  # , ColoredOCRer
from sanmou_report_analysis.utils.sentence import LineSentence
from sanmou_report_analysis.utils.stitch import get_image_mask_by_color


def which_color(bgr):
    if np.sum(abs(bgr - np.array([92, 92, 255]))) < 21:
        return TextColor.RED
    elif np.sum(abs(bgr - np.array([255, 255, 255]))) < 21:
        return TextColor.WHITE
    elif np.sum(abs(bgr - np.array([255, 0, 0]))) < 21:
        return TextColor.BLUE
    elif np.sum(abs(bgr - np.array([0, 255, 0]))) < 21:
        return TextColor.GREEN
    elif np.sum(abs(bgr - np.array([0, 255, 255]))) < 21:
        return TextColor.YELLOW
    elif np.sum(abs(bgr - np.array([0, 128, 255]))) < 21:
        return TextColor.ORANGE
    elif np.sum(abs(bgr - np.array([255, 0, 255]))) < 21:
        return TextColor.MAROON
    elif np.sum(abs(bgr - np.array([255, 100, 166]))) < 21:
        return TextColor.ICON
    return None


def check_patch_with_color(seg_img, text_color):
    # 判断该patch的主要颜色是不是目标颜色
    seg_img_gray = cv2.cvtColor(seg_img, cv2.COLOR_BGR2GRAY)
    _, binarized = cv2.threshold(seg_img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    binarized = binarized // 255

    seg_img_hsv = cv2.cvtColor(seg_img, cv2.COLOR_BGR2HSV)
    icon_mask = get_image_mask_by_color(seg_img_hsv, text_color) // 255

    iou = np.sum(binarized * icon_mask) / (np.sum(binarized) + 1e-6)
    return iou


def split_line_by_color(line_img):
    line_img_gray = cv2.cvtColor(line_img, cv2.COLOR_BGR2GRAY)
    # 获取图像中文字区域的最小外接矩形
    hist = np.max(line_img_gray, axis=0)

    nonzero_pts = cv2.findNonZero(line_img_gray)
    xa, ya, wa, ha = cv2.boundingRect(nonzero_pts)

    nonzero = np.nonzero(hist)[0]
    if len(nonzero) == 0:
        return []
    start = nonzero[0]
    end = nonzero[-1]

    patch_idx = []

    seg_img_hsv = cv2.cvtColor(line_img, cv2.COLOR_BGR2HSV)
    max_color = None
    max_pixel = 10
    max_mask = None
    for number_color in [TextColor.GREEN, TextColor.YELLOW, TextColor.MAROON, TextColor.ORANGE]:
        # 这几个颜色区域一般只会出现一个，因此只需要找到最大的颜色块即可
        cmask = get_image_mask_by_color(seg_img_hsv, number_color)
        num_pixel = np.sum(cmask)
        if num_pixel > max_pixel:
            max_pixel = num_pixel
            max_color = number_color
            max_mask = cmask

    if max_color is not None:
        # 如果有上述颜色块，则将该区域记录下来
        nonzero_pts = cv2.findNonZero(max_mask)
        xn, yn, wn, hn = cv2.boundingRect(nonzero_pts)
        patch_idx.append((xn, xn + wn, max_color))

    for text_color in [TextColor.BLUE, TextColor.RED]:
        # 武将对应的颜色块一般有1-2个
        cmask = get_image_mask_by_color(seg_img_hsv, text_color)
        nonzero_pts = cv2.findNonZero(cmask)
        if nonzero_pts is not None:
            xw, yw, ww, hw = cv2.boundingRect(nonzero_pts)
            if ww < 10:
                save_image(cmask, debug_dir / f"line_{xw}_{xw + ww}_{text_color.value}_img.png")
            # 如果有2个颜色块，一半宽高比会超过5，所以据此判断个数
            if ww / hw < 5:
                patch_idx.append((xw, xw + ww, text_color))
            else:
                # 有多个武将标签，需要进一步拆分
                # 这里采用从武将颜色块开始，寻找一个连续的空白区域（相邻像素>10）作为分割点
                chist = 1 - (np.max(cmask, axis=0) > 10)
                nonzero = np.nonzero(chist)[0]

                start = xw + 1
                for i in range(1, len(nonzero)):
                    if nonzero[i] != nonzero[i - 1] + 1:
                        if nonzero[i - 1] - start > 10:
                            # print(xw, start, nonzero[i], xw+ww)
                            if start - xw > 5:
                                patch_idx.append((xw, start, text_color))
                            if xw + ww - nonzero[i] > 5:
                                patch_idx.append((nonzero[i], xw + ww, text_color))
                            break
                        elif nonzero[i] > start + 3:
                            start = nonzero[i]
                else:
                    patch_idx.append((xw, xw + ww, text_color))

    # 找到所有非白色区域的左右边缘，将整体的文字边缘按照这些区域进行划分，其余部分则为白色区域
    patch_idx.sort(key=lambda x: x[0])
    colored_segments = []
    for _iii, pidx in enumerate(patch_idx):
        if len(colored_segments) == 0:
            colored_segments.append(pidx)
        else:
            pre_start, pre_end, pre_color = colored_segments[-1]
            cur_start, cur_end, cur_color = pidx
            if cur_start <= pre_end:
                if cur_end > pre_end:
                    colored_segments[-1] = (pre_start, cur_end, pre_color)
            elif cur_start > pre_end + 8:
                colored_segments.append([pre_end + 1, cur_start - 1, TextColor.WHITE])
                colored_segments.append(pidx)

    # 如果最后一个颜色块没有覆盖到文字的最右边，则补充一个白色块
    if len(colored_segments) > 0:
        final_end = colored_segments[-1][1]
        if final_end < end:
            colored_segments.append((final_end + 1, end, TextColor.WHITE))
    else:
        colored_segments.append((xa, xa + wa, TextColor.WHITE))

    # 目前每行战斗记录不会超过6个颜色块，超过则应该是识别错误，需要debug
    if len(colored_segments) > 6:
        save_image(line_img, debug_dir / f"line_{xw}_{xw + ww}_{text_color.value}_img.png")
        save_image(cmask, debug_dir / f"line_{xw}_{xw + ww}_{text_color.value}_mask.png")
        error_image = debug_dir / f"line_{xw}_{xw + ww}_{text_color.value}_img.png"
        raise RuntimeError(f"检测到过多的颜色块，可能是识别错误，请检查图片: {error_image}")
    return colored_segments


def split_image_to_lines(panorama):
    segment_idxs = []
    row_hist = np.max(panorama, axis=(1, 2)).astype(int)

    # 可视化 hist
    """
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 4))
    plt.plot(hist.astype(int))
    plt.title("Row activation histogram (hist)")
    plt.xlabel("Row index")
    plt.ylabel("Active (1/0)")
    plt.tight_layout()
    plt.show()
    """

    # 按照纵向像素值分布，识别每一行记录的区域
    top = -1
    for row_idx in range(len(row_hist)):
        if top == -1 and row_hist[row_idx] > 30:
            top = row_idx
        elif top > -1 and (
            ((row_hist[row_idx - 1] - row_hist[row_idx]) > 80) or (row_hist[row_idx] < 30)
        ):
            btm = row_idx
            # 两行记录拼接在一起了，需要拆分
            if btm - top > 35:
                inter = int((btm + top) / 2) + 1
                segment_idxs.append([top, inter])
                segment_idxs.append([inter, btm])
            elif btm - top < 4:
                pass
            else:
                segment_idxs.append([top + 1, btm])
            top = -1

    action_list = []
    stage_dict = {}
    round = 0
    # TODO debug mode
    # 逐行分析
    sttt = 0  # 4900
    for _seg_idx, (seg_top, seg_btm) in enumerate(segment_idxs[sttt:]):
        seg_img = panorama[seg_top:seg_btm]

        seg_hist = np.max(np.array(seg_img), axis=(0, 2))
        nonzero = np.where(seg_hist > 0)[0]
        start = nonzero[0]

        # 找到每行第一个图像块，判断是否为兵种图标，不是则判定为上一行的延续
        first_end = start
        for i in range(1, len(nonzero)):
            if nonzero[i] != nonzero[i - 1] + 1:
                first_end = nonzero[i - 1]
                if first_end - start > 2:
                    break
                else:
                    start = nonzero[i]
        else:
            first_end = nonzero[-1]

        if check_patch_with_color(seg_img[:, start : first_end + 1], TextColor.ICON) > 0.5:
            # 行首有兵种图表
            right = min(nonzero[-1] + 5, seg_img.shape[1])
            img_patch = seg_img[:, first_end + 1 : right]

            # 去除每行下方可能出现的横线
            valid = False
            while not valid:
                if img_patch.shape[0] == 0:
                    break
                seg_img_grey = cv2.cvtColor(img_patch, cv2.COLOR_BGR2GRAY)
                seg_img_x = seg_img_grey[-1]  # np.max(seg_img_grey, axis=0)
                # print(seg_img_x.shape)
                nonzero = np.where(seg_img_x > 0)[0]
                if len(nonzero) > 0:
                    start = nonzero[0]
                    early_break = False
                    for i in range(1, len(nonzero)):
                        if nonzero[i] != nonzero[i - 1] + 1:
                            end = nonzero[i - 1]
                            if end - start + 1 > 45:
                                img_patch = img_patch[:-1]
                                early_break = True
                                break
                            start = nonzero[i]
                    if early_break:
                        continue

                    end = nonzero[-1]
                    if end - start + 1 > 45:
                        img_patch = img_patch[:-1]
                        continue

                valid = True
            if not valid:
                # utils.save_image(seg_img, debug_dir / f"line_{seg_idx}_{seg_top}-{seg_btm}.png")
                continue

            stage_dict.setdefault(round, []).append(img_patch)

        else:
            if round not in action_list:
                wwmask_nonzero = np.where(np.max(seg_img, axis=0) > 0)[0]
                wwleft = wwmask_nonzero[0]
                yyright = wwmask_nonzero[-1]

                # 特殊情况：有可能是“行动顺序”判定
                seg_img_hsv = cv2.cvtColor(seg_img, cv2.COLOR_BGR2HSV)
                wmask = get_image_mask_by_color(seg_img_hsv, TextColor.WHITE)
                ymask = get_image_mask_by_color(seg_img_hsv, TextColor.YELLOW)

                # 检查wmask的最左边和ymask的最右边
                if np.sum(wmask) > 20 and np.sum(ymask) > 20:
                    wmask_nonzero = np.where(np.max(wmask, axis=0) > 0)[0]
                    ymask_nonzero = np.where(np.max(ymask, axis=0) > 0)[0]

                    if len(wmask_nonzero) > 0 and len(ymask_nonzero) > 0:
                        wmask_left = wmask_nonzero[0]
                        ymask_right = ymask_nonzero[-1]

                        if wmask_left == wwleft and ymask_right == yyright:
                            action_list.append(round)
                            continue

                segs = split_line_by_color(seg_img)
                if len(segs) == 2 and (
                    segs[0][2] == TextColor.WHITE and segs[1][2] == TextColor.YELLOW
                ):
                    # 特殊情况：行动顺序判定
                    action_list.append(round)
                    continue

            # if check_patch_with_color(seg_img[:, start:first_end + 1], TextColor.WHITE) > 0.5:
            #    continue

            # 行首没有兵种图表，需要与前面行拼接
            seg_img = seg_img[1:-1, start:]
            img_width = len(seg_hist)
            if start > img_width * 0.35 and start < img_width * 0.5:
                # 新一回合的开始
                round += 1
            else:
                if round in stage_dict:
                    first_line = stage_dict[round][-1]
                    first_line_gray = cv2.cvtColor(first_line, cv2.COLOR_BGR2GRAY)
                    col_sum = np.sum(first_line_gray, axis=0)
                    nonzero_cols = np.where(col_sum > 0)[0]
                    if len(nonzero_cols) > 0:
                        rightmost = min(nonzero_cols[-1] + 1, first_line.shape[1])
                        first_line = first_line[:, :rightmost]

                    valid = False
                    while not valid:
                        if seg_img.shape[0] == 0:
                            break

                        # print(seg_img.shape)
                        seg_img_grey = cv2.cvtColor(seg_img, cv2.COLOR_BGR2GRAY)
                        seg_img_x = np.max(seg_img_grey, axis=0)
                        # print(seg_img_x.shape)
                        nonzero = np.where(seg_img_x > 0)[0]
                        if len(nonzero) > 0:
                            start = nonzero[0]
                            early_break = False
                            for i in range(1, len(nonzero)):
                                if nonzero[i] != nonzero[i - 1] + 1:
                                    end = nonzero[i - 1]
                                    if end - start + 1 > 45:
                                        seg_img = seg_img[1:]
                                        early_break = True
                                        break
                                    start = nonzero[i]
                            if early_break:
                                continue

                            end = nonzero[-1]
                            if end - start + 1 > 45:
                                seg_img = seg_img[1:]
                                continue

                        valid = True

                    if not valid:
                        continue

                    # 去掉seg_img左边全为0的部分图像
                    seg_img_gray = cv2.cvtColor(seg_img, cv2.COLOR_BGR2GRAY)
                    col_sum = np.sum(seg_img_gray, axis=0)
                    nonzero_cols = np.where(col_sum > 0)[0]
                    if len(nonzero_cols) > 0:
                        leftmost = max(nonzero_cols[0] - 1, 0)
                        rightmost = min(nonzero_cols[-1] + 1, seg_img.shape[1])
                        seg_img = seg_img[:, leftmost:rightmost]

                    # 使seg_img和first_line高度一致
                    height_diff = seg_img.shape[0] - first_line.shape[0]
                    if height_diff > 0:
                        pad_top = height_diff // 2
                        pad_bottom = height_diff - pad_top
                        first_line = np.pad(
                            first_line,
                            ((pad_top, pad_bottom), (0, 0), (0, 0)),
                            mode="constant",
                            constant_values=0,
                        )
                    elif height_diff < 0:
                        pad_top = (-height_diff) // 2
                        pad_bottom = -height_diff - pad_top
                        seg_img = np.pad(
                            seg_img,
                            ((pad_top, pad_bottom), (0, 0), (0, 0)),
                            mode="constant",
                            constant_values=0,
                        )
                    connector = np.zeros((seg_img.shape[0], 3, 3), dtype=seg_img.dtype)
                    merged_img = np.concatenate([first_line, connector, seg_img], axis=1)

                    # utils.save_image(merged_img, f"./line_{round}_{len(stage_dict[round])}.png")
                    stage_dict[round][-1] = merged_img
    return stage_dict


def get_text_from_patch(seg_img, start, end, text_color, hero_names, scale=2.0):
    tag_img0 = seg_img[:, start:end]
    nonzero_coords = cv2.findNonZero(
        cv2.cvtColor(tag_img0, cv2.COLOR_BGR2GRAY) if tag_img0.ndim == 3 else tag_img0
    )
    x, y, w, h = cv2.boundingRect(nonzero_coords)
    if h < 5:
        return ""

    tag_img0 = tag_img0[y : y + h, x : x + w]

    if text_color in [TextColor.BLUE, TextColor.RED]:
        if tag_img0.shape[1] / tag_img0.shape[0] > 5:
            # 规避成功，后面有个“的伤害”
            text_hist = np.max(np.array(tag_img0), axis=(0))
            nonzero = np.where(text_hist > 0)[0]
            right = nonzero[-1]
            for i in range(len(nonzero) - 1, 0, -1):
                if nonzero[i - 1] != nonzero[i] - 1:
                    left = nonzero[i]
                    if right - left < 10:
                        # right = left - 1
                        break
                    else:
                        right = nonzero[i - 1]
            else:
                right = nonzero[-1]
            tag_img0 = tag_img0[:, : right + 1]

        potential_names = hero_names[text_color.value]
        min_diff = 1e6
        best_name = ""
        for pot_name, pot_img in potential_names.items():
            tag_img1 = tag_img0.copy()  # [y:y+h, x:x+w]
            tag_img1 = cv2.cvtColor(tag_img1, cv2.COLOR_BGR2GRAY)
            tag_img1 = cv2.threshold(tag_img1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

            text_hist = np.max(np.array(tag_img1), axis=(1))
            nonzero = np.where(text_hist > 0)[0]
            top = nonzero[0]
            for i in range(1, len(nonzero)):
                if nonzero[i] != nonzero[i - 1] + 1:
                    btm = nonzero[i - 1]
                    if btm - top > 5:
                        break
                    top = nonzero[i]
            else:
                btm = nonzero[-1]
            tag_img1 = tag_img1[top : btm + 1, :]

            text_hist = np.max(np.array(tag_img1), axis=(0))
            nonzero = np.where(text_hist > 0)[0]
            start = nonzero[0]

            start1 = start
            for i in range(1, len(nonzero)):
                if nonzero[i] != nonzero[i - 1] + 1:
                    start1 = nonzero[i - 1]
                    break

            end1 = nonzero[-1]
            for i in range(len(nonzero) - 2, 0, -1):
                if nonzero[i] != nonzero[i + 1] - 1:
                    end1 = nonzero[i + 1]
                    break

            if end1 - start1 < 10:
                save_image(seg_img, debug_dir / f"line_{start}_{end}_cut.png")
                return None

            tag_img1 = tag_img1[:, start1 + 1 : end1 - 1]
            xp, yp, wp, hp = cv2.boundingRect(cv2.findNonZero(tag_img1))
            tag_img1 = tag_img1[yp : yp + hp, xp : xp + wp]

            pot_img = cv2.resize(
                pot_img, (tag_img1.shape[1], tag_img1.shape[0]), interpolation=cv2.INTER_LINEAR
            )

            diff = np.mean(np.abs(pot_img.astype(np.float32) - tag_img1.astype(np.float32)))
            if diff < min_diff:
                min_diff = diff
                best_name = pot_name
        # print('名字部分误差：', min_diff, best_name)
        if min_diff < 110:
            return best_name
        else:
            print("名字部分误差：", min_diff, best_name)
            return None

    elif text_color in [TextColor.YELLOW, TextColor.MAROON, TextColor.GREEN, TextColor.ORANGE]:
        ocr_success = False
        fail_count = 0
        scale = 3
        while not ocr_success:
            if w < 11:
                tag_img = np.pad(
                    tag_img0, ((19, 19), (7, 7), (0, 0)), mode="constant", constant_values=0
                )
            else:
                tag_img = np.pad(
                    tag_img0, ((7, 7), (7, 7), (0, 0)), mode="constant", constant_values=0
                )

            tag_img = cv2.cvtColor(tag_img, cv2.COLOR_BGR2GRAY)
            _, tag_img = cv2.threshold(tag_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            h0, w0 = tag_img.shape[:2]
            tag_img = cv2.resize(
                tag_img, (int(w0 * scale), int(h0 * scale)), interpolation=cv2.INTER_LINEAR
            )
            ocr_results = ocr_text(tag_img)
            pads = []
            for ocr_res in ocr_results:
                pads.append(ocr_res.text.strip())
            pad_str = "".join(pads)

            if fail_count > 15:
                # print(f"OCR识别失败过多次，放弃该patch: {pad_str}，宽高：{w}, {h}")
                # save_image(tag_img0, debug_dir / f"line_{start}_{end}.png")
                # raise RuntimeError(f"OCR识别失败过多次，放弃该patch: {pad_str}，宽高：{w}，{h}")
                print("数字识别失败：", pad_str)
                return None

            if not re.match(r"^[\d.%]+$", pad_str):
                fail_count += 1
                scale += 0.2
            else:
                break

        return pad_str

    else:
        assert text_color == TextColor.WHITE
        ocr_success = False
        fail_count = 0
        scale = 2
        while not ocr_success:
            tag_img = np.pad(tag_img0, ((7, 7), (7, 7), (0, 0)), mode="constant", constant_values=0)

            tag_img = cv2.cvtColor(tag_img, cv2.COLOR_BGR2GRAY)
            _, tag_img = cv2.threshold(tag_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            h0, w0 = tag_img.shape[:2]
            tag_img = cv2.resize(
                tag_img, (int(w0 * scale), int(h0 * scale)), interpolation=cv2.INTER_LINEAR
            )
            ocr_results = ocr_text(tag_img)
            pads = []
            for ocr_res in ocr_results:
                pads.append(ocr_res.text.strip())
            pad_str = "".join(pads)

            if pad_str != "":
                ocr_success = True
            else:
                fail_count += 1
                scale += 0.2
                if fail_count > 15:
                    return None

        return pad_str


def find_sentence(color_list):
    max_sim = 0
    best_sentence = None
    potential_sentences = [
        subclass
        for subclass in LineSentence.__subclasses__()
        if subclass.len_patch == len(color_list)
    ]
    for subclass in potential_sentences:
        cur_sim = subclass.match(color_list)
        if cur_sim == 1:
            return subclass(color_list)
        else:
            if cur_sim > max_sim:
                max_sim = cur_sim
                best_sentence = subclass

    if max_sim >= 0.7:
        return best_sentence(color_list)
    else:
        return f"未匹配到任何模式: {color_list}"


def get_potential_sentence_list(seg_img, seg_list, hero_names, factor=1.0):
    # 识别每行记录中每个颜色区域的文本内容
    color_list = []
    for start, end, text_color in seg_list:
        pad_str = get_text_from_patch(seg_img, start, end, text_color, hero_names, scale=factor)
        if pad_str is None:
            return ""  # None #f'文本识别有误({pad_str})，请手动处理'
        color_list.append((pad_str, text_color))
    # 匹配句式并返回。具体匹配过程见utils/sentence.py
    return find_sentence(color_list)


def analysis_image_by_lines(panorama, hero_names):
    # 将战报全图分解成一行行的战斗记录，并按照回合数保存
    stage_dict = split_image_to_lines(panorama)

    print(f"战斗报告总共包含{len(stage_dict.keys())}个回合.")
    round_dict = {}
    unmatched_lines = {}
    for round, seg_imgs in stage_dict.items():
        inner = tqdm(seg_imgs, desc=f"正在分析第{round}回合", unit="行", ncols=100)
        line_texts = []
        for i, seg_img in enumerate(seg_imgs):
            # 将每行战斗记录按照文字颜色分割成多个片段
            seg_list = split_line_by_color(seg_img)
            # 按照颜色片段顺序和文字内容识别具体句式
            sentence = get_potential_sentence_list(seg_img, seg_list, hero_names, factor=1)
            if isinstance(sentence, LineSentence):
                line_texts.append(sentence)
            else:
                # 句式识别失败，需要检查优化代码
                assert isinstance(sentence, str), "分析代码BUG，请检查！"
                print(sentence)
                line_texts.append(None)
                unmatched_lines[f"{round}_{i}"] = seg_img
                save_image(seg_img, debug_dir / f"Round{round}_Line{i}.png")
            inner.update(1)

        round_dict[round] = line_texts

    # 如果上述分析过程有识别失败的部分，则需要人工补充
    # 将未匹配行的图像保存到指定文件夹，人工查看图像内容后，
    # 按照“文本内容_颜色;文本内容_颜色;...”的格式输入。
    # 若输入文本有误则需要重新输入，直到输入的内容成功匹配句式
    if len(unmatched_lines) > 0:
        print("开始处理未匹配行的图像，请打开文件夹：", debug_dir)
    for key, _img in unmatched_lines.items():
        round, line = key.split("_")

        match = False
        while not match:
            input_str = input(f"请输入第{round}回合，第{line}行的文本内容：")
            sent_list = []
            patches = input_str.split(";")
            for patch in patches:
                ptext, pcolor = patch.split("_")
                color = TextColor[pcolor.upper()]
                sent_list.append([ptext, color])

            sentence = find_sentence(sent_list)
            if isinstance(sentence, LineSentence):
                round_dict[int(round)][int(line)] = sentence
                match = True
            else:
                print("输入数据解析失败，请重新输入！")

    return round_dict


def text_to_image(text, font_size=40, font_path=None):
    font_path = "C:/Windows/Fonts/simhei.ttf"
    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except OSError:
        font = ImageFont.load_default()

    approx_width = len(text) * font_size + 100
    img_width = min(approx_width, 1000)
    img_height = font_size * 2

    img = Image.new("L", (img_width, img_height), color=0)
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), text, font=font, fill="white")
    return np.array(img)


def get_img_by_name(hero_name):
    # img = text_to_image(f'[{hero_name}]', font_size=35)
    img = text_to_image(hero_name, font_size=35)
    xp, yp, wp, hp = cv2.boundingRect(cv2.findNonZero(img))
    img = img[yp : yp + hp, xp : xp + wp]
    img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return img


def image_to_report(battle_report_dir, meta_info):
    save_dir = battle_report_dir
    line_sentence_path = save_dir / "sentence.pkl"
    global debug_dir
    debug_dir = save_dir / "unmatched"

    # 武将名识别可能有误，这里改为用已识别到的武将名生成模板图，
    # 再用待识别图像与模板图的像素差最小值来确定武将名字。
    hero_names = {"blue": {}, "red": {}}
    for side, heroes in meta_info.items():
        for _hero_idx, info in heroes.items():
            color = "blue" if side == "left" else "red"
            hero_name = info[0]["name"]
            hero_names[color][hero_name] = get_img_by_name(hero_name)
            # save_image(hero_names[color][hero_name], f"./temp/hero_{color}_{hero_name}.png")
            # print(img.shape)

    # logger.info(f"获取{idx}的report。")
    image_path = battle_report_dir / "panorama.png"
    print(f"Analyze battle image: {image_path}")
    panorama = read_image(image_path)
    stage_dict = analysis_image_by_lines(panorama, hero_names)

    with open(line_sentence_path, "wb") as f:
        pickle.dump(stage_dict, f)
    return stage_dict
