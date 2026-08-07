# -*- coding: utf-8 -*-

import argparse, csv, sqlite3
from decimal     import Decimal, ROUND_HALF_UP
from collections import defaultdict
from typing      import Union

DB_PATH = r"C:\boatrace\boatrace.db"

P_GEN_PRE  = {1:10, 2:8, 3:6, 4:4, 5:2, 6:1}
P_GEN_FIN  = {1:11, 2:9, 3:7, 4:6, 5:4, 6:3}
P_G12_PRE  = {1:11, 2:9, 3:7, 4:5, 5:3, 6:2}
P_G12_FIN  = {1:12, 2:10, 3:8, 4:7, 5:5, 6:4}
P_SG_PRE   = {1:12, 2:10, 3:8, 4:6, 5:4, 6:3}
P_SG_FIN   = {1:13, 2:11, 3:9, 4:8, 5:6, 6:5}

BT_KEY = "ファン感謝３Ｄａｙｓボートレースバトルトーナメント"

def is_bt_series(series_title: Union[str, None]) -> bool:
    s = (series_title or "").strip()
    return BT_KEY in s
#-------------------------------------------------------------------------------
def point_for(grade:int, is_final:int, rank:int, *, force_g12=False) -> float:

    if rank is None or not (1 <= rank <= 6): return 0.0
    fin = 1 if (is_final or 0) else 0
    if force_g12:tbl             = P_G12_FIN if fin else P_G12_PRE
    else:
        g = 0 if grade is None else int(grade)
        if g in (0, 1):      tbl = P_GEN_FIN if fin else P_GEN_PRE
        elif g in (2, 3, 4): tbl = P_G12_FIN if fin else P_G12_PRE
        elif g == 5:         tbl = P_SG_FIN  if fin else P_SG_PRE
        else:                tbl = P_GEN_FIN if fin else P_GEN_PRE
    return float(tbl.get(rank, 0))
#-------------------------------------------------------------------------------
def is_countable_start(fault_code:int, fault_level:int, finish_rank:int) -> bool:

    fc = (fault_code or 'N').upper()
    if fc in ('K', 'L', 'S') and fault_level == 0: return False
    if finish_rank == 0:                           return False

    return True
#-------------------------------------------------------------------------------
def load_official(c:sqlite3.Connection, year:int, season:int) -> dict[int, int]:

    rows = c.execute("""
        SELECT player_id, score_ave
          FROM Season_result
         WHERE year=? AND season=?
    """, (year, season)).fetchall()

    return {int(pid):int(score) for pid, score in rows if score is not None}
#===============================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv",  type=str, help="CSV出力するパス")
    ap.add_argument("year",   type=int, help="対象年(yyyy)")
    ap.add_argument("season", type=int, help="対象期(1:前期/2:後期)")
    args = ap.parse_args()

    date_fr = (f"{args.year-1}-05-01") if args.season == 1 else (f"{args.year-1}-11-01")
    date_to = (f"{args.year-1}-10-31") if args.season == 1 else (f"{args.year}-04-30")

    with sqlite3.connect(DB_PATH) as c:
        c.execute("PRAGMA foreign_keys=ON;")
        rows = c.execute("""
            SELECT e.player_id, e.finish_rank, e.fault_code, e.fault_level, r.grade, 
          COALESCE(r.is_final,0), r.series_title
              FROM Race_entries e
              JOIN Races r
                ON r.race_id = e.race_id
             WHERE r.status  = 'held'
               AND r.date
           BETWEEN ? AND ?
        """, (date_fr, date_to)).fetchall()

        starts    = defaultdict(int)
        total_pts = defaultdict(lambda: Decimal('0'))
        bt_cnt    = defaultdict(int)

        for pid, f_rank, fcode, flevel, grade, is_final, sname in rows:
            if not is_countable_start(fcode, flevel, f_rank): continue
            starts[pid] += 1
            rank         = int(f_rank) if f_rank is not None else None

            force_g12 = is_bt_series(sname)
            if force_g12: bt_cnt[pid] += 1
            total_pts[pid] += Decimal(str(point_for(grade, is_final, rank,
                                                    force_g12= force_g12  )))

        official = load_official(c, args.year, args.season)

    mismatches = []
    ok_count = ng_count = 0
    for pid in set(starts.keys()) | set(official.keys()):
        st   = starts.get(pid, 0)
        tp   = total_pts.get(pid, Decimal('0'))
        rate = (tp / Decimal(st)) if st > 0 else Decimal('0')
        x100 = (rate * Decimal(100)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        off  = official.get(pid, None)

        if off is None:
            mismatches.append([pid, st, float(tp), float(rate),
                               int(x100) if st>0 else "", "", "", bt_cnt.get(pid,0)])
            ng_count += 1
        else:
            if int(x100) == off: ok_count += 1
            else:
                diff = int(x100) - off
                mismatches.append([pid, st, float(tp), float(rate), int(x100), off,
                                   diff, bt_cnt.get(pid,0)])
                ng_count += 1
    total_players = ok_count + ng_count

    print("=== 全選手 照合サマリ ===")
    print(f"対象期間        : {date_fr} ～ {date_to}")
    print(f"選手数(推定)    : {total_players}")
    print(f"一致(OK)        : {ok_count}")
    print(f"不一致(NG/N/A)  : {ng_count}")
    if mismatches:
        cnt_ng = 0 
        print("\n====== 差異あり ========")
        for row in mismatches[:100]:
            pid, st, tp, rate, calc_x100, off, diff, bcnt = row
            if off:
                print(f"ID:{pid} 出走:{st:3} 得点:{tp:6} 率:{rate:.3f}  "
                      f"算出:{calc_x100:3} 公式:{off:3} 差:{diff}  B/T:{bcnt}" )
                cnt_ng += 1 
            else: continue
        print(f"-差異件数：{cnt_ng}件-")
        cnt_ng = 0
        print(f"\n======== 公式データ無し ==========")
        for row in mismatches[:100]:
            pid, st, tp, rate, calc_x100, off, diff, bcnt = row
            if not off:
                print(f"ID:{pid} 出走:{st:3} 得点:{tp:6} 率:{rate:.3f}  "
                      f"算出:{calc_x100:3} 公式:{off:3} 差:{diff}  B/T:{bcnt}" )
                cnt_ng += 1
        print(f"-ﾃﾞｰﾀ無し：{cnt_ng}件")                             
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["player_id", "starts", "total_points",
                        "rate", "calc_x100_rounded", "official_x100",
                        "diff(calc-off)", "bt_starts"                ] )
            w.writerows(mismatches)
        print(f"\n差異CSV出力: {args.csv}")
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
