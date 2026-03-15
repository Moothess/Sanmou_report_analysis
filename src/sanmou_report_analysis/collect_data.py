from pathlib import Path

import pandas as pd


def batch_read_xlsx(folder_path: str) -> dict[str, pd.DataFrame]:
    """
    批量读取指定文件夹下的所有xlsx文件

    Args:
        folder_path: xlsx文件所在的文件夹路径

    Returns:
        字典，键为文件名，值为DataFrame
    """
    data = {}
    folder = Path(folder_path)

    for xlsx_file in folder.glob("*.xlsx"):
        try:
            df = pd.read_excel(xlsx_file)
            data[xlsx_file.stem] = df
            print(f"✓ 已读取: {xlsx_file.name}")
        except Exception as e:
            print(f"✗ 读取失败: {xlsx_file.name} - {e}")

    return data


# 使用示例
if __name__ == "__main__":
    # 指定文件夹路径
    xlsx_folder = "./data/{}/analysis_result.xlsx"  # 修改为你的文件夹路径

    all_data = []
    for num in range(173, 181):
        xlsx_file = xlsx_folder.format(num)

        df = pd.read_excel(xlsx_file, sheet_name="damage")

        print(df.head())
        all_data.append(df)

    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df.to_excel("./combined_analysis_result.xlsx", index=False)
