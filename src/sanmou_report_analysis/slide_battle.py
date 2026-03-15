# Author: Mian Qin
# Date Created: 2024/10/27
from pathlib import Path

import keyboard

from sanmou_report_analysis.utils.process_info import get_resolution
from sanmou_report_analysis.utils.slide_report import slide_battle_images


def collect_report():
    root_dir = Path("./battle")
    idx_list = [int(path.name) for path in root_dir.iterdir()]
    current_idx = max(idx_list) + 1 if idx_list else 0
    save_dir = root_dir / str(current_idx)
    print("按s开始。按q退出。")
    stop = True
    while stop:
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            if event.name == "s":
                position_info = get_resolution()
                slide_battle_images(save_dir, position_info, max_n=1)

                current_idx += 1
                stop = False
                print("收集完成，退出程序。")
                # winsound.Beep(300, 1000)
            if event.name == "q":
                break
    keyboard.unhook_all()


def main():
    collect_report()


if __name__ == "__main__":
    main()
