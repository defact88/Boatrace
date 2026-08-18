# -*- coding: utf-8 -*-
# C:\boatrace\Tools\odds_snapshot_audit.py
#
# Odds_snapshots 検査 / 間引きツール
#
# 使い方:
#   python odds_snapshot_audit.py                              (検査のみ、DB変更なし)
#   python odds_snapshot_audit.py --thin                       (検査後、間引きを実行)
#   python odds_snapshot_audit.py --date-from 2026-07-01 --date-to 2026-07-31 --thin

from __future__ import annotations
import argparse, sqlite3
from datetime import datetime as dt, timedelta
from typing   import Dict, List, Tuple

DB_PATH = r"C:\boatrace\boatrace.db"

TARGET_BET_TYPES  = ("3T", "3F", "2T", "KK")   # 2F は対象外(別スクリプトで一括削除)
EXPECTED_SET_SIZE = 185                        # 3T120+3F20+2T30+KK15
FULL_SET_MIN_ROWS = 100                        # この行数以上を「完全スナップショット」とみなす(ヒット単体insertとの区別用)
KEEP_SET_COUNT    = 3                          # is_final=0 の完全スナップショットを何セットまで残すか

# ----------------------------------------------------------
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

# ----------------------------------------------------------
def _date_where(args):
    clauses, params = [], []
    if args.date_from:
        clauses.append("date >= ?"); params.append(args.date_from)
    if args.date_to:
        clauses.append("date <= ?"); params.append(args.date_to)
    return (" AND " + " AND ".join(clauses)) if clauses else "", params

# ----------------------------------------------------------
def _load_race_sets(c:sqlite3.Connection, where:str, params:list):
    """
    (date, venue_id, race_no) 毎に captured_at をキーとした set 情報を集計する。
    TARGET_BET_TYPES のみが対象。
    戻り値: { (date, venue_id, race_no): { captured_at: {"is_final":0/1, "rows":int}, ... }, ... }
    """
    bt_ph = ",".join("?" * len(TARGET_BET_TYPES))
    rows = c.execute(f"""
        SELECT date, venue_id, race_no, captured_at, is_final, COUNT(*) AS cnt
          FROM Odds_snapshots
         WHERE bet_type IN ({bt_ph}){where}
      GROUP BY date, venue_id, race_no, captured_at, is_final
      ORDER BY date, venue_id, race_no, captured_at
        """, (*TARGET_BET_TYPES, *params)).fetchall()

    races: Dict[Tuple, Dict[str, dict]] = {}
    for r in rows:
        key = (r["date"], r["venue_id"], r["race_no"])
        races.setdefault(key, {})[r["captured_at"]] = {"is_final": r["is_final"], "rows": r["cnt"]}

    return races

# ----------------------------------------------------------
def _pick_evenly_spaced(timestamps:List[dt], n:int) -> List[dt]:
    """timestamps の中から、なるべく均等な間隔になるよう n 個を選んで返す"""

    if len(timestamps) <= n: return timestamps[:]
    if n <= 1: return [max(timestamps)]

    ts_sorted  = sorted(timestamps)
    t_min, t_max = ts_sorted[0], ts_sorted[-1]
    span       = (t_max - t_min).total_seconds()
    targets    = [t_min + timedelta(seconds=span * i / (n - 1)) for i in range(n)]

    remaining = ts_sorted[:]
    chosen    = []
    for target in targets:
        idx = min(range(len(remaining)), key=lambda i: abs((remaining[i] - target).total_seconds()))
        chosen.append(remaining.pop(idx))

    return sorted(chosen)

