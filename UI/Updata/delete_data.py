# -*- coding: utf-8 -*-
# C:\boatrace\Inport\delete_data.py
from __future__ import annotations
from datetime   import datetime, timedelta, timezone
from pathlib    import Path
import argparse, sqlite3

DB_PATH = Path(r"C:\boatrace\boatrace.db")
JST     = timezone(timedelta(hours=9))
# ------------------
def jst_today_str() -> str:
    return datetime.now(JST).date().strftime("%Y-%m-%d")
# ------------------
def jst_yesterday_str() -> str:
    return (datetime.now(JST).date() - timedelta(days=1)).strftime("%Y-%m-%d")
# ------------------
def parse_args():

    p = argparse.ArgumentParser(description="K B インポートデータ削除")
    p.add_argument("--enable_K", action="store_true", help="enable delete K")
    p.add_argument("--enable_B", action="store_true", help="enable delete B")
    p.add_argument("--date_from",              help="(YYYY-MM-DD)")
    p.add_argument("--date_to",                help="(YYYY-MM-DD)")

    return p.parse_args()
#---------------------------------------------------------------------
def main():

    args     = parse_args()
    date_f   = args.date_from or jst_today_str()
    date_t   = args.date_to   or jst_today_str()
    enable_K = args.enable_K
    enable_B = args.enable_B
    target = ("K" if enable_K else "") + (" B" if enable_B else "")

    print(f"[INFO] Target {target} : {date_f} ～ {date_t}")

    with sqlite3.connect(DB_PATH, timeout=60) as con:
        con.execute("PRAGMA foreign_keys=ON;")
        cur = con.cursor()
        cnt_entr, cnt_race, cnt_prog, del1, del2, del3 = 0, 0, 0, 0, 0, 0

        if enable_K:
            (cnt_entr,) = cur.execute(""" SELECT COUNT(1) FROM Race_entries WHERE date
                                          BETWEEN ? AND ? """, (date_f, date_t,)).fetchone()
            (cnt_race,) = cur.execute(""" SELECT COUNT(1) FROM Races WHERE date
                                          BETWEEN ? AND ? """, (date_f, date_t,)).fetchone()
        if enable_B:
            (cnt_prog,) = cur.execute(""" SELECT COUNT(1) FROM Race_programs WHERE date
                                          BETWEEN ? AND ? """, (date_f, date_t,)).fetchone()

        print( f"[INFO] Counts  Race_entries={cnt_entr:,}  "
               f"Races={cnt_race:,}  Race_programs={cnt_prog:,}" )

        try:
            cur.execute("BEGIN;")
            if enable_K:
                del1 = cur.execute( """DELETE FROM Race_entries WHERE date
                                       BETWEEN ? AND ? """, (date_f, date_t)).rowcount
                del2 = cur.execute( """DELETE FROM Races        WHERE date
                                       BETWEEN ? AND ? """, (date_f, date_t)).rowcount
            if enable_B:
                del3 = cur.execute( """DELETE FROM Race_programs WHERE date
                                       BETWEEN ? AND ? """, (date_f, date_t)).rowcount

            con.commit()

            print( f"[DONE] Deleted  Race_entries={del1:,}  "
                   f"Races={del2:,}  Race_programs={del3:,}"  )

        except Exception as e:
            con.rollback()
            print(f"[ERR] Rollback: {e}")
            return 1

    return 0
#---------------------------------------------------------------------
if __name__ == "__main__":
    raise SystemExit(main())
