# Author: Mian Qin
# Date Created: 2025/6/18
from collections import defaultdict
from typing import Optional, Union
from pathlib import Path
import bisect
import json

from typing import Callable

import cv2
#from logger_config import logger
from enum import auto, Enum, IntEnum, StrEnum, Flag


class Round(IntEnum):
    PREPARE = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    RESULT = 9


class Position(StrEnum):
    FRONT = "前排"
    BACK = "后排"


class SkillType(Enum):
    ACTIVE = auto()
    PASSIVE = auto()
    COMMAND = auto()
    PURSUIT = auto()


class DamageType(Enum):
    兵刃 = auto()
    谋略 = auto()
    传递 = auto()
    逃兵 = auto()


class DamageSourceType(Enum):
    ACTIVE_SKILL = auto()
    PASSIVE_SKILL = auto()
    COMMAND_SKILL = auto()
    PURSUIT_SKILL = auto()
    NORMAL_ATTACK = auto()
    COUNTER_ATTACK = auto()


class Country(StrEnum):
    魏 = "魏"
    蜀 = "蜀"
    吴 = "吴"
    群 = "群"


class Gender(StrEnum):
    MAN = "M"
    WOMAN = "W"


class TroopType(StrEnum):
    盾兵 = "盾兵"
    弓兵 = "弓兵"
    枪兵 = "枪兵"
    骑兵 = "骑兵"

class TextColor(StrEnum):
    ORANGE = "orange"  # 会心奇谋伤害颜色
    BLUE = "blue"  # 我方团队颜色
    RED = "red"  # 敌方团队颜色
    MAROON = "maroon"  # 伤害颜色
    GREEN = "green"  # 治疗
    WHITE = "white"  # 文字
    YELLOW = "yellow"  # 属性变化
    OTHER = "purple"  # 其他颜色
    ICON = "icon"  # 图标颜色

class BoundingBox:
    __slots__ = ("l", "t", "r", "b")

    def __init__(self, ltrb):
        l, t, r, b = ltrb
        self.l = int(l)
        self.t = int(t)
        self.r = int(r)
        self.b = int(b)

    def __repr__(self):
        return f"BoundingBox(l={self.l}, t={self.t}, r={self.r}, b={self.b}, height={self.height}, width={self.width})"

    @property
    def height(self):
        return self.b - self.t

    @property
    def width(self):
        return self.r - self.l

    @property
    def area(self):
        return self.height * self.width

    @property
    def center(self):
        return (self.t + self.b) // 2, (self.l + self.r) // 2

    def copy(self):
        return BoundingBox(self.to_ltrb())

    def to_slice(self):
        return slice(self.t, self.b), slice(self.l, self.r)

    def to_ltrb(self) -> tuple[int, int, int, int]:
        return self.l, self.t, self.r, self.b

    def move(self, dt=0, dl=0):
        dl = int(dl)
        dt = int(dt)
        self.l += dl
        self.r += dl
        self.t += dt
        self.b += dt

    def expand(self, dt=0, dl=0):
        dl = int(dl)
        dt = int(dt)
        self.l = max(0, self.l - dl)
        self.r = self.r + dl
        self.t = max(0, self.t - dt)
        self.b = self.b + dt

    def merge(self, other: "BoundingBox"):
        return BoundingBox((
            min(self.l, other.l),
            min(self.t, other.t),
            max(self.r, other.r),
            max(self.b, other.b),
        ))

    def vertical_gap_box(self, other: "BoundingBox", expand: int = 0) -> Union["BoundingBox", None]:
        """
        垂直方向的间距框
        """
        if self.b >= other.t:
            return None

        return BoundingBox((
            min(self.l, other.l),
            max(self.b - expand, self.t),
            max(self.r, other.r),
            min(other.t + expand, other.b),
        ))

    def horizontal_gap_box(self, other: "BoundingBox", expand: int = 0) -> Optional["BoundingBox"]:
        """
        水平方向的间距框
        """
        if self.r >= other.l:
            return None

        return BoundingBox((
            max(self.r - expand, self.l),
            min(self.t, other.t),
            min(other.l + expand, other.r),
            max(self.b, other.b),
        ))

    def intersection_area(self, other):
        """计算两个边界框的交集面积"""
        # 计算交集的边界
        inter_l = max(self.l, other.l)
        inter_r = min(self.r, other.r)
        inter_t = max(self.t, other.t)
        inter_b = min(self.b, other.b)

        # 如果没有交集，面积为0
        if inter_r <= inter_l or inter_b <= inter_t:
            return 0

        return (inter_r - inter_l) * (inter_b - inter_t)

    def union_area(self, other: "BoundingBox"):
        """计算两个边界框的并集面积"""
        area_a = self.area
        area_b = other.area
        return area_a + area_b - self.intersection_area(other)

    def iou(self, other: "BoundingBox"):
        """计算交并比IoU"""
        intersection = self.intersection_area(other)
        union = self.union_area(other)

        # 避免除以0的情况
        if union == 0:
            return 0.0

        return intersection / union

    def is_same_row(self, other: "BoundingBox", threshold) -> bool:
        return abs(self.center[0] - other.center[0]) <= threshold

    def is_same_column(self, other: "BoundingBox", threshold) -> bool:
        return abs(self.center[1] - other.center[1]) <= threshold

    def is_overlap(self, other: "BoundingBox") -> bool:
        if self.r <= other.l or other.r <= self.l:
            return False
        if self.b <= other.t or other.b <= self.t:
            return False
        return True


