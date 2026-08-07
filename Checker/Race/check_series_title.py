from __future__ import annotations
from datetime   import date, timedelta
from itertools  import groupby
import sqlite3, argparse

VENUES = [   None, "桐生", "戸田", "江戸川", "平和島", "多摩川", "浜名湖", "蒲郡",
           "常滑", "津",   "三国", "びわこ", "住之江", "尼崎",   "鳴門",   "丸亀",
           "児島", "宮島", "徳山", "下関",   "若松",   "芦屋",   "福岡",   "唐津", "大村"]

DB = r"C:\boatrace\boatrace.db"

DEFAULT_TITLES = {"タイトル競走", "特別タイトル競走", "一般競走"}  # 優先度低い順に定義

#-----------------------------
def get_conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c
#-------------------------------------------------
def _best_title(day_rows:list, fallback:str) -> str:

    LOWEST   = {"タイトル競走", "特別タイトル競走"}
    GENERIC  = {"一般競走"}

    best_generic  = None

    for r in day_rows:
        t = r["series_title"]
        if t not in DEFAULT_TITLES:
            return t
        if t in GENERIC and best_generic is None:
            best_generic = t

    return best_generic or fallback

# ── dry_run出力 + 差分チェック ────────
def check_diff(c, venue_id:int, canon_title:str, d_fr:str, d_to:str) -> list[tuple]:

    rows = c.execute("""
        SELECT date,
               race_no,
               series_title
          FROM Races
         WHERE date BETWEEN ? AND ?
           AND venue_id      = ?
           AND series_title != ?
         ORDER BY date, race_no
        """,
        (d_fr, d_to, venue_id, canon_title)).fetchall()

    return [(r["date"], r["race_no"], r["series_title"]) for r in rows]

#-------------------------------------------------
def fetch_rows(c, venue_id:int, date_from:date, date_to:date) -> list:

    return c.execute("""
        SELECT date,
               series_title,
               day_no,
               race_no,
               is_final,
               status
          FROM Races
         WHERE venue_id = ?
           AND date BETWEEN ? AND ?
         ORDER BY date, race_no
        """,
       (venue_id, str(date_from), str(date_to))).fetchall()

#---------------------------------------
def is_series_end(day_rows:list) -> bool:

    race_nos    = {r["race_no"] for r in day_rows if r["status"] == "held"}
    has_r6      = 6 in race_nos
    has_final   = any(r["is_final"] and r["race_no"] in (11, 12) for r in day_rows)

    return has_r6 and has_final

#---------------------------------------
def group_by_date(rows) -> dict[str, list]:
    out = {}
    for r in rows:
        out.setdefault(r["date"], []).append(r)

    return out

#-----------------------------------------------------------
def build_series_spans(by_date:dict, year:int):

    spans        = []
    cur_title    = None
    cur_from     = None
    window_limit = None
    is_carryover = False

    for d_str, day_rows in by_date.items():

        day1_rows = [r for r in day_rows if r["day_no"] == 1]

        if day1_rows:
            if cur_title is not None:
                spans.append((cur_title, cur_from, _prev_date(d_str), is_carryover))

            cur_title    = day1_rows[0]["series_title"]
            cur_from     = d_str
            window_limit = _add_days(d_str, 9)
            is_carryover = d_str < f"{year}-01-01"

        if cur_title is None:
            continue

        if is_series_end(day_rows):
            if is_carryover:
                end_title = _best_title(day_rows, cur_title)
                spans.append((end_title, cur_from, d_str, is_carryover))
            else:
                spans.append((cur_title, cur_from, d_str, is_carryover))

            cur_title    = None
            cur_from     = None
            window_limit = None
            is_carryover = False
            continue

        if window_limit and d_str > window_limit:
            spans.append((cur_title, cur_from, d_str, is_carryover))
            cur_title    = None
            is_carryover = False

    if cur_title is not None:
        last_date = max(by_date.keys())
        spans.append((cur_title, cur_from, last_date, is_carryover))

    return spans

#-------------------
def _prev_date(d_str: str):
    return str(date.fromisoformat(d_str) - timedelta(days=1))
#-------------------
def _add_days(d_str: str, n: int):
    return str(date.fromisoformat(d_str) + timedelta(days=n))

#-----------------------------------------------------------
def prepend_carryover(c, venue_id:int, year:int, first_day_no:int, by_date:dict):

    lookback  = first_day_no + 2
    date_to   = date(year - 1, 12, 31)
    date_from = date_to - timedelta(days=lookback)

    rows = fetch_rows(c, venue_id, date_from, date_to)
    if not rows:
        print(f"[WARN] {VENUES[venue_id]} {year}: 年跨ぎ初日が見つかりません")
        return by_date

    prev_by_date = group_by_date(rows)

    found = {}
    for d_str, day_rows in prev_by_date.items():
        if any(r["day_no"] == 1 for r in day_rows):
            found = {}
        if found or any(r["day_no"] == 1 for r in day_rows):
            found[d_str] = day_rows

    if not found:
        print(f"[WARN] {VENUES[venue_id]} {year}: 年跨ぎ初日が見つかりません")
        return by_date

    found.update(by_date)

    return found

#-----------------------------------------------------------
def check_series_title(year:int, dry_run:bool=True):

    date_from = date(year, 1, 1)
    date_to   = date(year, 12, 31)
    c         = get_conn()

    for v in range(1, 25):
        rows = fetch_rows(c, v, date_from, date_to)
        if not rows:
            continue

        by_date        = group_by_date(rows)
        first_date     = min(by_date)
        first_day_rows = by_date[first_date]

        if not any(r["day_no"] == 1 for r in first_day_rows):
            first_day_no = first_day_rows[0]["day_no"]
            by_date = prepend_carryover(c, v, year, first_day_no, by_date)

        spans         = build_series_spans(by_date, year)
        updated_total = 0

        for canon_title, d_fr, d_to, carryover in spans:
            if dry_run:
                diffs = check_diff(c, v, canon_title, d_fr, d_to)
                diff_by_date:dict[str, list] = {}
                for d_str, r_no, actual in diffs:
                    diff_by_date.setdefault(d_str, []).append((r_no, actual))

                has_diff = bool(diffs)
                marker   = " ★" if has_diff else "  "
                co_mark  = " [年跨ぎ]" if carryover else ""
                print(f"{marker}[{VENUES[v]}] {d_fr} ～ {d_to}{co_mark}  →  {canon_title}")

                for d_str, entries in diff_by_date.items():
                    _, actual_title = entries[0]
                    r_nos = ", ".join(str(r) for r, _ in entries)
                    print(f"      {d_str}      '{actual_title}'")
                continue

            cur = c.execute("""
                UPDATE Races
                   SET series_title = ?
                 WHERE venue_id     = ?
                   AND date BETWEEN ? AND ?
                   AND series_title != ?
                """,
                (canon_title, v, d_fr, d_to, canon_title))

            updated_total += cur.rowcount

        if not dry_run and updated_total:
            print(f"[{VENUES[v]}] {year}: {updated_total} 件更新")

    if not dry_run:
        c.commit()
    c.close()
#-----------------------------------------------------------
if __name__ == "__main__":

    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--exec", action="store_true", help="dry_run解除して実際に更新")
    args = ap.parse_args()
    check_series_title(args.year, dry_run=not args.exec)