# ============================================================
# 検査
# ============================================================
def do_inspect(args) -> Dict[Tuple, Dict[str, dict]]:

    c = conn()
    where, params = _date_where(args)

    total = c.execute(f"SELECT COUNT(*) FROM Odds_snapshots WHERE 1=1{where}", params).fetchone()[0]
    print(f"[全体] 総行数: {total:,}")

    print("\n[賭式別 行数]")
    for r in c.execute(f"""
        SELECT bet_type, COUNT(*) AS cnt
          FROM Odds_snapshots
         WHERE 1=1{where}
      GROUP BY bet_type
      ORDER BY cnt DESC
        """, params).fetchall():
        print(f"  {r['bet_type']:>5} : {r['cnt']:>10,}")

    races = _load_race_sets(c, where, params)

    # ---- is_final=1 の重複検出 ----
    final_dup = []
    for key, sets in races.items():
        final_ts = [ts for ts, v in sets.items() if v["is_final"] == 1]
        if len(final_ts) > 1:
            final_dup.append((key, len(final_ts)))

    print(f"\n[is_final=1 重複] 対象レース: {len(final_dup)}")
    for (d_, v_, r_), n in sorted(final_dup, key=lambda x: -x[1])[:20]:
        print(f"  {d_} jcd={v_:02} {r_:02}R : final_batches={n}")

    # ---- is_final=0 の完全スナップショット過剰検出 ----
    excess = []
    anomaly_size = []
    for key, sets in races.items():
        full_ts = [ts for ts, v in sets.items() if v["is_final"] == 0 and v["rows"] >= FULL_SET_MIN_ROWS]
        if len(full_ts) > KEEP_SET_COUNT:
            excess.append((key, len(full_ts)))
        for ts, v in sets.items():
            if v["rows"] >= FULL_SET_MIN_ROWS and v["rows"] != EXPECTED_SET_SIZE:
                anomaly_size.append((key, ts, v["rows"]))

    print(f"\n[is_final=0 完全スナップショット過剰(>{KEEP_SET_COUNT}セット)] 対象レース: {len(excess)}")
    for (d_, v_, r_), n in sorted(excess, key=lambda x: -x[1])[:20]:
        print(f"  {d_} jcd={v_:02} {r_:02}R : full_sets={n}")

    print(f"\n[セット行数異常({EXPECTED_SET_SIZE}行と不一致)] 件数: {len(anomaly_size)}")
    for (d_, v_, r_), ts, rows in anomaly_size[:20]:
        print(f"  {d_} jcd={v_:02} {r_:02}R  {ts} : rows={rows}")

    # ---- B: 開催場/レースNo.別 総レコード数/セット数 ----
    print("\n[開催場/レースNo.別 総レコード数・セット数]")
    summary = c.execute(f"""
        SELECT venue_id, race_no,
               COUNT(*) AS total_rows,
               COUNT(DISTINCT date || '_' || captured_at) AS total_sets
          FROM Odds_snapshots
         WHERE bet_type IN ({",".join("?"*len(TARGET_BET_TYPES))}){where}
      GROUP BY venue_id, race_no
      ORDER BY venue_id, race_no
        """, (*TARGET_BET_TYPES, *params)).fetchall()

    for r in summary:
        print(f"  jcd={r['venue_id']:02} {r['race_no']:02}R : "
              f"rows={r['total_rows']:>7,}  sets={r['total_sets']:>5,}")

    c.close()
    return races

# ============================================================
# 間引き
# ============================================================
def do_thin(args, races:Dict[Tuple, Dict[str, dict]]):

    c = conn()
    del_final = 0
    del_full  = 0

    for (d_, v_, r_), sets in races.items():

        # ---- is_final=1: 最新1件のみ残す ----
        final_ts = [ts for ts, v in sets.items() if v["is_final"] == 1]
        if len(final_ts) > 1:
            keep   = max(final_ts)
            remove = [ts for ts in final_ts if ts != keep]
            ph     = ",".join("?" * len(remove))
            cur = c.execute(f"""
                DELETE FROM Odds_snapshots
                 WHERE date=? AND venue_id=? AND race_no=? AND is_final=1
                   AND captured_at IN ({ph})
                """, (d_, v_, r_, *remove))
            del_final += cur.rowcount

        # ---- is_final=0: 完全スナップショットを KEEP_SET_COUNT まで間引く ----
        full_ts = [ts for ts, v in sets.items() if v["is_final"] == 0 and v["rows"] >= FULL_SET_MIN_ROWS]
        if len(full_ts) > KEEP_SET_COUNT:
            dt_list = [dt.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in full_ts]
            keep_dt = set(_pick_evenly_spaced(dt_list, KEEP_SET_COUNT))
            keep_ts = {t.strftime("%Y-%m-%d %H:%M:%S") for t in keep_dt}
            remove  = [ts for ts in full_ts if ts not in keep_ts]
            ph      = ",".join("?" * len(remove))
            cur = c.execute(f"""
                DELETE FROM Odds_snapshots
                 WHERE date=? AND venue_id=? AND race_no=? AND is_final=0
                   AND captured_at IN ({ph})
                """, (d_, v_, r_, *remove))
            del_full += cur.rowcount

    c.commit()
    c.close()

    print(f"\n[THIN] is_final=1 重複削除: {del_final:,} 行")
    print(f"[THIN] is_final=0 過剰削除: {del_full:,} 行")

# ============================================================
def main():

    ap = argparse.ArgumentParser(description="Odds_snapshots 検査/間引きツール")
    ap.add_argument("--date-from", help="YYYY-MM-DD")
    ap.add_argument("--date-to",   help="YYYY-MM-DD")
    ap.add_argument("--thin", action="store_true", help="検査後、間引きをDBに実行する")
    args = ap.parse_args()

    races = do_inspect(args)

    if args.thin:
        do_thin(args, races)

if __name__ == "__main__":
    main()