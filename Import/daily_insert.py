# -*- coding: utf-8 -*-
# C:\boatrace\Import\daily_insert.py

from __future__      import annotations
from pathlib         import Path
from datetime        import datetime as dt, date, timedelta
from update_FLstate  import update_FLstate
from sub.ETL_Display import ETL_import_display_run
import argparse, sqlite3, subprocess, sys, os

BASE       = Path(r"C:\boatrace")
SUB        = Path(r"C:\boatrace\Import") 
DB_PATH    = BASE / r"boatrace.db"
ETL_PATH   = SUB / r"ETL_k_results.py"
LOG_PATH   = BASE / r"Archive\logs\daily_insert"
IMPORT_B   = SUB / r"import_B_txt.py"
IMPORT_D   = BASE / r"UI\Subprocess\ETL_import_Display.py"

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
def run_subprocess( date_iso:str, B:bool=False, K:bool=False,
                    overwrite:bool=False, background:bool=False ):
    if background:
        file_name = f"B_{date_iso}.log" if B else f"K_{date_iso}.log"
        log = LOG_PATH / "B" if B else LOG_PATH / "K"
        log = log / file_name
        log.parent.mkdir(parents=True, exist_ok=True)
        log_file = open(log, "w", encoding="utf-8")

    py  = sys.executable or "python"
    if K:
        cmd = [ py, str(ETL_PATH), "--date_from", date_iso, "--date_to", date_iso,]
        if background:
            cmd.append("--external")
    elif B:
        cmd = [ py, str(IMPORT_B), "--date", date_iso]
    if overwrite: cmd.append("--overwrite")

    opt = dict( cwd     = str(BASE),
                check   = True,
                timeout = 300,         )

    if background:
        opt.update( creationflags = 0x08000000,
                    stdout        = log_file,
                    stderr        = log_file,
                    stdin         = subprocess.DEVNULL,
                    text          = True,               )
    try:
        proc = subprocess.run(cmd, **opt)
        return proc.returncode
        SystemExit(2)

    except subprocess.TimeoutExpired:
        if not background:
            p = "ETL_k_results.py" if K else "import_B_txt.py"
            print(f"[TIMEOUT] {p} exceeded\n")
        else: pass
    except Exception as e:
        print(str(e))

#-----------------------------------------------------------
def run_import_display(date_frm:str, date_to:str, background:bool=False):

    if background:
        if date_frm == date_to:
            file_name = f"display_{date_frm}.log"
            log = LOG_PATH / "D" / file_name
        else:
            file_name = f"display_{date_frm}-{date_to}.log"
            log = LOG_PATH / "D" / file_name
        log.parent.mkdir(parents=True, exist_ok=True)

        py       = sys.executable or "python"
        cmd      = [ py, str(IMPORT_D), "--date_from", date_frm, "--date_to", date_to,]
        log_file = open(log, "w", encoding="utf-8")

        try:
            proc = subprocess.Popen( cmd,
                                     cwd    = str(BASE),
                                     creationflags=0x08000000,
                                     stdout = log_file,
                                     stderr = log_file,
                                     stdin  = subprocess.DEVNULL,
                                     text   = True,               )

        except subprocess.TimeoutExpired:
            proc.terminate()
            proc.wait(timeout=3)
            print("Terminated by stop request")

        except Exception as e:
            print(str(e))
    else:
        ETL_import_display_run(date_frm, date_to)

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
        con.close()

#===============================================================================
def parse_args():

    p = argparse.ArgumentParser(description="Daily K/B/display_run updater")
    p.add_argument("--date",      default=None,         help="対象日(yyyy)")
    p.add_argument("--date_from",                       help="期間開始(YYYY-MM-DD)")
    p.add_argument("--date_to",                         help="期間終了(YYYY-MM-DD)")
    p.add_argument("--overwrite",  action="store_true",default=False,  help="上書きﾓｰﾄﾞ")
    p.add_argument("--all",        action="store_true",default=False,  help="全不足日")
    p.add_argument("--background", action="store_true",default=False,  help="BGモード")

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
            print(f"{_date} is already imported")
        else:
            run_subprocess(_date, True, False, args.overwrite, args.background)
            run_subprocess(yesterday(_date), False, True, args.overwrite, args.background)

        _date = (dt.fromisoformat(_date) + timedelta(days=1)).strftime("%Y-%m-%d")

    update_FLstate()

    run_import_display(yesterday(d_f), yesterday(d_t), args.background)

#-----------------------------
def yesterday(_date:str):

    return (dt.fromisoformat(_date) - timedelta(days=1)).strftime("%Y-%m-%d")

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main())
