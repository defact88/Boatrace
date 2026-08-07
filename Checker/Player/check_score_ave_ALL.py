# -*- coding: utf-8 -*-
# C:\boatrace\Checker\Player\check_score_ave_ALL.py

import argparse, csv, sqlite3, re
from decimal     import Decimal, ROUND_HALF_UP
from collections import defaultdict
from typing      import  Dict, Optional
from datetime    import datetime as dt, date, timedelta

DB_PATH = r"C:\boatrace\boatrace.db"

P_GEN_PRE  = [0, 10,  8, 6, 4, 2, 1]
P_GEN_FIN  = [0, 11,  9, 7, 6, 4, 3]
P_G12_PRE  = [0, 11,  9, 7, 5, 3, 2]
P_G12_FIN  = [0, 12, 10, 8, 7, 5, 4]
P_SG_PRE   = [0, 12, 10, 8, 6, 4, 3]
P_SG_FIN   = [0, 13, 11, 9, 8, 6, 5]

BT_KEY = re.compile(r"ファン感謝３Ｄａｙｓボートレースバトルトーナメント"
                    r"|ファン感謝３ｄａｙｓボートレースバトルトーナメント"
                    r"|ＢＯＡＴＲＡＣＥバトルトーナメント",re.I)

#-----------------------------
def is_bt(series_title:str|None) -> bool:
    s = (series_title or "").strip()
    return True if BT_KEY.search(s) else False
#-----------------------------
def is_countable(f_level:int|None, finish) -> bool:
    if f_level == 0: return False
    if finish  == 0: return False
    return True
#-----------------------------------------------------------
def point_for(grade:int|None, final:int|None, rank:int|None, *, force_g12:bool=False):

    if rank is None or not (1 <= rank <= 6): return 0.0

    if force_g12:                tbl = P_G12_FIN if final else P_G12_PRE
    else:
        if   grade in (2, 3, 4): tbl = P_G12_FIN if final else P_G12_PRE
        elif grade ==  5:        tbl = P_SG_FIN  if final else  P_SG_PRE
        else:                    tbl = P_GEN_FIN if final else P_GEN_PRE

    return tbl[rank or 0]

#-----------------------------------------------------------
def load_official(c:sqlite3.Connection, year:int, season:int):

    rows = c.execute("""
        SELECT player_id, score_ave
          FROM Season_result
         WHERE year   =?
           AND season =?
    """, (year, season)).fetchall()

    return {int(pid):int(score) for pid, score in rows if score is not None}

