# Author: Mian Qin
# Date Created: 2025/6/28
import re
import shutil
from pathlib import Path
from typing import Union

import cv2
import numpy as np
from PIL import ImageGrab

from sanmou_report_analysis.utils.data_structure import *

def ltrb_to_ltwh(left, top, right, bottom):
    """
    Convert from (left, top, right, bottom) to (left, top, width, height).
    """
    width = right - left
    height = bottom - top
    return left, top, width, height

def ltwh_to_ltrb(left, top, width, height):
    """
    Convert from (left, top, width, height) to (left, top, right, bottom).
    """
    right = left + width
    bottom = top + height
    return left, top, right, bottom

def screenshot(save_path=None, region_ltrb=(0, 0, 1920, 1080)):
    """
    使用 PIL.ImageGrab 截图
    Color mode: RGB
    :param save_path: 保存路径（可选）
    :param region_ltrb: 区域 (left, top, right, bottom)
    :return: BGR 格式的 numpy 数组
    """
    # PIL.ImageGrab.grab 接受 (left, top, right, bottom) 格式
    img = ImageGrab.grab(bbox=region_ltrb)
    
    if save_path is not None:
        img.save(save_path)
    
    img = np.array(img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img

_re_pattern_dict = create_lazy_dict(
    {
        "valid_path": r"^[a-zA-Z0-9_\.\/\\\-\s]+$"
    }, loader=re.compile
)


def is_valid_path(path: Union[str, Path]) -> bool:
    # 正则表达式：仅允许 字母、数字、下划线、点、斜杠、反斜杠、连字符、空格
    if isinstance(path, Path):
        path = str(path)
    pattern = _re_pattern_dict["valid_path"]
    return bool(re.fullmatch(pattern, path))


def read_image(file_path: Path | str) -> np.ndarray:
    if is_valid_path(file_path):
        image = cv2.imread(file_path)
    else:
        temp_path = "./.temp.png"
        shutil.copy(file_path, temp_path)
        image = cv2.imread(temp_path)
        Path(temp_path).unlink()
    return image


def save_image(image, save_path: Union[Path, str], log=False):
    if isinstance(save_path, str):
        save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    if is_valid_path(save_path):
        success = cv2.imwrite(str(save_path), image)
    else:
        temp_path = "./.temp.png"
        success = cv2.imwrite(temp_path, image)
        shutil.move(temp_path, save_path)
    #if log:
    #    if success:
    #        logger.debug(f"Saved image to {save_path}")
    #    else:
    #        logger.error(f"Failed to save image to {save_path}")


def get_region(region_ltrb, save_path=None):
    img = screenshot(save_path, region_ltrb=region_ltrb)
    return img


def get_full_screen(save_path=None):
    region_ltrb = (0, 0, 3840, 2064)
    img = screenshot(save_path, region_ltrb=region_ltrb)
    return img


def nms(match_results: list[Union[MatchResult, tuple[MatchResult, dict]]],
        threshold: Union[int, np.ndarray]
        ) -> list[Union[MatchResult, tuple[MatchResult, dict]]]:
    """
    带临时属性的NMS实现

    :param match_results: 包含MatchResult和临时属性的元组列表 [(match_result, attrs), ...]
    :param threshold: 抑制阈值(可int或np.ndarray)
    :return: 经过NMS处理的结果 [(match_result, attrs), ...]
    """
    if len(match_results) == 0:
        return match_results
    if isinstance(match_results[0], MatchResult):
        extra_attributes = False
        match_results = [(match_result, {}) for match_result in match_results]
    else:
        extra_attributes = True
    # 按置信度降序排序（通过元组的第一个元素MatchResult访问score）
    match_results.sort(key=lambda x: x[0].score, reverse=True)

    results_after_nms = []
    while match_results:
        # 取出当前最高分结果及其属性
        best_match, best_attrs = match_results[0]
        results_after_nms.append((best_match, best_attrs))

        center = np.array(best_match.box.center)
        remain_result = []

        for match, attrs in match_results[1:]:
            pos = np.array(match.box.center)
            # 计算距离并比较阈值
            if np.all(np.abs(pos - center) < threshold):
                continue  # 抑制该结果
            remain_result.append((match, attrs))

        match_results = remain_result

    if not extra_attributes:
        results_after_nms = [result[0] for result in results_after_nms]
    return results_after_nms


def distance_transform(image_binary):
    image_dist = cv2.distanceTransform(image_binary, cv2.DIST_L2, 3)
    return image_dist



def match_icon(icon, image, mode=cv2.TM_CCOEFF_NORMED, threshold=0.8, nms_threshold=20) \
        -> list[MatchResult]:
    assert mode in [cv2.TM_CCOEFF_NORMED, cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]
    if np.any(np.array(icon.shape[:2]) > np.array(image.shape[:2])):
        return []
    result = cv2.matchTemplate(image, icon, mode)
    #print(np.max(result))
    if mode in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        result = 1 - result
    loc = np.where(result >= threshold)
    confidence = result[loc]
    dx, dy = icon.shape[:2]
    match_result = [MatchResult((l, t, l + dy, t + dx), c) for t, l, c in zip(*loc, confidence)]
    match_result_after_nms = nms(match_result, nms_threshold)
    return match_result_after_nms


def match_icon_many(image_bgr, icon_bgr_list, mode=cv2.TM_CCOEFF_NORMED, threshold=0.8, nms_across_type=True,
                    nms_threshold=20) \
        -> list[list[MatchResult]]:
    if isinstance(threshold, float) or isinstance(threshold, int):
        threshold = [threshold for _ in range(len(icon_bgr_list))]

    match_results_list = []
    for i, (icon_bgr, t) in enumerate(zip(icon_bgr_list, threshold)):
        match_results = match_icon(icon_bgr, image_bgr, mode=mode, threshold=t)
        match_results_list.append(match_results)
    if nms_across_type:
        result_to_nms = []
        for i, match_results in enumerate(match_results_list):
            for result in match_results:
                result_to_nms.append((result, {"icon_idx": i}))
        result_after_nms = nms(result_to_nms, threshold=nms_threshold)
        match_results_list: list[list[MatchResult]] = [[] for _ in range(len(icon_bgr_list))]
        for result in result_after_nms:
            icon_idx = result[1]["icon_idx"]
            match_results_list[icon_idx].append(result[0])
    return match_results_list


def draw_boxes(image_bgr, box_list: list[BoundingBox], color=(0, 0, 255), thickness=2):
    new_image = image_bgr.copy()
    for box in box_list:
        l, t, r, b = box.to_ltrb()
        cv2.rectangle(new_image, (l, t), (r, b), color, thickness)
    return new_image


def resize_image(image, scale_factor: float):
    """
    按比例缩放图片
    :param image: 原始图片
    :param scale_factor: 缩放比例
    :return: 缩放后的图片
    """
    height, width = image.shape[:2]  # 获取原始高度和宽度
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)

    # 使用cv2.resize进行缩放
    resized_img = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    return resized_img

