# Author: Mian Qin
# Date Created: 2024/10/27
import sys
from pathlib import Path


def ensure_capture_supported_platform(platform_name: str | None = None) -> None:
    current_platform = platform_name or sys.platform
    if current_platform != "win32":
        raise RuntimeError(
            "report_collection capture workflow currently supports Windows only "
            "(requires win32 APIs). On macOS/Linux, run analysis with: "
            "`uv run python -m sanmou_report_analysis.report_analysis`."
        )


def collect_report(stage1):
    from sanmou_report_analysis.utils.stitch import stitch_images

    root_dir = Path("./data")
    idx_list = [int(path.name) for path in root_dir.iterdir()]
    current_idx = max(idx_list) + 1 if stage1 else max(idx_list)
    save_dir = root_dir / str(current_idx)
    if stage1:
        import keyboard

        from sanmou_report_analysis.utils.collect_battle_image import get_battle_images
        from sanmou_report_analysis.utils.process_info import get_resolution

        print("按s开始。按q退出。")
        stop = True
        while stop:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == "s":
                    position_info = get_resolution()
                    image_list = get_battle_images(save_dir, position_info)
                    stitch_images(image_list, save_dir, repaint=False)

                    current_idx += 1
                    stop = False
                    print("按s开始。按q退出。")
                    # winsound.Beep(300, 1000)
                if event.name == "q":
                    break
        keyboard.unhook_all()
    else:
        stitch_images([], save_dir, repaint=False)


def main():
    # 两个步骤：1.实时截图，2.截图拼接
    # stage1设置是否重新获取截图，为False的话只会拼接已经截好的图
    stage1 = True
    if stage1:
        ensure_capture_supported_platform()
    from sanmou_report_analysis.report_analysis import main_phase2

    collect_report(stage1)
    main_phase2()


if __name__ == "__main__":
    main()
