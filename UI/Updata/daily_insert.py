# -*- coding: utf-8 -*-
# C:\boatrace\Import\daily_insert.py

from __future__ import annotations
from pathlib    import Path
from datetime   import datetime as dt, date, timedelta, timezone
import argparse, subprocess, sys, json

from update_FLstate import update_FLstate
import ETL_odds_data, ETL_Before_info, ETL_K_results, import_B_txt
from queries import Query
import Dal as dal

BASE      = Path(r"C:\boatrace")

LOG_PATH  = Path(r"C:\boatrace\Archive\logs\daily_insert")
BEF_PATH  = Path(r"C:\boatrace\UI\Updata\ETL_Before_info.py")
ODDS_PATH = Path(r"C:\boatrace\UI\Updata\ETL_odds_data.py")

# ===========  共通ヘルパー  ===========
def today_iso() -> str:

    JST = timezone(timedelta(hours=9))
    return dt.now(JST).date().strftime("%Y-%m-%d")

#-------------------
def yesterday(x) -> date:

    if isinstance(x, date): return x -timedelta(days=1)
    if isinstance(x,  str): return to_date(x) -timedelta(days=1)

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

#-----------------------------------------------------------
def ensure_programs(d:date):

    (cnt,) = dal.fetch_one("""
                 SELECT COUNT(1)
                   FROM Race_programs
                  WHERE date=?
                 """ ,
                 (to_str(d),)          )

    if cnt and cnt > 0:
        return True
    else:
        return False

#-----------------------------------------------------------
def call_K(_date:date, overwrite:bool=False, background:bool=False):

    if background:
        file_name = f"K_txt_{to_str(_date)}.log"
        log       = LOG_PATH / "K_txt" / file_name
        log.parent.mkdir(parents=True, exist_ok=True)
        log_file = open(log, "w", encoding="utf-8")

        sys.stdout = log_file
        sys.stderr = log_file

    argv = ["--date_from", to_str(_date), "--date_to", to_str(_date), "--external"]

    if overwrite:
        argv.append("--overwrite")

    ETL_K_results.main(argv)

#-----------------------------------------------------------
def call_B(_date:date, overwrite:bool=False, background:bool=False):

    if background:
        file_name = f"B_txt_{to_str(_date)}.log"
        log       = LOG_PATH / "B_txt" / file_name
        log.parent.mkdir(parents=True, exist_ok=True)
        log_file = open(log, "w", encoding="utf-8")

        sys.stdout = log_file
        sys.stderr = log_file

    argv = ["--date", to_str(_date)]

    if overwrite:
        argv.append("--overwrite")

    import_B_txt.main(argv)

#-----------------------------------------------------------
def run_ETL(date_from:date, date_to:date, background:bool, overwrite:bool):

    d_from = to_str(date_from) ;d_to = to_str(date_to)
 
    argv = ["--date_from", d_from, "--date_to", d_to,]
    if overwrite:
        argv.append("--overwrite")

    if background:

        for prc, _path in (("B_info", BEF_PATH), ("odds", ODDS_PATH)):
            d         = f"{d_from}" if d_from == d_to else f"{d_from} - {d_to}"
            file_name = f"{prc}_{d}.log"
            log       = LOG_PATH / prc / file_name

            log.parent.mkdir(parents=True, exist_ok=True)

            startupinfo             = subprocess.STARTUPINFO()
            startupinfo.dwFlags    |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0 

            with open(log, "w", encoding="utf-8") as log_file:
                cmd = [sys.executable, str(_path),]
                cmd.append(argv)
                opt = dict( creationflags= subprocess.CREATE_NO_WINDOW,
                                   stdout= log_file,
                                   stderr= log_file,
                                    stdin= subprocess.DEVNULL,
                                      cwd= str(BASE),                                       )
                try:
                    proc = subprocess.Popen(cmd, **opt)

                except subprocess.TimeoutExpired:
                    proc.terminate()
                    proc.wait(timeout=3)
                    print("Terminated by stop request")

                except Exception as e:
                    print(str(e))

    else:
        ETL_Before_info.main(argv)
        ETL_odds_data.main(argv)

#-----------------------------------------------------------
def update_overall(_date:date, overwrite:bool=False):

    d_from  = to_str( _date -timedelta(days=int(270)) )
    d_to    = to_str(_date)
    data1   = Query( d_from, d_to, query_results=True, exclude_rookie=[True,False]
                      )._pack(by_course=True)
    data2   = Query( d_from, d_to, query_results=True, exclude_rookie=[True,False], exclude_venue=3
                      )._pack(by_course=True)

    json1 = json.dumps(data1, ensure_ascii=False)
    json2 = json.dumps(data2, ensure_ascii=False)

    sql = "REPLACE" if overwrite else "IGNORE"

    try:
        dal.execute(f"""
                INSERT OR {sql}
                          INTO Daily_Overall (date, all_venue, excld_edo)
                        VALUES (?, ?, ?)
                    """,
                    (to_str(_date), json1, json2) )

        print(f"[{_date}] Daily_Overall created.")

    except Exception as e:
        print(str(e))

#===============================================================================
def main():

    p = argparse.ArgumentParser()
    p.add_argument("--date",       type=date.fromisoformat, help="対象日(yyyy)")
    p.add_argument("--date_from",  type=date.fromisoformat, help="開始日(YYYY-MM-DD)")
    p.add_argument("--date_to",    type=date.fromisoformat, help="終了日(YYYY-MM-DD)")
    p.add_argument("--days",       type=int,                help="直近n日間不足日補填")
    p.add_argument("--overwrite",  action="store_true",     help="上書きﾓｰﾄﾞ")
    p.add_argument("--background", action="store_true",     help="BGモード")
    args  = p.parse_args()

    if args.date and (args.date_from or args.date_to):
        print("date / (date_from , date_to) 両方の指定はできません")
        raise SystemExit(2)
    if (args.date_from and not args.date_to) or (args.date_to and not args.date_from):
        print("(date_from , date_to) を併せて指定してください")
        raise SystemExit(2)

    if args.days:
        date_from = dt.today() -timedelta(days=args.days)
        date_to   = dt.today()
    elif args.date:
        date_from = args.date
        date_to   = args.date
    elif args.date_from and args.date_to:
        date_from = args.date_from
        date_to   = args.date_to
    else:
        date_from = dt.today()
        date_to   = dt.today()

    _date = date_from
    while _date <= date_to:

        if not args.overwrite and ensure_programs(_date):
            print(f"[{_date}] B_file is already imported")
            call_K(yesterday(_date), args.overwrite, args.background)
        else:
            call_B(_date, args.overwrite, args.background)
            call_K(yesterday(_date), args.overwrite)
        update_overall(_date, args.overwrite)

        _date += timedelta(days=1)

    update_FLstate()

    run_ETL(yesterday(date_from), yesterday(date_to), args.background, args.overwrite)

    sys.exit(0)

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main())
