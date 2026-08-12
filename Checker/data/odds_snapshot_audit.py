# -*- coding: utf-8 -*-
# C:\boatrace\Tools\odds_snapshot_audit.py
#
# Odds_snapshots テーブルの検査 / 可視化 / 間引きツール
#
# 使い方:
#   python odds_snapshot_audit.py inspect [--date-from YYYY-MM-DD] [--date-to YYYY-MM-DD]
#   python odds_snapshot_audit.py plot    [--date-from ...] [--date-to ...]
#   python odds_snapshot_audit.py thin    [--date-from ...] [--date-to ...] [--apply] [--delete-duplicates]
#
# thin は既定でドライラン。--apply を付けたときのみ実際にDBを更新し、その直前に自動バックアップを取る。
# 既定の是正方法は「物理削除」ではなく「is_final=0への降格」(締切に最も近い1バッチだけを is_final=1 として残す)。

from __future__ import annotations
import argparse, sqlite3, sys
from datetime import datetime as dt
from pathlib  import Path

DB_PATH    = r"C:\boatrace\boatrace.db"
OUT_DIR    = Path(r"C:\boatrace\tmp\odds_audit")
BACKUP_DIR = Path(r"C:\boatrace\BACKUP\DB\odds_audit")

# ----------------------------------------------------------
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON;")
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
def _auto_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts  = dt.now().strftime("%Y%m%d_%H%M%S")
    dst = BACKUP_DIR / f"boatrace_{ts}.db"
    with open(DB_PATH, "rb") as fsrc, open(dst, "wb") as fdst:
        fdst.write(fsrc.read())
    print(f"[backup] {dst}")

# ============================================================
# 1) inspect: 現状把握
# ============================================================
def cmd_inspect(args):

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

    print("\n[is_final 重複レース検出] (本来は1レース1バッチのみのはず)")
    dup = c.execute(f"""
        SELECT date, venue_id, race_no, COUNT(DISTINCT captured_at) AS n
          FROM Odds_snapshots
         WHERE is_final = 1{where}
      GROUP BY date, venue_id, race_no
        HAVING n > 1
      ORDER BY n DESC, date, venue_id, race_no
        """, params).fetchall()

    if not dup:
        print("  重複なし")
    else:
        for r in dup[:30]:
            print(f"  {r['date']} jcd={r['venue_id']:02} {r['race_no']:02}R : "
                  f"final_batches={r['n']} (excess={r['n']-1})")
        if len(dup) > 30:
            print(f"  ...ほか {len(dup)-30} レース")
        excess_total = sum(r["n"] - 1 for r in dup)
        print(f"\n  重複レース数: {len(dup)} / 超過バッチ延べ数: {excess_total}")

    print("\n[日付別 総行数(直近10日)]")
    for r in reversed(c.execute(f"""
        SELECT date, COUNT(*) AS cnt
          FROM Odds_snapshots
         WHERE 1=1{where}
      GROUP BY date
      ORDER BY date DESC
         LIMIT 10
        """, params).fetchall()):
        print(f"  {r['date']} : {r['cnt']:>8,}")

    c.close()

