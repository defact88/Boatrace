import os
from datetime import date, timedelta

def check_boatrace_files():
    # 設定項目
    target_dir = r"C:\boatrace\Archive\K"
    start_date = date(2005, 1, 1)
    end_date = date.today() - timedelta(days=1)  # 実行当日の前日
    
    # 除外期間 (東日本大震災の影響による開催中止期間)
    excl_start = date(2011, 3, 15)
    excl_end = date(2011, 3, 31)

    missing_files = []
    expected_days = 0
    found_count = 0

    print(f"検査期間: {start_date} ～ {end_date}")
    print(f"対象フォルダ: {target_dir}")
    print("-" * 40)

    current_date = start_date
    while current_date <= end_date:
        # 除外期間内か判定
        if excl_start <= current_date <= excl_end:
            current_date += timedelta(days=1)
            continue

        expected_days += 1
        
        # ファイル名の生成 (Kyymmdd.TXT)
        # %y は西暦の下2桁
        filename = f"K{current_date.strftime('%y%m%d')}.TXT"
        file_path = os.path.join(target_dir, filename)

        if os.path.exists(file_path):
            found_count += 1
        else:
            missing_files.append(f"{current_date.strftime('%Y/%m/%d')} ({filename})")

        current_date += timedelta(days=1)

    # 結果出力
    print(f"理論上の必要ファイル数: {expected_days}件")
    print(f"実際に存在するファイル数: {found_count}件")
    print(f"不足数: {len(missing_files)}件")
    
    if missing_files:
        print("\n[不足している日付一覧]")
        for missing in missing_files:
            print(missing)
    else:
        print("\n不足しているファイルはありません。")

if __name__ == "__main__":
    check_boatrace_files()