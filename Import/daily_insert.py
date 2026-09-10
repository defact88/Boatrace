# -*- coding: utf-8 -*-
# C:\boatrace\Import\daily_insert.py

from __future__      import annotations
from pathlib         import Path
from datetime        import datetime as dt, date, timedelta
from update_FLstate  import update_FLstate
import ETL_import_Display
import ETL_K_results
import import_B_txt

import argparse, sqlite3, subprocess, sys, os

BASE     = Path(r"C:\boatrace")
DB_PATH  = BASE / r"boatrace.db"
LOG_PATH = BASE / r"Archive\logs\daily_insert"
IMPORT_D = BASE / r"UI\Subprocess\ETL_import_Display.py"

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
        con.close()
        return True
    else:
        con.close()
        return False

#-----------------------------------------------------------
def call_K(date_iso:str, overwrite:bool=False, background:bool=False):

    if background:
        file_name = f"K_{date_iso}.log"
        log       = LOG_PATH / "K" / file_name
        log.parent.mkdir(parents=True, exist_ok=True)
        log_file = open(log, "w", encoding="utf-8")

        sys.stdout = log_file
        sys.stderr = log_file

    argv = ["--date_from", date_iso, "--date_to", date_iso, "--external"]

    if overwrite:
        argv.append("--overwrite")

    ETL_K_results.main(argv)

#-----------------------------------------------------------
def call_B(date_iso:str, overwrite:bool=False, background:bool=False):

    if background:
        file_name = f"B_{date_iso}.log"
        log       = LOG_PATH / "B" / file_name
        log.parent.mkdir(parents=True, exist_ok=True)
        log_file = open(log, "w", encoding="utf-8")

        sys.stdout = log_file
        sys.stderr = log_file

    argv = ["--date", date_iso]

    if overwrite:
        argv.append("--overwrite")

    import_B_txt.main(argv)

#-----------------------------------------------------------
def run_import_display(date_from:str, date_to:str, background:bool=False):

    if background:
        if date_from == date_to:
            file_name = f"display_{date_from}.log"
            log = LOG_PATH / "D" / file_name
        else:
            file_name = f"display_{date_from}-{date_to}.log"
            log = LOG_PATH / "D" / file_name

        log.parent.mkdir(parents=True, exist_ok=True)

        startupinfo             = subprocess.STARTUPINFO()
        startupinfo.dwFlags    |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0 

        with open(log, "w", encoding="utf-8") as log_file:
            py  = sys.executable
            cmd = [ py, str(IMPORT_D), "--date_from", date_from, "--date_to", date_to,]
            opt = dict( creationflags= subprocess.CREATE_NO_WINDOW,
                               stdout= log_file,
                               stderr= log_file,
                                stdin= subprocess.DEVNULL,
                                  cwd= str(BASE),                                       )
            try:
                proc = subprocess.Popen( cmd, **opt)

            except subprocess.TimeoutExpired:
                proc.terminate()
                proc.wait(timeout=3)
                print("Terminated by stop request")

            except Exception as e:
                print(str(e))

    else:
        ETL_import_Display.main(["--date_from", date_from, "--date_to", date_to])

#===============================================================================
def parse_args():

    p = argparse.ArgumentParser(description="Daily K/B/display_run updater")
    p.add_argument("--date",      default=None,         help="対象日(yyyy)")
    p.add_argument("--date_from",                       help="期間開始(YYYY-MM-DD)")
    p.add_argument("--date_to",                         help="期間終了(YYYY-MM-DD)")
    p.add_argument("--overwrite",  action="store_true", help="上書きﾓｰﾄﾞ")
    p.add_argument("--all",        action="store_true", help="直近10日不足日")
    p.add_argument("--background", action="store_true", help="BGモード")

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

    if args.all:
        d_f = (dt.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        d_t = dt.today().strftime("%Y-%m-%d")
    elif args.date:
        d_f, d_t = args.date, args.date
    elif args.date_from and args.date_to:
        d_f, d_t = args.date_from, args.date_to
    else:
        _today   = dt.today().strftime("%Y-%m-%d")
        d_f, d_t = _today, _today

    _date = d_f
    while _date <= d_t:
        if not args.overwrite and ensure_programs(_date):
            print(f"[{_date}] B_file is already imported")
            call_K(yesterday(_date), args.overwrite, args.background)
        else:
            call_B(_date, args.overwrite, args.background)
            call_K(yesterday(_date), args.overwrite)

        _date = (dt.fromisoformat(_date) + timedelta(days=1)).strftime("%Y-%m-%d")

    update_FLstate()

    run_import_display(yesterday(d_f), yesterday(d_t), args.background)

    sys.exit(0)

#-----------------------------
def yesterday(_date:str):

    return (dt.fromisoformat(_date) - timedelta(days=1)).strftime("%Y-%m-%d")

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main())
