# -*- coding: utf-8 -*-

import time, sys, subprocess, argparse
from datetime import datetime as dt, timedelta

TARGET_SCRIPT = r"C:\boatrace\UI\Subprocess\import_Display_run.py"

INTERVAL_SEC = 60 
#---------------------------------------
def parse_args():

    p = argparse.ArgumentParser(description="ETL for import_Display_run.py")
    p.add_argument("--date",      default=None,         help="対象日(yyyy)")
    p.add_argument("--date_from",                       help="期間開始(YYYY-MM-DD)")
    p.add_argument("--date_to",                         help="期間終了(YYYY-MM-DD)")
    p.add_argument("--overwrite", action="store_true",default=False,  help="上書きﾓｰﾄﾞ")

    return p.parse_args()
#---------------------------------------
def main():

    args  = parse_args()

    if args.date and (args.date_from or args.date_to):
        print("date / (date_from , date_to) 両方の指定はできません")
        raise SystemExit(2)
    if (args.date_from and not args.date_to) or (args.date_to and not args.date_from):
        print("(--date_from , --date_to) を併せて指定してください")
        raise SystemExit(2)
    if args.date:
        start_date = dt.strptime(args.date, "%Y-%m-%d")
        end_date   = dt.strptime(args.date, "%Y-%m-%d")
    elif args.date_from and args.date_to:
        start_date = dt.strptime(args.date_from, "%Y-%m-%d")
        end_date   = dt.strptime(args.date_to, "%Y-%m-%d")

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")

        print(f"\n{'='*50}")
        print(f"実行開始: {date_str}")
        print(f"{'='*50}")

        cmd = [ sys.executable, TARGET_SCRIPT, 
                "--date", date_str, 
                "--ALL_venue", 
                "--ALL_race"                   ]

        try:
            result = subprocess.run(cmd, check=False)

            if result.returncode == 0:
                print(f"\n[SUCCESS] {date_str} の処理が正常に完了しました。")
            else:
                print(f"\n[WARN] {date_str} は戻り値 {result.returncode} で終了しました。")

        except Exception as e:
            print(f"\n[ERROR] サブプロセスの実行中に予期せぬエラーが発生しました: {e}")

        if current_date < end_date:
            print(f"\n次の実行まで {INTERVAL_SEC} 秒待機します...")
            time.sleep(INTERVAL_SEC)

        current_date += timedelta(days=1)

    print(f"\n{'='*50}")
    print("全期間の処理が終了しました。")
    print(f"{'='*50}")
#---------------------------------------
if __name__ == "__main__":
    sys.exit(main())
