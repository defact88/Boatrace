# check_finals_by_series.py
# 指定年の全ｼﾘｰｽﾞを精査し 優勝戦(Races.is_final)が適正数であるかを検査

from __future__  import annotations
from datetime    import datetime
from collections import defaultdict
from typing      import List, Tuple, Dict
from wcwidth     import wcswidth
import argparse, sqlite3, re

DB      = r"C:\boatrace\boatrace.db"
DATEFMT = "%Y-%m-%d"
MAX_SPAN_DAYS = 10  # シリーズ最大幅

RE_W_FINAL = re.compile(
    r"男女Ｗ|男女ダブル|男女ハーフ|Ｗ優勝戦|ダブル優勝戦|Ｗ決定戦|オオムラグランプリ"
    r"|グランプリ／グランプリ"
    r"|チャレンジカップ／Ｇ２レディースＣＣ"
    r"|グランプリ（賞金王決定戦）／グランプリＳ"
    r"|クイーンズクライマックス", re.M)
#-------------------------------------------------------------------------------
def conn() -> sqlite3.Connection:
    c             = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c
#-------------------------------------------------------------------------------
def pad_display(text: str, width: int) -> str:
    disp_len = wcswidth(text)
    return text + " " * max(0, width - disp_len)
#-------------------------------------------------------------------------------
def verify_year(year:int):
    str_year = str(year)
    date_f   = f"{year}-01-01"
    date_t   = f"{year}-12-31"
    next_cut = f"{year+1}-01-{MAX_SPAN_DAYS:02d}"

    with conn() as c:
        total_races = c.execute("""
            SELECT
             COUNT(*) AS cnt
              FROM Races 
             WHERE strftime('%Y', date)=?
        """, (str_year,)).fetchall()[0]["cnt"]

        rows = c.execute("""
            SELECT r.series_title, r.venue_id, r.date,
                   r.status, r.is_final, r.race_no, v.venue_name
              FROM Races  r
              JOIN venues v
                ON v.venue_id = r.venue_id
             WHERE r.date
           BETWEEN ? AND ?
          ORDER BY r.series_title, r.venue_id, r.date, r.race_no
        """, (date_f, next_cut))

        # (series_title, venue_id) 単位で10日幅分割
        buckets: Dict[Tuple[str,int], List[List[sqlite3.Row]]] = defaultdict(list)
        for r in rows:
            key = ((r["series_title"] or "").strip(), int(r["venue_id"]))
            if not buckets[key]: buckets[key].append([r]); continue

            grp      = buckets[key][-1]
            start_dt = datetime.strptime(grp[0]["date"], DATEFMT)
            cur_dt   = datetime.strptime(  r["date"],    DATEFMT)
            if (cur_dt - start_dt).days <= MAX_SPAN_DAYS: grp.append(r)
            else:                                         buckets[key].append([r])
        series_total = 0 
        ok_cnt       = 0
        ng_list:List[Tuple[str,str,str,str]] = []

        for (title, vid), groups in buckets.items():
            title_str = title or ""
            is_mixed  = RE_W_FINAL.search(title_str)

            for g in groups:
                start_date = g[0]["date"]
                if not (date_f <= start_date <= date_t): continue
                series_total += 1
                venue_name    = g[0]["venue_name"]
                end_date      = g[-1]["date"]
                finals_held   = sum(1 for rr in g if (rr["status"]         == "held"
                                                 and (rr["is_final"] or 0) == 1     ))
                ok     = False
                reason = ""

                if is_mixed:
                    # W優勝戦:OK==優勝戦2(例外OK:優勝戦 == 0 and 最終日最終R == cancelled)
                    if   finals_held == 2: ok = True
                    elif finals_held == 0:
                        last_day_rows = [rr for rr in g if rr["date"] == end_date]
                        if last_day_rows:
                            max_rno = max(rr["race_no"] for rr in last_day_rows)
                            last_r  = next(rr for rr in last_day_rows
                                                        if rr["race_no"] == max_rno)
                            ok      = (last_r["status"] == "cancelled")
                        if not ok: reason = "優勝戦不足(0)"
                    else:
                        reason = "優勝戦不足(1)" if finals_held == 1 else "優勝戦過多"
                else:      # 通常シリーズ
                    if   finals_held == 1: ok = True
                    elif finals_held == 0:
                        last_day_rows = [rr for rr in g if rr["date"] == end_date]
                        if last_day_rows:
                            max_rno = max(rr["race_no"] for rr in last_day_rows)
                            last_r  = next(rr for rr in last_day_rows
                                                            if rr["race_no"] == max_rno)
                            ok = (last_r["status"] == "cancelled")
                        if not ok: reason = "優勝戦0"
                    else: reason = "優勝戦2~"
                if ok: ok_cnt += 1
                else:
                    ng_list.append((title_str, venue_name,
                                    f"{start_date}～{end_date}", reason))

        print(f"\n=== 優勝戦検査（開始{year}年～期間最大{MAX_SPAN_DAYS}日） ===")
        print(f"   \n対象全ﾚｰｽ数 : {total_races}")
        print(f"  対象シリーズ数 : {series_total}")
        print(f"検査OKシリーズ数 : {ok_cnt}")
        print(f"  検査NGシリーズ : {len(ng_list)} 件")
        if ng_list:
            print("---- NG一覧 ----")
            for title, venue, period, reason in ng_list:
                print(f"[{pad_display(title, 40)}] [{venue}] [{period}] [{reason}]")
#===============================================================================
def main():
    ap = argparse.ArgumentParser(description="Racesis_finalの精査")
    ap.add_argument("--year", type=int, required=True, help="対象年(yyyy)")
    args = ap.parse_args()
    verify_year(args.year)
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
