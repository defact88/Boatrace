# -*- coding: utf-8 -*-
# C:\boatrace\UI\Scraper\import_original_info.py
# オリジナル展示データを取得して Oriten に upsert (summarize_today.py からサブプロセス実行)
#   exit code: 0=OK / 1=取得エラー / 2=未反映(再試行) / 3=対象外

import Dal as dal
import argparse, sys
from datetime import datetime as dt, date
from scrape_original_info import SUPPORTED, FIELDS, build_url, fetch_html, parse_original, is_today_only

# ----------------------------------------------------------
def build_ids(d_iso:str, venue_id:int, race_no:int, frame_no:int):

    ymd      = dt.strptime(d_iso, "%Y-%m-%d").strftime("%y%m%d")
    race_id  = int(f"{ymd}{venue_id:02d}{race_no:02d}")
    entry_id = int(f"{ymd}{venue_id:02d}{race_no:02d}{frame_no}")

    return race_id, entry_id

# ----------------------------------------------------------
def fetch_frames(d_iso:str, venue_id:int, race_no:int) -> dict:
    """ {frame_no: is_absent} (出走表の枠 / 欠場はBefore_infoから) """

    rows = dal.fetch_all("""
           SELECT rp.frame_no, COALESCE(be.is_absent, 0)
             FROM Race_programs rp
        LEFT JOIN Before_info   be ON be.entry_id = rp.program_id
            WHERE rp.date= ? AND rp.venue_id= ? AND rp.race_no= ?
         ORDER BY rp.frame_no
           """, (d_iso, venue_id, race_no))

    return {int(r[0]): int(r[1]) for r in rows}

# ----------------------------------------------------------
def upsert_Oriten(d_iso:str, venue_id:int, race_no:int, parsed:dict, frames:dict):

    sql = """
        INSERT INTO Oriten( entry_id, date, venue_id, race_no, frame_no,
                            time_turning, time_acceleration, time_lap )
             VALUES (?,?,?,?,?,?,?,?)
        ON CONFLICT(entry_id)
            DO UPDATE SET time_turning      = excluded.time_turning,
                          time_acceleration = excluded.time_acceleration,
                          time_lap          = excluded.time_lap
          """
    params = []
    for fr in sorted(frames):
        p        = parsed.get(fr)
        if not p: continue
        _, e_id  = build_ids(d_iso, venue_id, race_no, fr)
        params.append(( e_id, d_iso, venue_id, race_no, fr,
                        p["time_turning"], p["time_acceleration"], p["time_lap"] ))

    dal.executemany(sql, params)

# ====================================================================
def main(argv=None):

    ap = argparse.ArgumentParser()
    ap.add_argument("--date",  required=True, help="YYYY-MM-DD")
    ap.add_argument("--venue", required=True, type=int)
    ap.add_argument("--race",  required=True, type=int)
    args = ap.parse_args(argv)

    if args.venue not in SUPPORTED:
        print(f"[SKIP] venue={args.venue} は対象外"); return 3

    if is_today_only(args.venue) and args.date != date.today().strftime("%Y-%m-%d"):
        print(f"[SKIP] venue={args.venue} は当日分のみ取得可"); return 3

    frames = fetch_frames(args.date, args.venue, args.race)
    if not frames:
        print(f"[WARN] venue={args.venue} {args.race}R Race_programs が未整備です"); return 2

    url = build_url(args.venue, args.date.replace("-", ""), args.race)
    try:
        html = fetch_html(url)
    except Exception as e:
        print(f"[ERR] Page access failed: {e}"); return 1

    parsed = parse_original(html, args.venue)

    # 欠場でない枠に、1項目も値が無い(未反映/計測前)なら未反映扱い
    not_ready = [ fr for fr, absent in frames.items()
                  if not absent and not any( (parsed.get(fr) or {}).get(f) is not None
                                             for f in FIELDS ) ]
    if not_ready:
        print(f"page update yet (not ready frames={not_ready})"); return 2

    upsert_Oriten(args.date, args.venue, args.race, parsed, frames)
    print(f"[OK] Upsert: {args.date} jcd={args.venue} {args.race}R")

    return 0

if __name__ == "__main__":
    sys.exit(main())