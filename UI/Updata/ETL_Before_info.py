# -*- coding: utf-8 -*-
# C:\boatrace\UI\Updata\ETL_Before_info.py

import time, sys, subprocess, argparse
from datetime          import datetime as dt, timedelta
import get_Before_info
import Dal as dal

INTERVAL_SEC  = 5

#=====================================================================
def check_Before_info_data(date_from, date_to, quiet_mode=False):

    sql = """
        SELECT r.date, 
               r.venue_id, 
               r.race_no,
               r.status,
               COUNT(d.frame_no) as record_count,
               SUM(CASE WHEN(d.is_absent = 0 AND e.fault_code != 'K') 
                         AND( d.exhibition IS NULL OR 
                                d.slit_ADJ IS NULL OR 
                                    d.tilt IS NULL)
                        THEN 1 ELSE 0 END) as missing_val_count

          FROM Races r
    INNER JOIN Race_entries e ON     r.date = e.date 
                             AND r.venue_id = e.venue_id 
                             AND  r.race_no = e.race_no

     LEFT JOIN Before_info d  ON     e.date = d.date 
                             AND e.venue_id = d.venue_id 
                             AND  e.race_no = d.race_no 
                             AND e.frame_no = d.frame_no

         WHERE r.date BETWEEN ? AND ?
      GROUP BY r.date, r.venue_id, r.race_no, r.status
        HAVING (r.status != 'cancelled' AND record_count < 6)
            OR (missing_val_count > 0)
      ORDER BY r.date, r.venue_id, r.race_no;
                """
    try:
        rows = dal.fetch_all(sql, (date_from, date_to))

        if quiet_mode:
            return len(rows) > 0

        if not rows:
            print(f"指定期間 ({date_from} ～ {date_to}) に不備のあるデータは見つかりませんでした。")
            return

        print(f"{'date':<12} | {'v_id':<4} | {'r_no':<4} | {'status':<10} | {'issue'}")
        print("-" * 65)
        
        for r in rows:
            issue = ""
            if r['record_count'] < 6:
                issue = f"Record missing ({r['record_count']}/6)"
            else:
                issue = f"Value missing ({r['missing_val_count']} boats)"
                
            print(f"{r['date']:<12} | {r['venue_id']:<4} | {r['race_no']:<4} | {r['status']:<10} | {issue}")

        print("-" * 65)
        print(f"合計: {len(rows)} 件の不備が見つかりました。")

    except sqlite3.Error as e:
        print(f"[SQL ERR] {e}")
    except Exception as e:
        print(f"[ERR] {e}")

#---------------------------------------------------------------------
def ETL_run(date_from:str, date_to:str, overwrite:bool=False):

    current_date = date_from
    while current_date <= date_to:
        date_str = current_date.strftime("%Y-%m-%d")

        print(f"\n{'='*50}")
        print(f"実行開始: {date_str}")
        print(f"{'='*50}")

        if not overwrite:
            has_missing = check_Before_info_data(date_str, date_str, quiet_mode=True)
            if not has_missing:
                print(f"[SKIP] {date_str} のデータは完備されています。")
                if current_date < date_to:
                    print(f"\n次の実行まで {INTERVAL_SEC} 秒待機します...")
                    time.sleep(INTERVAL_SEC)
                current_date += timedelta(days=1)
                continue

        args_list = ["--date", date_str, "--ALL_venue", "--ALL_race"]
        
        try:
            result_code = get_Before_info.main(args_list)

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
def main(argv=None):

    p = argparse.ArgumentParser()
    p.add_argument("--date",      default=None,         help="対象日(yyyy)")
    p.add_argument("--date_from",                       help="期間開始(YYYY-MM-DD)")
    p.add_argument("--date_to",                         help="期間終了(YYYY-MM-DD)")
    p.add_argument("--overwrite", action="store_true",  help="上書きﾓｰﾄﾞ")
    args = p.parse_args(argv)

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
    sys.exit(main())
