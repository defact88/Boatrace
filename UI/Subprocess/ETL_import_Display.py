# -*- coding: utf-8 -*-

import time, sys, subprocess, argparse
from datetime          import datetime as dt, timedelta
from check_display_run import check_display_data
import import_Display_run

INTERVAL_SEC  = 5

#---------------------------------------------------------------------
def ETL_run(date_from:str, date_to:str, overwrite:bool=False):

    current_date = date_from
    while current_date <= date_to:
        date_str = current_date.strftime("%Y-%m-%d")

        print(f"\n{'='*50}")
        print(f"実行開始: {date_str}")
        print(f"{'='*50}")

        if not overwrite:
            has_missing = check_display_data(date_str, date_str, quiet_mode=True)
            if not has_missing:
                print(f"[SKIP] {date_str} のデータは完備されています。")
                if current_date < date_to:
                    print(f"\n次の実行まで {INTERVAL_SEC} 秒待機します...")
                    time.sleep(INTERVAL_SEC)
                current_date += timedelta(days=1)
                continue

        args_list = ["--date", date_str, "--ALL_venue", "--ALL_race"]
        
        try:
            result_code = import_Display_run.main(args_list)

            if result_code == 0:
                print(f"\n[SUCCESS] {date_str} の処理が正常に完了しました。")
            else:
                print(f"\n[WARN] {date_str} は戻り値 {result_code} で終了しました。")

        except Exception as e:
            print(f"\n[ERROR] 実行中に予期せぬエラーが発生しました: {e}")

        if current_date < date_to:
            print(f"\n次の実行まで {INTERVAL_SEC} 秒待機します...")
            time.sleep(INTERVAL_SEC)

        current_date += timedelta(days=1)

    print(f"\n{'='*50}")
    print("全期間の処理が終了しました。")
    print(f"{'='*50}")

#---------------------------------------
def parse_args(argv=None):

    p = argparse.ArgumentParser(description="ETL for import_Display_run.py")
    p.add_argument("--date",      default=None,         help="対象日(yyyy)")
    p.add_argument("--date_from",                       help="期間開始(YYYY-MM-DD)")
    p.add_argument("--date_to",                         help="期間終了(YYYY-MM-DD)")
    p.add_argument("--overwrite", action="store_true",  help="上書きﾓｰﾄﾞ")

    return p.parse_args(argv)

#---------------------------------------
def main(argv=None):

    args  = parse_args(argv)

    if args.date and (args.date_from or args.date_to):
        print("date / (date_from , date_to) 両方の指定はできません")
        raise SystemExit(2)
    if (args.date_from and not args.date_to) or (args.date_to and not args.date_from):
        print("(--date_from , --date_to) を併せて指定してください")
        raise SystemExit(2)

    d_from = None
    d_to   = None
    if args.date:
        d_from = dt.strptime(args.date,      "%Y-%m-%d")
        d_to   = dt.strptime(args.date,      "%Y-%m-%d")
    elif args.date_from and args.date_to:
        d_from = dt.strptime(args.date_from, "%Y-%m-%d")
        d_to   = dt.strptime(args.date_to,   "%Y-%m-%d")

    ETL_run(d_from, d_to, args.overwrite)

#---------------------------------------
if __name__ == "__main__":
    raise SystemExit(main())