# ============================================================
# 2) plot: 可視化
# ============================================================
def cmd_plot(args):

    try:
        import matplotlib
        matplotlib.use("Agg")   # 非対話環境でも確実にPNG出力できるように
        import matplotlib.pyplot as plt
    except ImportError:
        print("[ERR] matplotlib が未インストールです。 pip install matplotlib を実行してください。")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    c = conn()
    where, params = _date_where(args)

    # --- ① 日付別 総行数 ---
    rows = c.execute(f"""
        SELECT date, COUNT(*) AS cnt
          FROM Odds_snapshots
         WHERE 1=1{where}
      GROUP BY date
      ORDER BY date
        """, params).fetchall()

    if rows:
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.bar([r["date"] for r in rows], [r["cnt"] for r in rows], color="#2B4A7A")
        ax.set_title("日付別 Odds_snapshots 行数")
        ax.set_ylabel("行数")
        ax.tick_params(axis="x", rotation=90, labelsize=6)
        fig.tight_layout()
        fig.savefig(OUT_DIR / "daily_row_counts.png", dpi=130)
        plt.close(fig)
        print(f"[OK] {OUT_DIR / 'daily_row_counts.png'}")

    # --- ② is_final バッチ数のヒストグラム(1が正常、2以上が重複バグの痕跡) ---
    rows = c.execute(f"""
        SELECT COUNT(DISTINCT captured_at) AS n
          FROM Odds_snapshots
         WHERE is_final = 1{where}
      GROUP BY date, venue_id, race_no
        """, params).fetchall()

    if rows:
        vals  = [r["n"] for r in rows]
        max_v = max(vals)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(vals, bins=range(1, max_v + 2), align="left", color="#CC0000", rwidth=0.8)
        ax.set_title("レース毎 is_final バッチ数の分布(1が正常)")
        ax.set_xlabel("distinct captured_at (is_final=1)")
        ax.set_ylabel("レース数")
        ax.set_xticks(range(1, max_v + 1))
        fig.tight_layout()
        fig.savefig(OUT_DIR / "final_batch_histogram.png", dpi=130)
        plt.close(fig)
        print(f"[OK] {OUT_DIR / 'final_batch_histogram.png'}")

    # --- ③ 取得間隔の分布(3T基準、設計通り5分/1分/15秒の3ピークになっているか) ---
    rows = c.execute(f"""
        SELECT date, venue_id, race_no, captured_at
          FROM Odds_snapshots
         WHERE bet_type='3T'{where}
      GROUP BY date, venue_id, race_no, captured_at
      ORDER BY date, venue_id, race_no, captured_at
        """, params).fetchall()

    intervals = []
    prev_key, prev_time = None, None
    for r in rows:
        key = (r["date"], r["venue_id"], r["race_no"])
        t   = dt.strptime(r["captured_at"], "%Y-%m-%d %H:%M:%S")
        if key == prev_key and prev_time is not None:
            intervals.append((t - prev_time).total_seconds())
        prev_key, prev_time = key, t

    intervals = [v for v in intervals if v <= 600]
    if intervals:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(intervals, bins=40, color="#2A6632")
        ax.set_title("取得間隔の分布(3T, 600秒以内)")
        ax.set_xlabel("秒")
        ax.set_ylabel("件数")
        fig.tight_layout()
        fig.savefig(OUT_DIR / "capture_interval_histogram.png", dpi=130)
        plt.close(fig)
        print(f"[OK] {OUT_DIR / 'capture_interval_histogram.png'}")

    c.close()
    return 0

# ============================================================
# 3) thin: is_final 重複の是正
# ============================================================
def cmd_thin(args):

    c = conn()
    where, params = _date_where(args)

    groups = c.execute(f"""
        SELECT date, venue_id, race_no
          FROM Odds_snapshots
         WHERE is_final = 1{where}
      GROUP BY date, venue_id, race_no
        HAVING COUNT(DISTINCT captured_at) > 1
        """, params).fetchall()

    if not groups:
        print("[OK] 是正対象なし(is_final の重複は検出されませんでした)")
        c.close()
        return 0

    print(f"[対象] {len(groups)} レースで is_final 重複を検出")

    affected = 0
    action   = "物理削除" if args.delete_duplicates else "is_final=0 へ降格"

    for g in groups:
        d, v, r = g["date"], g["venue_id"], g["race_no"]

        caps = c.execute("""
            SELECT DISTINCT captured_at
              FROM Odds_snapshots
             WHERE date=? AND venue_id=? AND race_no=? AND is_final=1
          ORDER BY captured_at DESC
            """, (d, v, r)).fetchall()

        demote_ts = [row["captured_at"] for row in caps[1:]]   # 最新1件(締切に最も近い)以外
        if not demote_ts: continue

        ph = ",".join("?" * len(demote_ts))

        if args.delete_duplicates:
            cnt = c.execute(f"""
                DELETE FROM Odds_snapshots
                 WHERE date=? AND venue_id=? AND race_no=? AND is_final=1
                   AND captured_at IN ({ph})
                """, (d, v, r, *demote_ts)).rowcount
        else:
            cnt = c.execute(f"""
                UPDATE Odds_snapshots
                   SET is_final = 0
                 WHERE date=? AND venue_id=? AND race_no=? AND is_final=1
                   AND captured_at IN ({ph})
                """, (d, v, r, *demote_ts)).rowcount

        affected += cnt

    if args.apply:
        _auto_backup()   # 反映直前にバックアップ
        c.commit()
        print(f"[APPLY] {affected} 行を{action}しました")
    else:
        c.rollback()
        print(f"[DRY-RUN] {affected} 行が{action}対象でした (--apply を付けると実際に反映されます)")

    c.close()
    return 0

# ============================================================
def main():
    ap = argparse.ArgumentParser(description="Odds_snapshots 検査/可視化/間引きツール")

    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--inspect", action="store_true", help="現状把握")
    group.add_argument("--plot", action="store_true", help="可視化")
    group.add_argument("--thin", action="store_true", help="間引き")
    
    ap.add_argument("--date-from", help="YYYY-MM-DD")
    ap.add_argument("--date-to",   help="YYYY-MM-DD")
    ap.add_argument("--apply", action="store_true", help="実際にDBへ反映する")
    ap.add_argument("--delete-duplicates", action="store_true", help="物理削除する")

    args = ap.parse_args()

    if args.inspect:
        return cmd_inspect(args)
    elif args.plot:
        return cmd_plot(args)
    elif args.thin:
        return cmd_thin(args)

    return 0

if __name__ == "__main__":
    sys.exit(main())