def are_images_matching(img1, img2, match_threshold=0.8, reprojection_threshold=5.0, min_matches=5):
    """
    通过仿射变换判断两张图片是否匹配
    
    参数:
    img1: 第一张图片 (numpy数组或文件路径)
    img2: 第二张图片 (numpy数组或文件路径)
    match_threshold: 特征匹配阈值 (默认0.8)
    reprojection_threshold: 重投影误差阈值 (默认5.0)
    min_matches: 最小匹配点数量 (默认10)
    
    返回:
    bool: 图片是否匹配
    float: 匹配置信度 (0-1之间)
    """
    
    # 如果输入是文件路径，则读取图片
    if isinstance(img1, str):
        img1 = cv2.imread(img1, cv2.IMREAD_GRAYSCALE)
    if isinstance(img2, str):
        img2 = cv2.imread(img2, cv2.IMREAD_GRAYSCALE)
    
    # 确保图片是灰度图
    if len(img1.shape) == 3:
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    if len(img2.shape) == 3:
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # 初始化SIFT检测器
    sift = cv2.SIFT_create()
    
    # 检测关键点和描述符
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)
    
    # 如果没有足够的关键点，返回不匹配
    if des1 is None or des2 is None or len(des1) < 2 or len(des2) < 2:
        return False, 0.0
    
    # 使用FLANN匹配器进行特征匹配
    index_params = dict(algorithm=1, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    
    matches = flann.knnMatch(des1, des2, k=2)
    
    # 应用Lowe's比率测试筛选好的匹配点
    good_matches = []
    for m, n in matches:
        if m.distance < match_threshold * n.distance:
            good_matches.append(m)
    
    # 如果没有足够的良好匹配点，返回不匹配
    if len(good_matches) < min_matches:
        return False, 0.0
    
    # 提取匹配点的坐标
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    
    # 使用RANSAC算法计算仿射变换矩阵
    M, mask = cv2.estimateAffine2D(src_pts, dst_pts, method=cv2.RANSAC, 
                                  ransacReprojThreshold=reprojection_threshold)
    
    if M is None:
        return False, 0.0
    
    # 计算内点数量 (RANSAC中的一致点)
    inlier_count = np.sum(mask)
    confidence = inlier_count / len(good_matches)
    
    # 如果内点比例足够高，则认为图片匹配
    if inlier_count >= min_matches and confidence > 0.5:
        return True, confidence
    else:
        return False, confidence

def is_image_similar_sift(img1, img2, ratio=0.75, min_match_count=18):
    """
    使用SIFT特征和KNN匹配判断两张图片是否相似。
    :param img1: 第一张图片（BGR或灰度）
    :param img2: 第二张图片（BGR或灰度）
    :param ratio: Lowe's ratio，用于筛选优质匹配
    :param min_match_count: 最小匹配点数，超过则认为相似
    :return: (is_similar: bool, match_count: int)
    """
    # 转为灰度
    if len(img1.shape) == 3:
        img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    else:
        img1_gray = img1
    if len(img2.shape) == 3:
        img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    else:
        img2_gray = img2

    #print(img1_gray.shape, img2_gray.shape)
    # 比较两张图片大小，将大的resize成和小的一致
    #h1, w1 = img1_gray.shape
    #h2, w2 = img2_gray.shape
    #area1 = h1 * w1
    #area2 = h2 * w2
    #if area1 > area2:
    #    img1_gray = cv2.resize(img1_gray, (w2, h2), interpolation=cv2.INTER_AREA)
    #elif area2 > area1:
    #    img2_gray = cv2.resize(img2_gray, (w1, h1), interpolation=cv2.INTER_AREA)

    sift = cv2.SIFT_create()
    kp1, des1 = sift.detectAndCompute(img1_gray, None)
    kp2, des2 = sift.detectAndCompute(img2_gray, None)

    if des1 is None or des2 is None:
        return False, 0

    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)

    # 筛选优质匹配
    good = []
    for m, n in matches:
        if m.distance < ratio * n.distance:
            good.append(m)

    is_similar = len(good) >= min_match_count
    return is_similar, len(good)

