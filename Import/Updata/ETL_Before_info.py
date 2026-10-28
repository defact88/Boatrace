# -*- coding: utf-8 -*-
# C:\boatrace\UI\Updata\ETL_Before_info.py

import time, sys, subprocess, argparse, sqlite3
from datetime import datetime as dt, date, timedelta, timezone

import get_Before_info
import Dal as dal

INTERVAL_SEC  = 5
VENUES = [ "", "桐生", "戸田", "江戸川", "平和島", "多摩川", "浜名湖", "蒲郡", "常滑",
            "津",  "三国", "びわこ", "住之江",  "尼崎",   "鳴門",  "丸亀", "児島",
           "宮島", "徳山",  "下関",   "若松",   "芦屋",   "福岡",  "唐津", "大村", ]
# ===========  共通ヘルパー  ===========
def today_iso() -> str:

    JST = timezone(timedelta(hours=9))

    return dt.now(JST).date().strftime("%Y-%m-%d")

#-------------------
def yesterday(x) -> str:

    if isinstance(x, date): return to_str(x -timedelta(days=1))
    if isinstance(x,  str): return to_str(to_date(x) -timedelta(days=1))

# ------------------
def to_str(x) -> str:

    if isinstance(x,  str): return x
    if isinstance(x, date): return x.strftime("%Y-%m-%d")

    raise ValueError("str conv error")

# ------------------
def to_date(x) -> date:

    if isinstance(x, date): return x
    if isinstance(x,  str): return date.fromisoformat(x)

    raise ValueError("date conv error")

#-----------------------------
def days_ago(d:str, range:int)-> str:

    d = to_date(d)

    return to_str(d -timedelta(days=range))

#-----------------------------
def days_pass(d:str, range:int)-> str:

    d = to_date(d)

    return to_str(d +timedelta(days=range))

#=====================================================================
def check_data(date_from, date_to, venue=None, race=None, quiet_mode=False):

    ph1 = f" AND r.venue_id = {venue} " if venue else ""
    ph2 = f" AND r.race_no  = {race} "  if race  else ""

    sql = f"""
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
           {ph1}
           {ph2}
      GROUP BY r.date, r.venue_id, r.race_no, r.status
        HAVING (r.status != 'cancelled' AND record_count < 6)
            OR (missing_val_count > 0)
      ORDER BY r.date, r.venue_id, r.race_no;
          """

    rows = dal.fetch_all(sql, (date_from, date_to))

    if quiet_mode:
        return rows[0]['missing_val_count'] if rows else 9

    if not rows:
        print(f"data [{date_from} ～ {date_to}] is completed")
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
    print(f"Total: {len(rows)} 件の不備が見つかりました。")

#---------------------------------------------------------------------
def get_data(d, v, r):

    arg_list = ["--date", d, "--venue", str(v), "--race", str(r)]
    try:
        rc = get_Before_info.main(arg_list)
        if rc == 0:
            print(f"\n[SUCCESS] {d}")
        else:
            print(f"\n[WARN] {d} return code {rc}")
    except Exception as e:
        print(f"\n[ERROR] {e}")

#---------------------------------------------------------------------
def ETL_run(date_f:str, date_t:str, venue:int, race:int, overwrite:bool=False):

    curr_date = date_f
    while curr_date <= date_t:

        print(f"\n{'='*50}\n {curr_date}\n{'='*50}")

        if not venue:
            for v in range(1,25):
                for r in range(1,13):
                    if not overwrite:
                        cd = check_data(curr_date, curr_date, v, r,  quiet_mode=True)
                        if cd == 9:
                            continue 
                        if cd == 0: 
                            print(f"[SKIP] data [{curr_date} {VENUES[v]} {r}R] was inserted")
                            continue
                    get_data(curr_date, v, r)
                    time.sleep(2)
        else:
            if not race:
                for r in range(1,13):
                    if not overwrite:
                        cd = check_data(curr_date, curr_date, v, r,  quiet_mode=True)
                        if cd == 9:
                            continue 
                        if cd == 0: 
                            print(f"[SKIP] data [{curr_date} {VENUES[v]} {r}R] was inserted")
                            continue
                    get_data(curr_date, venue, r)
                    time.sleep(2)
            else:
                get_data(curr_date, venue, race)

        if curr_date < date_t:
            print(f"\n wait {INTERVAL_SEC} sec...")
            time.sleep(INTERVAL_SEC)
        curr_date = days_pass(curr_date, 1)

#---------------------------------------
def main(argv=None):

    p = argparse.ArgumentParser()
    p.add_argument("--date",         help="対象日(YYYY-MM-DD)")
    p.add_argument("--date_from",    help="期間開始(YYYY-MM-DD)")
    p.add_argument("--date_to",      help="期間終了(YYYY-MM-DD)")
    p.add_argument("--venue",       type=int)
    p.add_argument("--race",        type=int)
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--check",     action="store_true")
    args = p.parse_args(argv)

    if args.date and (args.date_from or args.date_to):
        print("select [date] or [date_from, date_to]")
        raise SystemExit(2)

    if (args.date_from and not args.date_to) or (args.date_to and not args.date_from):
        print("select both [date_from] and [date_to]")
        raise SystemExit(2)

    if args.date:
        date_f, date_t = args.date, args.date
    elif args.date_from and args.date_to:
        date_f, date_t = args.date_from, args.date_to
    else:
        date_f, date_t = today_iso(), today_iso()

    if args.check:
        check_data(date_f, date_t)
        raise SystemExit(0)
    else:
        ETL_run(date_f, date_t, args.venue, args.race, args.overwrite)

#---------------------------------------
if __name__ == "__main__":
    sys.exit(main())
