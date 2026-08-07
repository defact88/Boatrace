# -*- coding: utf-8 -*-
# C:\boatrace\Import\daily_insert.py

from __future__ import annotations
from pathlib    import Path
from datetime   import datetime as dt, date, timedelta
import argparse, sqlite3, subprocess, sys, os
from update_FLstate import update_FLstate

BASE       = Path(r"C:\boatrace")
SUB        = Path(r"C:\boatrace\Import") 
DB_PATH    = BASE / r"boatrace.db"
ETL_PATH   = SUB / r"ETL_k_results.py"
IMPORT_B   = SUB / r"import_B_txt.py"
IMPORT_D   = BASE / r"UI\Subprocess\import_display_run.py"

#-----------------------------
def yesterday(_date:str):

    return (dt.fromisoformat(_date) - timedelta(days=1)).strftime("%Y-%m-%d")
#-----------------------------------------------------------
def ensure_programs(d_iso:str):

    with sqlite3.connect(str(DB_PATH), timeout=60) as con:

        (cnt,) = con.execute("""
                     SELECT COUNT(1)
                       FROM Race_programs
                      WHERE date=?
                     """ ,
                     (d_iso,)              ).fetchone()

    if cnt and cnt > 0:
        print(f"SKIP: already updated B for {d_iso}")
        raise SystemExit(2)

#-----------------------------------------------------------
def run_etl_result(d_f:str, d_t:str, overwrite:bool=False):

    py                = sys.executable or "python"
    if overwrite: cmd = [ py, str(ETL_PATH), "--date_from", d_f, "--date_to", d_t, "--external",
                                                                                  "--overwrite" ]
    else:         cmd = [ py, str(ETL_PATH), "--date_from", d_f, "--date_to", d_t, "--external"]

    try:
        proc = subprocess.run( cmd,
                               cwd     = str(BASE),
                               stdout  = subprocess.DEVNULL,
                               stderr  = subprocess.DEVNULL,
                               stdin   = subprocess.DEVNULL,
                               check   = False,
                               timeout = 600,                )

        print(f"update result {d_f} ～ {d_t} done")
        print(proc.returncode)

    except subprocess.TimeoutExpired:
        print("[TIMEOUT] ETL_k_results.py exceeded 600s\n")

#-----------------------------------------------------------
def run_import_B(d_f:str, d_t:str, overwrite:bool=False):

    py                = sys.executable or "python"
    if overwrite: cmd = [py, str(IMPORT_B), "--date_from", d_f, "--date_to", d_t, "--overwrite"]
    else:         cmd = [py, str(IMPORT_B), "--date_from", d_f, "--date_to", d_t]

    proc = subprocess.run( cmd,
                           cwd    = str(BASE),
                           stdout = subprocess.DEVNULL,
                           stderr = subprocess.DEVNULL,
                           check  = False,              )

    print(f"update programs {d_f} ～ {d_t} done")
    print(proc.returncode)

#-----------------------------------------------------------
def run_import_display(date:str):

    log_path = BASE / r"Archive\logs" / f"import_display_{date}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    py  = sys.executable or "python"
    cmd = [py, str(IMPORT_D), "--date", date, "--ALL_venue", "--ALL_race"]

    log_file = open(log_path, "w", encoding="utf-8")
    proc     = subprocess.Popen( cmd,  cwd = str(BASE),
                                    stdout = log_file,
                                    stderr = log_file   )

    print(f"updating display_run {date} on backgroud")

#-----------------------------------------------------------
def import_grades(d_iso:str, overwrite:bool) -> None:
 # 2種ｸﾞﾚｰﾄﾞ同日同場開催にて不具合有り停止中

    with sqlite3.connect(str(DB_PATH), timeout=60) as con:
        con.execute("PRAGMA foreign_keys=ON;")
        cur = con.cursor()

        if overwrite:
            cur.execute("UPDATE Races SET grade=NULL WHERE date=?;", (d_iso,))

        cur.execute("""
            UPDATE Races AS r
               SET grade =( SELECT rp.grade
                              FROM Race_programs AS rp
                             WHERE rp.date     = r.date
                               AND rp.venue_id = r.venue_id
                               AND rp.race_no  = r.race_no  )
             WHERE r.date = ?
               AND EXISTS( SELECT 1
                             FROM Race_programs AS rp
                            WHERE rp.date     = r.date
                              AND rp.venue_id = r.venue_id
                              AND rp.race_no  = r.race_no  );
            """,
                  (d_iso,))

        con.commit()

#===============================================================================
def parse_args():

    p = argparse.ArgumentParser(description="Daily K updater (single-day).")
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
        d_f, d_t = args.date, args.date

    elif args.date_from and args.date_to:
        d_f, d_t = args.date_from, args.date_to

    else:
        _today   = dt.today().strftime("%Y-%m-%d")
        d_f, d_t = _today, _today

    run_import_B(d_f, d_t, args.overwrite)
    run_etl_result(yesterday(d_f), yesterday(d_t), args.overwrite)
    update_FLstate()

    run_import_display(yesterday(d_f))

    return 0

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main())
