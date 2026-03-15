# Authors: Mian Qin, Huajun Zhou
# Date Created: 2025/10/23

import json
import pickle
from pathlib import Path

from sanmou_report_analysis.utils.analyze import analysis
from sanmou_report_analysis.utils.meta_info import extract_meta_info
from sanmou_report_analysis.utils.report_detail import image_to_report


def get_report_id():
    _root_dir = Path("./data")
    battle_report_dir_list = list(_root_dir.iterdir())
    battle_report_dir_list.sort(key=lambda x: int(x.stem))
    battle_report_dir = battle_report_dir_list[-1]
    return battle_report_dir


def get_saved_battle_info(report_id):
    int(report_id.stem)
    battle_info_save_path = report_id / "meta_info.json"
    line_layout_save_path = report_id / "sentence.pkl"

    with open(battle_info_save_path, encoding="utf-8") as f:
        battle_info = json.load(f)

    with open(line_layout_save_path, "rb") as f:
        battle_detail = pickle.load(f)

    return battle_info, battle_detail


def main_phase2():
    # 三个步骤：1. 提取武将和技能信息，2. 解析战报图像，3. 分析战报文本
    stage1 = True
    report_id = get_report_id()
    print(f"Processing report from: {report_id}")
    if stage1:
        battle_info = extract_meta_info(report_id)
        battle_detail = image_to_report(report_id, battle_info)
    else:
        battle_info, battle_detail = get_saved_battle_info(report_id)
    analysis(report_id, battle_info, battle_detail)


if __name__ == "__main__":
    main_phase2()
