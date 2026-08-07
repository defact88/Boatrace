# -*- coding: utf-8 -*-
# compare_score_rate.py
# 指定年期で指定選手の得点率を算出し Season_result.score_ave(公式値)と照合
# 出走数: S/K/L かつ fault_level=0 は出走に含めない。F は出走扱い。finish_rank=0 除外。
# サマリ: 優勝戦出走、SG出走、G1/G2/PG1出走、B/T出走、1～6着の総数を表示。
#   表示: 三位四捨五入(=小数第2位)、公式との一致判定(OK/NG)

import argparse, sqlite3, re
from decimal  import Decimal, ROUND_HALF_UP
from typing   import Union
from datetime import datetime as dt, date, timedelta

DB_PATH = r"C:\boatrace\boatrace.db"

P_GEN_PRE  = [0, 10,  8, 6, 4, 2, 1]
P_GEN_FIN  = [0, 11,  9, 7, 6, 4, 3]
P_G12_PRE  = [0, 11,  9, 7, 5, 3, 2]
P_G12_FIN  = [0, 12, 10, 8, 7, 5, 4]
P_SG_PRE   = [0, 12, 10, 8, 6, 4, 3]
P_SG_FIN   = [0, 13, 11, 9, 8, 6, 5]

BT_KEY = re.compile(r"ファン感謝３Ｄａｙｓボートレースバトルトーナメント"
                    r"|ファン感謝３ｄａｙｓボートレースバトルトーナメント"
                    r"|ボートレースバトルトーナメント",re.I)
#-----------------------------------------------------------
def is_bt_series(series_title:Union[str, None]) -> bool:
    s = (series_title or "").strip()
    return True if BT_KEY.search(s) else False
#-----------------------------------------------------------
def point_for(grade:Union[int, None], final:Union[int, None],
              rank:Union[int, None], *, force_g12:bool=False) -> float:

    if rank is None or not (1 <= rank <= 6): return 0.0

    if force_g12:                tbl = P_G12_FIN if final else P_G12_PRE
    else:
        if   grade in (2, 3, 4): tbl = P_G12_FIN if final else P_G12_PRE
        elif grade ==  5:        tbl = P_SG_FIN  if final else  P_SG_PRE
        else:                    tbl = P_GEN_FIN if final else P_GEN_PRE

    return tbl[rank or 0]

#-----------------------------------------------------------
def is_countable_start(fault_code:Union[int, None], fault_level:Union[int, None], finish_rank):

    fc = (fault_code or 'N').upper()
    if fc in ('K', 'L', 'S') and (fault_level == 0): return False
    if finish_rank == 0:                             return False

    return True
#-----------------------------------------------------------
def fetch_official_score(c:sqlite3.Connection, player_id:int, year:int, season:int):

    row = c.execute("""
        SELECT score_ave
          FROM Season_result
         WHERE player_id=? AND year=? AND season=?
    """, (player_id, year, season)).fetchone()

    return int(row[0]) if row and row[0] is not None else None
#-----------------------------------------------------------
def calc_score_rate(c:sqlite3.Connection, player_id:int, date_fr:str, date_to:str):

    rows = c.execute(
        """
        SELECT e.finish_rank, e.fault_code, e.fault_level,
               r.grade,       r.is_final,   r.series_title, r.date
          FROM Race_entries e
          JOIN Races r 
            ON r.race_id   = e.race_id
         WHERE e.player_id = ?
           AND r.status    = 'held'
           AND r.date      BETWEEN ? AND ?
        """,
               (player_id, date_fr, date_to)).fetchall()

    starts       = 0
    total_p      = Decimal('0')
    final_starts = 0
    sg_starts    = 0
    g12_starts   = 0
    bt_starts    = 0
    rank_counts  = {i: 0 for i in range(1, 7)}
    fault_cnt    = {'S0':0, 'S1':0, 'S2':0, 'F':0, 'L0':0, 'L1':0, 'K0':0, 'K1':0}
    final        = []

    for rank, fcode, flevel, grade, is_final, sname, _date in rows:

        if fcode != 'N':
            key = f"{fcode}{flevel if flevel is not None else ''}"
            fault_cnt[key] += 1
        if not is_countable_start(fcode, flevel, rank): continue

        starts += 1
        if is_final:
            final_starts += 1
            final.append((_date, sname))
        force_g12 = is_bt_series(sname) if date_to > ("2016-05-01") else False
        if force_g12:
            bt_starts  += 1
            g12_starts += 1
        else:
            if   grade == 5:         sg_starts  += 1
            elif grade in (2, 3, 4): g12_starts += 1

        if (rank is not None) and (rank in range(1,7)): rank_counts[rank] += 1
        total_p += Decimal(str( point_for(grade, is_final, rank, force_g12=force_g12)))

    rate = (total_p / starts) if starts > 0 else 0

    summary = { "final_starts": final_starts,
                   "sg_starts":    sg_starts,
                  "g12_starts":   g12_starts,
                   "bt_starts":    bt_starts,
                 "rank_counts":  rank_counts,  }

    return starts, total_p, rate, summary, fault_cnt, final, g12_starts, sg_starts
#===============================================================================
def main():

    ap = argparse.ArgumentParser(description="指定期の得点率算出と比較")
    ap.add_argument("year",      type=int, help="対象年(yyyy)")
    ap.add_argument("season",    type=int, help="対象期(1:前期/2:後期)")
    ap.add_argument("player_id", type=int, help="登録番号(player_id)")
    args = ap.parse_args()

    date_f = (f"{args.year-1}-05-01") if args.season == 1 else (f"{args.year-1}-11-01")
    date_t = (f"{args.year-1}-10-31") if args.season == 1 else (f"{args.year}-04-30")

    with sqlite3.connect(DB_PATH) as c:
        c.execute("PRAGMA foreign_keys=ON;")
        starts, total, rate, summ, f, fin, g1, sg = calc_score_rate(c, args.player_id, date_f, date_t)
        official_x100 = fetch_official_score(c, args.player_id, args.year, args.season)

    # 三位四捨五入
    rate_rounded = Decimal(str(rate)).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    rate_x100    = (rate * Decimal(100)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    verdict = "N/A" if official_x100 is None else ("OK" if rate_x100 == Decimal(official_x100) else "NG")

    print("=== 勝率（得点率）検証 ===\n")
    print(f"選手ID        : {args.player_id}")
    print(f"対象期間      : {date_f} ～ {date_t}")
    print(f"出走数        : {starts}")
    print(f"優出回数      : {summ['final_starts']}")
    print(f"SG出走数      : {summ['sg_starts']}")
    print(f"G1/G2/PG1出走 : {summ['g12_starts']}")
    print(f"B/T出走数     : {summ['bt_starts']}")
    print(f"1着～6着数    : " + " / ".join(f"{i}着: {summ['rank_counts'][i]}" for i in range(1, 7)))
    print(f"事故          : " + " / ".join(f"{k}:{v}" for k, v in f.items()))
    print(f"優出          : " + "".join(f"\n・{d}: {s}" for d, s in fin))
    print(f"SG出走        : {sg}")
    print(f"G1/G2出走     : {g1}")
    print(f"総得点        : {total}")
    print(f"算出得点率    : {rate_rounded}")
    if official_x100 is None:
        print("公式値        : (Season_result に未登録)")
    else:
        official_decimal = (Decimal(official_x100) / Decimal(100)).quantize(Decimal('0.00'))
        print(f"公式 score_ave: {official_decimal}")
        print(f"一致判定      : {verdict}")
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()