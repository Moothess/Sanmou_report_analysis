# SBAT_v0.3 — 战报自动分析工具

适用于游戏《三国：谋定天下》的战报截图采集与自动化分析工具。

---

## 功能概览

1. **战报采集**：自动识别游戏窗口，截取战报详情页各回合截图，并拼接为完整战报长图。
2. **战报解析**：提取武将基础信息（国籍、兵种、星级、等级、技能等），使用 OCR 识别战报文本，还原每回合的行动事件序列。
3. **战报分析**：对解析结果进行结构化统计分析，输出兵力变化、技能触发等关键数据。

---

## 使用方法

### 完整流程（采集 + 分析）

运行 `report_collection.py`，它会依次完成截图采集和战报分析：

```bash
python report_collection.py
```

1. 程序启动后，在游戏内打开目标战报详情页。
2. 按 `S` 键开始自动截图采集。
3. 采集完成后程序自动进行图像拼接，并调用分析流程。
4. 按 `Q` 键退出。

> `stage1 = True` 表示重新截图；改为 `False` 则跳过截图，仅对已有截图重新拼接。

### 仅分析（不重新截图）

直接运行 `report_analysis.py`，对 `data/` 目录下最新的战报数据执行分析：

```bash
python report_analysis.py
```

> `stage1 = True` 表示重新执行元信息提取和图像解析；改为 `False` 则从已保存的 `meta_info.json` / `sentence.pkl` 中读取缓存，直接进行分析。

---

## 内部流程说明

### `report_collection.py`（第一阶段）

| 步骤 | 说明 |
|------|------|
| `get_resolution()` | 获取游戏窗口的位置与分辨率 |
| `get_battle_images()` | 自动翻页截取各回合战报图像 |
| `stitch_images()` | 将截图拼接为完整长图，保存至 `data/<id>/` |

### `report_analysis.py`（第二阶段）

| 步骤 | 说明 |
|------|------|
| `extract_meta_info()` | 识别武将名称、国籍、兵种、星级、技能等元数据，保存为 `meta_info.json` |
| `image_to_report()` | OCR 解析战报长图，提取每轮行动文本，保存为 `sentence.pkl` |
| `analysis()` | 对战报文本进行结构化分析，输出统计结果 |

---

## 数据目录结构

```
data/
└── <report_id>/
    ├── meta_info.json       # 武将与技能元数据
    ├── sentence.pkl         # OCR 解析后的战报文本序列（缓存）
    ├── hero_detail/         # 武将详情截图
    └── images_to_stitch/    # 各回合原始截图
```


## 注意事项

- 运行前请确保游戏已在前台运行，窗口标题为 `三国：谋定天下`。
- 若 OCR 识别效果不佳，可检查 `images/digit_dict.txt` 和 `images/troop_type/` 中的模板图片是否完整。
- 战报数据按自增 ID 存储于 `data/` 目录，每次新采集会自动创建新子目录。
