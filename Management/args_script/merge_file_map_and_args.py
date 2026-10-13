# merge_file_map_and_args.py

import pandas as pd
from pathlib import Path

# 入力ファイル
MAP_PATH = Path(r"C:\boatrace\Management_GUI\file_map.csv")
ARGS_PATH = Path(r"C:\boatrace\Management_GUI\args_table.csv")

# 出力ファイル
OUT_PATH = Path(r"C:\boatrace\Management_GUI\file_map_with_args.csv")

def main():
    if not MAP_PATH.exists() or not ARGS_PATH.exists():
        print("[ERROR] 入力ファイルが見つかりません")
        return

    # 読み込み
    df_map = pd.read_csv(MAP_PATH)
    df_args = pd.read_csv(ARGS_PATH)

    # 結合（ファイル名で）
    df = pd.merge(df_map, df_args, how="left", on="ファイル名")

    # 引数がない.pyも残す形式
    df["引数"] = df["引数"].fillna("")

    # ソート（任意）
    df = df_args.merge(df_map, how="left", on="ファイル名")
    df = df[["カテゴリ", "サブカテゴリ", "ファイル名", "実行パス", "引数"]]

    # 出力
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"[OK] 統合ファイルを出力しました: {OUT_PATH}")

if __name__ == "__main__":
    main()
