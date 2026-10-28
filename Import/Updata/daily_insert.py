# -*- coding: utf-8 -*-
# C:\boatrace\Import\daily_insert.py

from __future__ import annotations
from pathlib    import Path
from datetime   import datetime as dt, date, timedelta, timezone
import argparse, subprocess, sys, json

from update_FLstate import update_FLstate
import ETL_odds_data, ETL_Before_info, ETL_K_results, import_B_txt, get_player_schedule
from queries import Query
import Dal as dal

BASE      = Path(r"C:\boatrace")
LOG_PATH  = Path(r"C:\boatrace\Archive\logs\daily_insert")
BEF_PATH  = Path(r"C:\boatrace\Import\Updata\ETL_Before_info.py")
ODDS_PATH = Path(r"C:\boatrace\Import\Updata\ETL_odds_data.py")
SCH_PATH  = Path(r"C:\boatrace\Import\Updata\get_player_schedule.py")

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
def days_pass(d:str, range:int):

    d = to_date(d)

    return to_str(d +timedelta(days=range))

#-----------------------------------------------------------
def ensure_programs(d:date):

    row = dal.fetch_one("""
              SELECT COUNT(1)
                FROM Race_programs
               WHERE date=?
              """ ,
              (d,) )

    return True if row[0] else False

#-----------------------------------------------------------
def call_K(d_iso:str, background:bool=False):

    if background:
        file_name = f"K_txt_{d_iso}.log"
        log       = LOG_PATH / "K_txt" / file_name
        log.parent.mkdir(parents=True, exist_ok=True)
        log_file = open(log, "w", encoding="utf-8")

        sys.stdout = log_file
        sys.stderr = log_file

    argv = ["--date_from", d_iso, "--date_to", d_iso, "--external", "--overwrite"]

    ETL_K_results.main(argv)

#-----------------------------------------------------------
def call_B(d_iso:str, overwrite:bool=False, background:bool=False):

    if background:
        file_name = f"B_txt_{d_iso}.log"
        log       = LOG_PATH / "B_txt" / file_name
        log.parent.mkdir(parents=True, exist_ok=True)
        log_file  = open(log, "w", encoding="utf-8")

        sys.stdout = log_file
        sys.stderr = log_file

    argv = ["--date", d_iso]

    if overwrite:
        argv.append("--overwrite")

    import_B_txt.main(argv)

#-----------------------------------------------------------
def run_ETL(d_from:str, d_to:str, background:bool):

    argv = ["--date_from", d_from, "--date_to", d_to,]

    if background:

        for prc, _path in (("B_info", BEF_PATH), ("odds", ODDS_PATH)), ("schedule", SCH_PATH):
            if prc == "schedule": argv = ["--regist_player",]

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
                                      cwd= str(BASE),                    )
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
def update_overall(d_iso:str, overwrite:bool=False):

    d_from  = days_ago(d_iso, 270)
    d_to    = d_iso
    data1   = Query( d_from, d_to, q_results=True, exclude_rookie=[True,False]
                      )._pack(by_course=True)
    data2   = Query( d_from, d_to, q_results=True, exclude_rookie=[True,False], exclude_venue=3
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
                    (d_iso, json1, json2) )

        print(f"[{d_iso}] Daily_Overall created.")

    except Exception as e:
        print(str(e))

#===============================================================================
def main():

    p = argparse.ArgumentParser()
    p.add_argument("--date",       type=str,            help="対象日(yyyy)")
    p.add_argument("--date_from",  type=str,            help="開始日(YYYY-MM-DD)")
    p.add_argument("--date_to",    type=str,            help="終了日(YYYY-MM-DD)")
    p.add_argument("--days",       type=int,            help="直近n日間不足日補填")
    p.add_argument("--overwrite",  action="store_true", help="上書きﾓｰﾄﾞ")
    p.add_argument("--background", action="store_true", help="BGモード")
    args  = p.parse_args()

    if args.date and (args.date_from or args.date_to):
        print("date / (date_from , date_to) 両方の指定はできません")
        raise SystemExit(2)
    if (args.date_from and not args.date_to) or (args.date_to and not args.date_from):
        print("(date_from , date_to) を併せて指定してください")
        raise SystemExit(2)

    if args.days:
        date_to   = today_iso()
        date_from = days_ago(date_to, args.days)
    elif args.date:
        date_to   = args.date
        date_from = args.date
    elif args.date_from and args.date_to:
        date_to   = args.date_to
        date_from = args.date_from
    else:
        date_to   = today_iso()
        date_from = today_iso()

    d = date_from
    while d <= date_to:

        if not args.overwrite and ensure_programs(d):
            print(f"[{d}] B_file is already imported")
            call_K(yesterday(d), args.background)
        else:
            call_B(d, args.overwrite, args.background)
            call_K(yesterday(d),      args.background)

        update_overall(d, args.overwrite)

        d = days_pass(d, 1)

    update_FLstate()
    get_player_schedule.get_schedule(all=True)
    run_ETL(yesterday(date_from), yesterday(date_to), args.background)

    sys.exit(0)

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main())
