# -*- coding: utf-8 -*-
# C:\boatrace\Tools\odds_data_audit.py

from __future__ import annotations
from datetime   import datetime as dt, timedelta
from typing     import Dict, List, Tuple
import argparse
import Dal as dal

DB_PATH   = r"C:\boatrace\boatrace.db"
BET_TYPES = ("3T", "3F", "2T", "2F", "TT", "FF", "KK")
SET_SIZE  = 212
MAX_SET   = 1

VENUES = [ None,    " 桐生 ", " 戸田 ", "江戸川", "平和島", "多摩川", "浜名湖", " 蒲郡 ",
          " 常滑 ", "  津  ", " 三国 ", "びわこ", "住之江", " 尼崎 ", " 鳴門 ", " 丸亀 ",
          " 児島 ", " 宮島 ", " 徳山 ", " 下関 ", " 若松 ", " 芦屋 ", " 福岡 ", " 唐津 ", " 大村 ",]

# ----------------------------------------------------------
def _today():

    return dt.today().strftime("%Y-%m-%d")
# ----------------------------------------------------------
def _date_where(args):

    params  = []
    clauses = " AND date >= ? AND date <= ? "

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

    rows = dal.fetch_all(f"""
        SELECT date, venue_id, race_no, captured_at,
               COUNT(*) AS cnt
          FROM Odds
         WHERE bet_type IN (?, ?, ?, ?, ?, ?, ?)
        {where}
      GROUP BY date, venue_id, race_no, captured_at
      ORDER BY date, venue_id, race_no, captured_at
        """,
        (*BET_TYPES, *params))

    races:Dict[Tuple, Dict[str, dict]] = {}

    for r in rows:
        key = (r["date"], r["venue_id"], r["race_no"])
        races.setdefault(key, {})[r["captured_at"]] = {"rows":r["cnt"]}

    return races

# ----------------------------------------------------------
def _pick_evenly_spaced(timestamps:List[dt], n:int) -> List[dt]:

    if len(timestamps) <= n: return timestamps[:]
    if               n <= 1: return [max(timestamps)]

    ts_sorted    = sorted(timestamps)
    t_min, t_max = ts_sorted[0], ts_sorted[-1]
    span         = (t_max - t_min).total_seconds()
    targets      = [t_min + timedelta(seconds=span * i / (n - 1)) for i in range(n)]
    remaining    = ts_sorted[:]
    chosen       = []

    for target in targets:
        idx = min(range(len(remaining)), key=lambda i:abs((remaining[i] - target).total_seconds()))
        chosen.append(remaining.pop(idx))

    return sorted(chosen)

# ============================================================
def do_inspect(args) -> Dict[Tuple, Dict[str, dict]]:

    where, params = _date_where(args)

    total = dal.fetch_one(f"""
        SELECT COUNT(*)
          FROM Odds
         WHERE 1=1
        {where}
        """,
        params)[0]

    print( f"[対象期間] {params[0]} ～ {params[1]}\n" if params[0] != params[1]
            else f"[対象日] {params[0]}\n" )
    print(f"[総ﾚｺｰﾄﾞ数] {total:,}")
    print("\n[賭式別レコード数]\n")

    for r in dal.fetch_all(f"""
        SELECT bet_type,
               COUNT(*) AS cnt
          FROM Odds
         WHERE 1=1
        {where}
      GROUP BY bet_type
      ORDER BY cnt DESC
        """,params):

        print(f"{r['bet_type']:>5} : {r['cnt']:>10,}")

    # セットサイズ異常 / 過剰スナップショット検出
    excess       = []
    anomaly_size = []
    races        = _load_race_sets(where, params)

    for key, sets in races.items():
        full_ts = [ts for ts, v in sets.items() if v["rows"] == SET_SIZE]
        if len(full_ts) > MAX_SET:
            excess.append((key, len(full_ts)))
        for ts, v in sets.items():
            if v["rows"] != SET_SIZE:
                anomaly_size.append((key, ts, v["rows"]))

    print(f"\n【 セットサイズ  異常 】(1set= {SET_SIZE})\n"
          f"\n検出数: {len(anomaly_size)} ﾚｰｽ\n")
    for (d_, v_, r_), ts, rows in anomaly_size[:20]:
        print(f"  {d_} jcd={v_:02} {r_:02}R  {ts} : rows={rows}")

    print(f"\n【過剰スナップショット】(MAX= {MAX_SET}set)\n"
          f"\n検出数: {len(excess)} ﾚｰｽ\n")
    for (d_, v_, r_), n in sorted(excess, key=lambda x: -x[1]):
        print(f"  {d_} {VENUES[v_]} {r_:02}R : full_sets= {n}")

    # サマリ(開催場/レースNo.別 総レコード数/セット数)
    if args.detail:

        summary = dal.fetch_all(f"""
            SELECT date, venue_id, race_no,
                   COUNT(*)                                   AS total_rows,
                   COUNT(DISTINCT date || '_' || captured_at) AS total_sets
              FROM Odds
             WHERE bet_type IN (?, ?, ?, ?, ?, ?, ?)
            {where}
          GROUP BY date, venue_id, race_no
          ORDER BY date, venue_id, race_no
            """,
            (*BET_TYPES, *params))

        print(f"\n[  日付     開催場/ﾚｰｽNo.  レコード数/セット数 ]\n")
        for r in summary:
            print(f"{r['date']}  {VENUES[r['venue_id']]} {r['race_no']:>2}R  :  "
                  f"rows={r['total_rows']:>5,}  sets={r['total_sets']:>3,}"       )

    return races

# ============================================================
def do_thin(args, races:Dict[Tuple, Dict[str, dict]]):

    del_cnt = 0

    for (d_, v_, r_), sets in races.items():
        # 完全スナップショットを MAX_SET まで間引く
        full_ts = [ts for ts, v in sets.items() if v["rows"] == SET_SIZE]

        if len(full_ts) > MAX_SET:
            dt_list = [dt.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in full_ts]
            keep_dt = set(_pick_evenly_spaced(dt_list, MAX_SET))
            keep_ts = {t.strftime("%Y-%m-%d %H:%M:%S") for t in keep_dt}
            remove  = [ts for ts in full_ts if ts not in keep_ts]
            ph      = ",".join("?" * len(remove))

            cur = dal.execute(f"""
                DELETE
                  FROM Odds
                 WHERE date     =?
                   AND venue_id =?
                   AND race_no  =?
                   AND captured_at IN ({ph})
                """,
                (d_, v_, r_, *remove))

            del_cnt += cur.rowcount

    print(f"\n[THIN]  過剰削除: {del_full:,} 行")

# ============================================================
def main():

    ap = argparse.ArgumentParser(description="Odds_snapshots 検査/間引きツール")
    ap.add_argument("--date_from",                   help="YYYY-MM-DD")
    ap.add_argument("--date_to",                     help="YYYY-MM-DD")
    ap.add_argument("--thin",   action="store_true", help="検査後DBに間引きを実行")
    ap.add_argument("--detail", action="store_true", help="summarize in detail")

    args  = ap.parse_args()
    races = do_inspect(args)

    if args.thin:
        do_thin(args, races)

if __name__ == "__main__":
    main()