def find_template_matches(
    large_img: np.ndarray,          # 大图像 (BGR格式)
    template: np.ndarray,            # 小模板 (BGR格式)
    threshold: float = 0.8,         # 相似度阈值 (0-1)
    method: int = cv2.TM_CCOEFF_NORMED,  # 匹配算法
    nms_threshold: float = 0.5,     # 非极大值抑制阈值
    multi_scale: bool = True,      # 启用多尺度检测
    scales: list = range(5, 15)  # 缩放比例
):  # 返回匹配矩形位置和置信度
    
    # 转换为灰度图以提高性能
    large_gray = cv2.cvtColor(large_img, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    # 获取模板尺寸
    h, w = template_gray.shape[:2]
    
    # 存储所有匹配结果
    all_matches = []

    # 确定检测模式（单尺度或多尺度）
    search_scales = [1.0] if not multi_scale else scales
    
    for scale_orig in search_scales:
        scale = scale_orig / 10.
        # 计算当前缩放比例
        if scale != 1.0:
            resized_w = max(5, int(w * scale))
            resized_h = max(5, int(h * scale))
            scaled_template = cv2.resize(template_gray, (resized_w, resized_h))
        else:
            scaled_template = template_gray
        
        # 如果模板比图像大则跳过
        if scaled_template.shape[0] > large_gray.shape[0] or scaled_template.shape[1] > large_gray.shape[1]:
            continue
        
        # 执行模板匹配
        result = cv2.matchTemplate(large_gray, scaled_template, method)
        
        # 根据匹配方法调整结果处理
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            loc = np.where(result <= (1.0 - threshold) if method == cv2.TM_SQDIFF_NORMED else threshold)
        else:
            loc = np.where(result >= threshold)
        
        # 收集所有匹配结果
        for pt in zip(*loc[::-1]):
            match_score = result[pt[1], pt[0]]
            rect = (*pt, resized_w, resized_h)  # (x, y, w, h)
            all_matches.append((rect, float(match_score)))
    
    # 如果没有找到匹配则返回空列表
    if not all_matches:
        return []
    
    # 非极大值抑制（NMS）过滤重叠结果
    rects = [rect for rect, score in all_matches]
    scores = [score for rect, score in all_matches]
    
    # 使用OpenCV的NMSBoxes
    indices = cv2.dnn.NMSBoxes(
        bboxes=rects, 
        scores=scores, 
        score_threshold=threshold, 
        nms_threshold=nms_threshold
    )
    
    # 收集最终结果
    final_matches = []
    for i in indices.flatten():
        final_matches.append((tuple(rects[i]), scores[i]))
    
    return final_matches

def detect_matches_with_sift(
    large_img: np.ndarray, 
    small_img: np.ndarray, 
    min_match_count: int = 10,
    ratio_threshold: float = 0.7
):
    """
    使用SIFT特征匹配检测大图像中小图像的出现次数
    
    参数:
        large_img: 大图像 (BGR格式)
        small_img: 小图像 (BGR格式)
        min_match_count: 最小匹配点数，用于确认有效匹配
        ratio_threshold: Lowe's比率测试的阈值
        
    返回:
        (num_matches, matches_info)
        num_matches: 检测到的匹配组数
        matches_info: 每个匹配的边界框(x, y, w, h)和匹配关键点数
    """
    # 转换为灰度图
    gray_large = cv2.cvtColor(large_img, cv2.COLOR_BGR2GRAY)
    gray_small = cv2.cvtColor(small_img, cv2.COLOR_BGR2GRAY)
    
    # 初始化SIFT检测器
    sift = cv2.SIFT_create()
    
    # 检测关键点并计算描述符
    kp_large, des_large = sift.detectAndCompute(gray_large, None)
    kp_small, des_small = sift.detectAndCompute(gray_small, None)
    
    #print(len(des_small))
    #print(len(des_large))
    
    # 如果小图像没有足够关键点，直接返回
    if des_small is None or len(des_small) < 2:
        return 0, []
    
    # 创建匹配器
    matcher = cv2.BFMatcher()
    raw_matches = matcher.knnMatch(des_small, des_large, k=2)
    
    # 应用Lowe's比率测试
    good_matches = []
    for m, n in raw_matches:
        if m.distance < ratio_threshold * n.distance:
            good_matches.append(m)
    
    print(len(good_matches))
    
    # 如果没有足够匹配点直接返回
    if len(good_matches) < min_match_count:
        return 0, []
    
    # 将匹配点分组
    img_pts = np.float32([kp_small[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    scene_pts = np.float32([kp_large[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    
    # 使用DBSCAN聚类匹配点
    from sklearn.cluster import DBSCAN
    clustering = DBSCAN(eps=50, min_samples=min_match_count).fit(scene_pts[:, 0, :])
    
    # 统计聚类结果
    clusters = {}
    for idx, label in enumerate(clustering.labels_):
        if label == -1:  # 忽略噪声点
            continue
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(good_matches[idx])
    
    # 对每个匹配组计算单应性矩阵和边界框
    matches_info = []
    h_small, w_small = small_img.shape[:2]
    
    for cluster_id, cluster_matches in clusters.items():
        if len(cluster_matches) < min_match_count:
            continue
            
        # 获取匹配点的位置
        src_pts = np.float32([kp_small[m.queryIdx].pt for m in cluster_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp_large[m.trainIdx].pt for m in cluster_matches]).reshape(-1, 1, 2)
        
        # 计算单应性矩阵
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        
        if H is None:
            continue
            
        # 计算小图像在目标图像中的位置
        pts = np.float32([[0, 0], [0, h_small-1], 
                          [w_small-1, h_small-1], [w_small-1, 0]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, H)
        
        # 计算边界框
        min_x = max(0, int(min(dst[:, 0, 0])))
        min_y = max(0, int(min(dst[:, 0, 1])))
        max_x = min(large_img.shape[1], int(max(dst[:, 0, 0])))
        max_y = min(large_img.shape[0], int(max(dst[:, 0, 1])))
        
        width = max_x - min_x
        height = max_y - min_y
        
        # 排除大小不合理的匹配
        if width < 5 or height < 5 or width > large_img.shape[1]*0.5 or height > large_img.shape[0]*0.5:
            continue
        
        matches_info.append(((min_x, min_y, width, height), len(cluster_matches)))
    
    return matches_info

def match_template_with_sift(query_img, template_img, min_match_count=10, ransac_threshold=5.0, lowe_ratio=0.7, confidence_threshold=0.5):
    """
    使用SIFT特征匹配和空间一致性验证来检测查询图像中是否包含模板图像
    
    参数:
        template_path: 模板图像路径（您提供的"普攻"图片）
        query_path: 待检测的查询图像路径（实时截图）
        min_match_count: 最小匹配点数量阈值
        ransac_threshold: RANSAC算法的重投影误差阈值
        lowe_ratio: Lowe's比率测试的阈值
        confidence_threshold: 内点比率的置信度阈值
        
    返回:
        dict: 包含匹配结果、置信度和可视化数据的字典
    """
    
    gray_large = cv2.cvtColor(query_img, cv2.COLOR_BGR2GRAY)
    gray_small = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)

    if gray_small is None or gray_large is None:
        return {"success": False, "error": "无法读取图像文件"}
    
    # 初始化SIFT检测器
    sift = cv2.SIFT_create()
    
    # 寻找关键点和描述符
    kp1, des1 = sift.detectAndCompute(gray_small, None)
    kp2, des2 = sift.detectAndCompute(gray_large, None)

    # 检查是否找到足够的关键点
    if des1 is None or des2 is None:
        return {"success": False, "error": "未检测到足够特征点"}
    
    # 使用FLANN匹配器
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    
    # 进行KNN匹配
    matches = flann.knnMatch(des1, des2, k=2)
    
    # 应用Lowe's Ratio Test进行初步筛选
    good_matches = []
    for m, n in matches:
        if m.distance < lowe_ratio * n.distance:
            good_matches.append(m)
    
    # 初步匹配结果
    result = {
        "success": False,
        "initial_matches": len(good_matches),
        "inlier_matches": 0,
        "inlier_ratio": 0.0,
        "homography_matrix": None,
        "bounding_box": None
    }
    
    # 检查是否有足够匹配点进行空间验证
    if len(good_matches) < min_match_count:
        result["error"] = f"匹配点不足: {len(good_matches)} < {min_match_count}"
        return result
    
    # 获取匹配点的坐标
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    
    # 使用RANSAC算法计算单应性矩阵，并进行空间一致性验证
    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, ransac_threshold)
    matches_mask = mask.ravel().tolist()
    print(np.sum(matches_mask))

    # 提取内点匹配
    inlier_matches = [m for i, m in enumerate(good_matches) if matches_mask[i] == 1]
    inlier_ratio = len(inlier_matches) / len(good_matches)
    
    # 更新结果
    result["inlier_matches"] = len(inlier_matches)
    result["inlier_ratio"] = inlier_ratio
    result["homography_matrix"] = M
    
    return inlier_ratio > confidence_threshold

def are_shapes_matching(img1, img2, threshold=1):
    """
    使用Hu矩判断两张图片中的图形形状是否匹配
    
    参数:
    img1, img2: 输入图像（文件路径或numpy数组）
    threshold: 相似度阈值（默认0.2，值越小匹配要求越严格）
    
    返回:
    bool: 形状是否匹配
    float: 实际相似度得分
    """
    
    # 转换为灰度图
    #gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    #gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # 二值化处理
    #_, thresh1 = cv2.threshold(gray1, 127, 255, cv2.THRESH_BINARY)
    #_, thresh2 = cv2.threshold(gray2, 127, 255, cv2.THRESH_BINARY)
    
    # 查找轮廓
    contours1, _ = cv2.findContours(img1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours2, _ = cv2.findContours(img2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 检查是否找到轮廓
    if not contours1 or not contours2:
        raise ValueError("一张或两张图片中未检测到轮廓")
    
    # 获取面积最大的轮廓（假设这是主要图形）
    cnt1 = max(contours1, key=cv2.contourArea)
    cnt2 = max(contours2, key=cv2.contourArea)
    
    # 计算Hu矩相似度（值越小表示越相似）
    similarity = cv2.matchShapes(cnt1, cnt2, cv2.CONTOURS_MATCH_I2, 0.0)
    
    # 根据阈值判断是否匹配
    return similarity < threshold, similarity

def non_max_suppression(boxes, overlap_thresh):
    """
    应用非极大值抑制（NMS）来合并重叠的匹配框。
    
    参数:
        boxes (list): 匹配框列表，每个框为(x1, y1, x2, y2, score)。
        overlap_thresh (float): 重叠阈值，高于此值的框将被合并。
    
    返回:
        list: 抑制后的框列表。
    """
    if len(boxes) == 0:
        return []
    boxes = np.array(boxes)
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    scores = boxes[:, 4]
    
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(scores)
    pick = []
    while len(idxs) > 0:
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)
        suppress = [last]
        for pos in range(0, last):
            j = idxs[pos]
            xx1 = max(x1[i], x1[j])
            yy1 = max(y1[i], y1[j])
            xx2 = min(x2[i], x2[j])
            yy2 = min(y2[i], y2[j])
            w = max(0, xx2 - xx1 + 1)
            h = max(0, yy2 - yy1 + 1)
            overlap = (w * h) / areas[j]
            if overlap > overlap_thresh:
                suppress.append(pos)
        idxs = np.delete(idxs, suppress)
    return boxes[pick]

def count_template_matches(template, source, threshold=0.7, scales=np.arange(0.5, 1.5, 0.1)):
    """
    使用多尺度模板匹配统计源图像中模板图像符号的数量。
    
    参数:
        template_path (str): 模板图像的路径（第一张图片）。
        source_path (str): 源图像的路径（第二张图片）。
        threshold (float): 匹配阈值，默认0.7，高于此值视为匹配。
        scales (ndarray): 缩放比例范围，默认从0.5到2.0，步长0.1。
    
    返回:
        int: 匹配到的模板数量。
    """
    
    # 转换为灰度图像
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    source_gray = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
    
    # 二值化处理
    _, template_gray = cv2.threshold(template_gray, 127, 255, cv2.THRESH_BINARY)
    _, source_gray = cv2.threshold(source_gray, 127, 255, cv2.THRESH_BINARY)
    
    # 获取模板尺寸
    t_h, t_w = template_gray.shape
    found = []  # 存储匹配框和得分
    
    # 多尺度匹配
    for scale in scales:
        width = int(t_w * scale)
        height = int(t_h * scale)
        # 跳过缩放后模板比源图大的情况
        if height > source_gray.shape[0] or width > source_gray.shape[1]:
            continue
        # 缩放模板
        resized_template = cv2.resize(template_gray, (width, height), interpolation=cv2.INTER_CUBIC)
        # 执行模板匹配
        result = cv2.matchTemplate(source_gray, resized_template, cv2.TM_CCOEFF_NORMED)
        # 找到匹配位置
        loc = np.where(result >= threshold)
        for pt in zip(*loc[::-1]):  # 切换坐标顺序
            # 存储匹配框的左上角和右下角坐标及得分
            found.append((pt[0], pt[1], pt[0] + width, pt[1] + height, result[pt[1], pt[0]]))
    
    # 应用非极大值抑制
    if len(found) > 0:
        found = non_max_suppression(found, overlap_thresh=0.3)
    return found