class MatchResult:
    __slots__ = ("box", "score")

    def __init__(self, box: BoundingBox | tuple, score: Optional[float] = None):
        if isinstance(box, tuple):
            box = BoundingBox(box)
        self.box = box
        self.score = score

    def __repr__(self) -> str:
        return f"MatchResult(box={repr(self.box)}, score={self.score})"


class OCRResult:
    __slots__ = ("box", "text")

    def __init__(self, box: Union[BoundingBox, tuple], text):
        if isinstance(box, tuple):
            box = BoundingBox(box)
        self.box = box
        self.text = text

    def __repr__(self) -> str:
        return f"OCRResult(box={repr(self.box)}, text='{self.text}')"

    def merge(self, other: "OCRResult"):
        new_text = self.text + other.text
        new_box = self.box.merge(other.box)
        return OCRResult(new_box, new_text)

    def __add__(self, other):
        return self.merge(other)


class LazyLoadDict(dict):
    """通用懒加载字典，通过 key-path 映射初始化"""

    def __init__(self, key_path_map: dict, loader=cv2.imread):
        super().__init__()
        self._key_path_map = key_path_map
        self._loader = loader  # 默认为 cv2.imread，可自定义加载逻辑

    def __missing__(self, key):
        if key in self._key_path_map:
            # 懒加载：只有访问时才会读取文件
            value = self._loader(self._key_path_map[key])
            self[key] = value  # 存入字典避免重复加载
            return value
        raise KeyError(key)

    def keys(self):
        """返回所有预定义的键（无论是否已加载）"""
        return self._key_path_map.keys()

    def values(self):
        """返回所有值（未加载的值会触发懒加载）"""
        return (self[key] for key in self._key_path_map)

    def items(self):
        """返回所有键值对（未加载的值会触发懒加载）"""
        return ((key, self[key]) for key in self._key_path_map)

    def __contains__(self, key):
        """检查键是否在预定义范围内（无论是否已加载）"""
        return key in self._key_path_map

    def __iter__(self):
        """迭代所有预定义的键（无论是否已加载）"""
        return iter(self._key_path_map)


def create_lazy_dict(key_path_map: dict, loader: Callable = cv2.imread) -> LazyLoadDict:
    """工厂函数：创建懒加载字典"""
    return LazyLoadDict(key_path_map, loader)