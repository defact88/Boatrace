# list_player_finals.py
# 指定(選手,年,期)の優勝戦出走(date, venue_id, series_title)を出力

from __future__ import annotations
import argparse, sqlite3
from datetime import date

DB_PATH = r"C:\boatrace\boatrace.db"
#-------------------------------------------------------------------------------
def season_range(year:int, season:int) -> tuple[str, str]:
    if   season == 1: y  = year - 1; return (f"{y}-05-01", f"{y}-10-31")
    elif season == 2: y0 = year - 1; return (f"{y0}-11-01", f"{year}-04-30")
    else:
        raise ValueError("season must be 1 or 2")
#-------------------------------------------------------------------------------
def q(c, sql, args=()):
    return c.execute(sql, args).fetchall()
#-------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="指定選手の優勝戦出走を出力")
    ap.add_argument("--player", type=int, required=True, help="登録番号(player_id)")
    ap.add_argument("--year",   type=int, required=True, help="対象年(yyyy)")
    ap.add_argument("--season", type=int, required=True, help="対象期(1:前期/2:後期)")
    args = ap.parse_args()

    d0, d1 = season_range(args.year, args.season)

    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON;")

        rows = q(c, """
            SELECT r.date, r.venue_id, r.series_title
              FROM Race_entries e
              JOIN Races r
                ON r.race_id   = e.race_id
             WHERE e.player_id = ?
               AND r.is_final  = 1
               AND r.date 
           BETWEEN ? AND ?
          ORDER BY r.date, r.venue_id
        """, (args.player, d0, d1))

    print(f"=== 優勝戦出走一覧 player={args.player} year={args.year} season={args.season} ===")
    print(f"対象期間: {d0} ～ {d1}")
    if not rows:
        print("該当なし")
        return

    for r in rows:
        print(f"{r['date']}\tV{r['venue_id']}\t{r['series_title']}")
    print(f"件数: {len(rows)}")
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
