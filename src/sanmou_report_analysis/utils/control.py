# Author: Mian Qin
# Date Created: 2025/6/28
import random
import time

import numpy as np
from pynput.mouse import Button
from pynput.mouse import Controller as MouseController

# 初始化鼠标控制器
_mouse = MouseController()


def click_ltrb(left: int, top: int, right: int, bottom: int):
    x = np.random.randint(left, right)
    y = np.random.randint(top, bottom)
    _mouse.position = (x, y)
    _mouse.click(Button.left, 1)


def human_like_move(x0, y0, x1, y1, duration=1.0, steps=5):
    # 计算方向向量
    dx = x1 - x0
    dy = y1 - y0
    distance = np.sqrt(dx**2 + dy**2)

    # 单位方向向量
    if distance > 0:
        ux = dx / distance
        uy = dy / distance
    else:
        return  # 起点和终点相同，不移动

    # 垂直向量（顺时针垂直）
    vx = -uy
    vy = ux

    # 随机振幅（最大为距离的1/8）
    amplitude = random.uniform(-distance / 8, distance / 8)

    # 生成路径点
    _mouse.press(Button.left)
    time.sleep(np.random.uniform(0.1, 0.2))
    for i in range(steps + 1):
        t = i / steps  # 0到1的进度

        # 主路径位置
        x = x0 + dx * t
        y = y0 + dy * t

        # 添加正弦波动（从0到π）
        wave = np.sin(t * np.pi) * amplitude

        # 垂直方向偏移
        x += vx * wave
        y += vy * wave

        # 移动鼠标
        _mouse.position = (int(x), int(y))
        if i > 0:
            move_duration = duration / steps
            time.sleep(move_duration)

    time.sleep(np.random.uniform(0.4, 0.5))
    _mouse.release(Button.left)
