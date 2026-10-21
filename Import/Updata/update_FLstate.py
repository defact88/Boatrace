# -*- coding: utf-8 -*-
# C:\boatrace\Inport\update_FLstate.py

from __future__ import annotations
from datetime   import datetime as dt, date, timedelta
import sys, Dal as dal

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

#---------------------------------------------------------------------
def term_range_for_today(today:date) -> tuple[date, date]:

    y  = today.year
    md = (today.month, today.day)

    if (5,1) <= md <= (10,31): start = date(y,   5,1) ;end = today
    elif        md >= (11, 1): start = date(y,  11,1) ;end = today
    else:                      start = date(y-1,11,1) ;end = today

    return start, end

#---------------------------------------------------------------------
def yymmdd_bounds(d:date) -> tuple[int, int]:

    yy = d.year % 100

    return ( int(f"{yy:02d}{d.month:02d}{d.day:02d}0000"),
             int(f"{yy:02d}{d.month:02d}{d.day:02d}9999")  )

#---------------------------------------------------------------------
def cnt_FL_st(start:date, end:date) -> dict[int, tuple[int,int]]:

    s_lo, s_hi = yymmdd_bounds(start)
    e_lo, e_hi = yymmdd_bounds(end)
    lo         = s_lo
    hi         = e_hi

    sql = """
          SELECT player_id,
             SUM( CASE WHEN fault_code = 'F'
                       THEN 1
                       ELSE 0 END            ) AS flying_cnt,
             SUM( CASE WHEN fault_code = 'L'
                        AND IFNULL(fault_level,0) = 1
                       THEN 1
                       ELSE 0 END            ) AS late_cnt
            FROM Race_entries
           WHERE race_id BETWEEN ? AND ?
             AND(fault_code='F' OR fault_code='L')
        GROUP BY player_id;
    """

    rows = dal.fetch_all(sql, (lo, hi))

    return {int(pid):(int(fly or 0), int(late or 0)) for (pid, fly, late) in rows}

#---------------------------------------------------------------------
def write_back(counts:dict[int, tuple[int,int]]) -> None:

    dal.execute("""
        UPDATE Players
           SET flying_st =0,
               late_st   =0;
        """)

    if not counts: return

    params = [(fly, late, pid) for pid, (fly, late) in counts.items()]

    cnt = dal.executemany("""
        UPDATE Players
           SET flying_st =?,
               late_st   =?
         WHERE player_id =?;
        """,
        params)

    print(f"{cnt} players update F_L states done.")

#=====================================================================
def update_FLstate():

    today      = dt.today().date()
    start, end = term_range_for_today(today)
    counts     = cnt_FL_st(start, end)

    write_back(counts)

#---------------------------------------------------------------------
if __name__ == "__main__":
    update_FLstate()
