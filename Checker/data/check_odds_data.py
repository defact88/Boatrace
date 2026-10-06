# -*- coding: utf-8 -*-
# C:\boatrace\Checker\data\check_odds_data.py

from __future__ import annotations
from datetime   import datetime as dt, timedelta
from typing     import Dict, List, Tuple
import argparse
import Dal as dal

DB_PATH   = r"C:\boatrace\boatrace.db"
BET_TYPES = ("3T", "3F", "2T", "2F", "TT", "FF", "KK")

VENUES = [ None,    " 桐生 ", " 戸田 ", "江戸川", "平和島", "多摩川", "浜名湖", " 蒲郡 ",
          " 常滑 ", "  津  ", " 三国 ", "びわこ", "住之江", " 尼崎 ", " 鳴門 ", " 丸亀 ",
          " 児島 ", " 宮島 ", " 徳山 ", " 下関 ", " 若松 ", " 芦屋 ", " 福岡 ", " 唐津 ", " 大村 ",]

# ----------------------------------------------------------
def _today():

    return dt.today().strftime("%Y-%m-%d")
# ----------------------------------------------------------
def _date_where(args):

    params  = []
    clauses = " WHERE date >= ? AND date <= ? "

    if args.date_from:
        if args.date_to:
            params = [args.date_from, args.date_to,]
        else:
            params = [args.date_from, _today(),]
    elif args.date_to:
        params = [args.date_to, args.date_to,]
    else:
        params = [_today(), _today(),]

    return clauses, params

# ----------------------------------------------------------
def _load_race_sets(where:str, params:list):

    races:Dict[Tuple,Dict[str,int]] = {}

    for bt in BET_TYPES:
        rows = dal.fetch_all(f"""
           SELECT r.date,
                  r.venue_id,
                  r.race_no,
                  COUNT(o.race_id) AS cnt
             FROM Races r
        LEFT JOIN Odds_{bt} o ON r.race_id = o.race_id 
            WHERE r.date >= ? AND r.date <= ?
              AND r.status = 'held'
         GROUP BY r.date, r.venue_id, r.race_no
         ORDER BY r.date, r.venue_id, r.race_no
           """,
           params )

        if rows:
            for r in rows:
                key = (r["date"], r["venue_id"], r["race_no"])
                races.setdefault(key, {})[bt] = r["cnt"]

    return races

# ----------------------------------------------------------
def fetch_program(where:str, params:list):

    row = dal.fetch_one(f"""
              SELECT SUM(CASE WHEN race_no = 1     THEN 1 ELSE 0 END) as cnt_v,
                     SUM(CASE WHEN status = 'held' THEN 1 ELSE 0 END) as cnt_r
                FROM Races
              {where}
              """,
              params )

    return row["cnt_v"], row["cnt_r"]

# ============================================================
def do_inspect(args) -> Dict[Tuple, Dict[str, dict]]:

    where, params    = _date_where(args)
    total_v, total_r = fetch_program(where, params)
    total_cnt        = 0
    bt_cnt           = {}

    for bt in BET_TYPES:
        cnt = dal.fetch_one(f"""
            SELECT COUNT(*)
              FROM Odds_{bt}
            {where}
            """,
            params )[0]

        total_cnt += cnt if cnt else 0
        bt_cnt[bt] = cnt

    print( f"[対象期間] {params[0]} ～ {params[1]}\n" if params[0] != params[1]
            else f"[対象日] {params[0]}\n" )

    print(f"[ 総 開催 数] {total_v:>6} 場")
    print(f"[ 総 ﾚｰｽ  数] {total_r:>6} ﾚｰｽ")
    print(f"[レコード 数] {total_cnt:>6} ﾚｺｰﾄﾞ")

    for bt in BET_TYPES:
        print(f"{"":>6}【 {bt} 】     {bt_cnt[bt]}")

    shortage:Dict[Tuple,List[str]] = {}
    no_record                      = []
    races                          = _load_race_sets(where, params)

    for key, bts in races.items():
        if sum(bts.values()) == 0:
           no_record.append(key)
           continue
        set_cnt = 0
        for bt, cnt in bts.items():
            if cnt == 0:
                shortage[key].append(bt)

    print(f"\n【 レコード 無し 】\n"
          f"    検出数: {len(no_record)} ﾚｰｽ\n")
    for d, v, r in no_record:
        print(f"  {d} {VENUES[v]} {r:02}R  : no record")

    print(f"\n【 レコード数 異常 】\n"
          f"    検出数: {len(shortage)} ﾚｰｽ\n")
    for (d, v, r), bt in shortage:
        print(f"  {d} {VENUES[v]} {r:02}R  【{bt}】: shortage")

    if args.detail:
        print(f"\n[  日付     開催場/ﾚｰｽNo.   賭式    レコード数 ]\n")
        for key, bts in races.items():
            for bt, cnt in bts.items():
                print(f"{key[0]}  {VENUES[key[1]]} {key[2]:>2}R  :  【{bt}】     {cnt}")

    return races

# ============================================================
def main():

    ap = argparse.ArgumentParser(description="Odds_snapshots 検査/間引きツール")
    ap.add_argument("--date_from",                   help="YYYY-MM-DD")
    ap.add_argument("--date_to",                     help="YYYY-MM-DD")
    ap.add_argument("--detail", action="store_true", help="summarize in detail")

    args  = ap.parse_args()
    races = do_inspect(args)

if __name__ == "__main__":
    main()