#-----------------------------------------------------------
def check_season(c:sqlite3.Connection, year:int, season:int):
    date_fr = (f"{year-1}-05-01") if season == 1 else (f"{year-1}-11-01")
    date_to = (f"{year-1}-10-31") if season == 1 else (f"{year}-04-30")

    rows = c.execute("""
        SELECT e.player_id, e.finish_rank, e.fault_level,
               r.grade, r.is_final, r.series_title
          FROM Race_entries e
          JOIN Races r ON r.race_id = e.race_id
         WHERE r.status  = 'held'
           AND r.date BETWEEN ? AND ?
    """, (date_fr, date_to)).fetchall()

    starts    = defaultdict(int)
    total_pts = defaultdict(lambda: Decimal('0'))
    bt_cnt    = defaultdict(int)

    for pid, f_rank, f_level, grade, is_final, sname in rows:
        if not is_countable(f_level, f_rank): continue
        force_g12 = is_bt(sname) if date_to > ("2016-05-01") else False
        starts[pid]    += 1
        bt_cnt[pid]    += 1 if is_bt(sname) else 0
        total_pts[pid] += Decimal(str(point_for(grade, is_final, f_rank, force_g12=force_g12)))

    official = load_official(c, year, season)
    
    ng_list = []
    na_list = []
    ok_count = 0
    
    pids = set(starts.keys()) | set(official.keys())
    for pid in pids:
        st   = starts.get(pid, 0)
        tp   = total_pts.get(pid, Decimal('0'))
        rate = (tp / Decimal(st)) if st > 0 else Decimal('0')
        x100 = (rate * Decimal(100)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        off  = official.get(pid, None)

        row = [pid, st, float(tp), float(rate), int(x100) if st>0 else 0, off, 
               (int(x100) - off) if off is not None else "", bt_cnt.get(pid,0)]

        if off is None:
            na_list.append(row)
        else:
            if int(x100) == off:
                ok_count += 1
            else:
                ng_list.append(row)
                
    return { "year": year, "season": season,
             "date_fr": date_fr, "date_to": date_to,
             "ok": ok_count, "ng": ng_list, "na": na_list,
             "total": ok_count + len(ng_list) + len(na_list) }

#=====================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv",  type=str, help="CSV出力するパス")
    ap.add_argument("--all_year", action="store_true", help="2006年前期～現在まで全期間検査")
    ap.add_argument("year",   type=int, nargs='?', help="対象年(yyyy)")
    ap.add_argument("season", type=int, nargs='?', help="対象期(1:前期/2:後期)")
    args = ap.parse_args()

    if not args.all_year and (args.year is None or args.season is None):
        ap.error("year と season を指定するか、--all_year を使用してください。")

    target_periods = []
    if args.all_year:
        now = dt.today()
        if now.month <= 4:          curr_y, curr_s = now.year, 1
        elif 5 <= now.month <= 10:  curr_y, curr_s = now.year, 2
        else:                       curr_y, curr_s = now.year +1, 1

        for y in range(2006, curr_y + 1):
            for s in [1, 2]:
                if y == curr_y and s > curr_s: break
                target_periods.append((y, s))
    else:
        target_periods.append((args.year, args.season))

    csv_rows      = []
    summary_lines = []

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys=ON;")

        for y, s in target_periods:
            res = check_season(conn, y, s)
            summary_lines.append(f"{y}年  {s}期: 不一致(NG) {len(res['ng']):3}件 / データ無(N/A) {len(res['na']):3}件")

            if not args.all_year:
                print(f"\n=== 照合サマリ ({y}年 {s}期) ===")
                print(f"対象期間    : {res['date_fr']} ～ {res['date_to']}")
                print(f"選手数(計)  : {res['total']}")
                print(f"一致(OK)    : {res['ok']}")
                print(f"不一致(NG)  : {len(res['ng'])}")
                print(f"データ無(NA): {len(res['na'])}")
                
                if res['ng']:
                    print("\n====== 差異あり ========")
                    for r in res['ng'][:100]:
                        print(f"ID:{r[0]} 出走:{r[1]:3} 得点:{r[2]:6} 率:{r[3]:.3f} 算出:{r[4]:3} 公式:{r[5]:3} 差:{r[6]:2} B/T:{r[7]}")
                    print(f"-差異件数：{len(res['ng'])}件-")
                if res['na']:
                    print(f"\n======== 公式データ無し ==========")
                    for r in res['na'][:100]:
                        print(f"ID:{r[0]} 出走:{r[1]:3} 得点:{r[2]:6} 率:{r[3]:.3f} 算出:{r[4]:3} 公式:--- B/T:{r[7]}")
                    print(f"-ﾃﾞｰﾀ無し：{len(res['na'])}件-") 
            if args.csv:
                for r in res['ng']: csv_rows.append([y, s,  "NG"] + r)
                for r in res['na']: csv_rows.append([y, s, "N/A"] + r)

    if args.all_year:
        print("\n\n=== 全期間 照合結果サマリ ===")
        for line in summary_lines:
            print(line)

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["year", "season", "type", "player_id", "starts", "total_pts", "rate", "calc_x100", "official", "diff", "bt_cnt"])
            w.writerows(csv_rows)
        print(f"\nCSV出力: {args.csv}")
#=====================================================================
if __name__ == "__main__":
    main()