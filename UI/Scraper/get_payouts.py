# -*- coding: utf-8 -*-
# C:\boatrace\UI\Subprocess\ETL_Before_info.py

import time, sys, subprocess, argparse
from datetime import datetime as dt, timedelta
import Dal as dal

# ------------------------------------------------------------
def _combo(*frames) -> int:

    return int("".join(str(f) for f in frames))

# ------------------------------------------------------------
def _get_finish_frames(race_id:int) -> dict:

    rows = dal.fetch_all("""
               SELECT finish_rank, frame_no
                 FROM Race_entries
                WHERE race_id = ?
                  AND finish_rank IS NOT NULL
             ORDER BY finish_rank, frame_no
               """,
               (race_id,) )

    result = {}
    for rk, fr in rows:
        result.setdefault(rk, []).append(fr)

    return result

# ------------------------------------------------------------
def _get_odds(race_id:int, bet_type:str, combo:int):

    row = dal.fetch_one("""
              SELECT odds
                FROM Odds
               WHERE race_id  = ?
                 AND bet_type = ?
                 AND combo    = ?
              """,
              (race_id, bet_type, combo) )

    return row[0] if row else None

# ------------------------------------------------------------
def _payout(odds) -> int|None:

    if odds is None:
        return None
    return int(odds * 10) * 10

# ------------------------------------------------------------
def _build_combo_sets(finish:dict) -> list[dict]:

    r1_list = finish.get(1, [])
    r2_list = finish.get(2, [])
    r3_list = finish.get(3, [])

    # --- 3T ---
    three_t = []
    for a in r1_list:
        for b in r2_list:
            for c in r3_list:
                three_t.append(_combo(a, b, c))

    # --- 3F ---
    three_f = sorted({_combo(*sorted([a, b, c])) for a in r1_list for b in r2_list for c in r3_list})

    # --- 2T ---
    two_t = list(dict.fromkeys( _combo(a, b) for a in r1_list for b in r2_list))

    # --- 2F ---
    two_f = sorted({_combo(*sorted([a, b])) for a in r1_list for b in r2_list})

    # --- TT ---
    tt = sorted(r1_list)

    # --- FF ---
    ff = sorted(set(r1_list) | set(r2_list))

    # --- KK ---
    kk = sorted( {_combo(*sorted([a, b])) for a in r1_list for b in r2_list} |
                 {_combo(*sorted([a, c])) for a in r1_list for c in r3_list} |
                 {_combo(*sorted([b, c])) for b in r2_list for c in r3_list}   )

    n = max(len(three_t), len(tt), 1)

    def _get(lst, i, none_val=9):
        return lst[i] if i < len(lst) else none_val

    sets = []
    for i in range(n):
        label = "normal" if i == 0 else f"tie_{i}"

        c3T  = _get(three_t, i, 0) if three_t else 0
        c3F  = _get(three_f, i, 9) if three_f else 0
        c2T  = _get(two_t,   i, 9) if two_t   else 0
        c2F  = _get(two_f,   i, 9) if two_f   else 0
        cTT  = _get(tt,      i, 9) if tt      else 0
        cFF1 = _get(ff,      0, 9)
        cFF2 = _get(ff,      1, 9)
        cKK1 = _get(kk,      0, 9) if kk      else 0
        cKK2 = _get(kk,      1, 9) if kk      else 0
        cKK3 = _get(kk,      2, 9) if kk      else 0

        if i > 0:
            if len(three_f) <= 1: c3F = 9
            if len(two_f)   <= 1: c2F = 9
            cFF1 = cFF2 = 9
            if len(kk) <= 2: cKK1 = cKK2 = cKK3 = 9

        sets.append( { "label": label,
                         "c3T": c3T,   "c3F": c3F,   "c2T": c2T,   "c2F": c2F,   "cTT": cTT,
                        "cFF1": cFF1, "cFF2": cFF2, "cKK1": cKK1, "cKK2": cKK2, "cKK3": cKK3, } )

    return sets

# ------------------------------------------------------------
def upsert_payouts(d_iso:str, venue_id:int, race_no:int):

    race_id = build_ids(d_iso, venue_id, race_no)
    finish  = _get_finish_frames(race_id)

    if not finish:
        return

    r1   = finish.get(1, [])
    r2   = finish.get(2, [])
    r3   = finish.get(3, [])
    has3 = bool(r1 and r2 and r3)
    has2 = bool(r1 and r2)
    has1 = bool(r1)

    combo_sets = _build_combo_sets(finish)
    rows       = []

    for s in combo_sets:

        label = s["label"]
        c3T   = s["c3T"]  ;c3F  = s["c3F"]
        c2T   = s["c2T"]  ;c2F  = s["c2F"]
        cTT   = s["cTT"]
        cFF1  = s["cFF1"] ;cFF2 = s["cFF2"]
        cKK1  = s["cKK1"] ;cKK2 = s["cKK2"] ;cKK3 = s["cKK3"]
        #-----------
        def po(bet_type:str, combo:int, valid:bool) -> int | None:

            if not valid or combo in (0, 9):
                return None
            return _payout(_get_odds(race_id, bet_type, combo))
        #-----------
        def is_sp(bet_type:str, combo:int, valid:bool) -> bool:

            if not valid or combo in (0, 9): return False
            return _get_odds(race_id, bet_type, combo) is None
        #-----------
        any_special = any([ is_sp("3T", c3T,  has3), is_sp("3F",  c3F,  has3),
                            is_sp("2T", c2T,  has2), is_sp("2F",  c2F,  has2),
                            is_sp("TT", cTT,  has1),
                            is_sp("FF", cFF1, has1), is_sp("FF",  cFF2, has1),
                            is_sp("KK", cKK1, has3), is_sp("KK",  cKK2, has3),
                            is_sp("KK", cKK3, has3),                           ])

        if any_special:
            rows.append({ "label":"special",
                            "c3T":c3T  if is_sp("3T", c3T,  has3) else 9,
                            "c3F":c3F  if is_sp("3F", c3F,  has3) else 9,
                            "c2T":c2T  if is_sp("2T", c2T,  has2) else 9,
                            "c2F":c2F  if is_sp("2F", c2F,  has2) else 9,
                            "cTT":cTT  if is_sp("TT", cTT,  has1) else 9,
                           "cFF1":cFF1 if is_sp("FF", cFF1, has1) else 9,
                           "cFF2":cFF2 if is_sp("FF", cFF2, has1) else 9,
                           "cKK1":cKK1 if is_sp("KK", cKK1, has3) else 9,
                           "cKK2":cKK2 if is_sp("KK", cKK2, has3) else 9,
                           "cKK3":cKK3 if is_sp("KK", cKK3, has3) else 9,
                            "p3T":70   if is_sp("3T", c3T,  has3) else None,
                            "p3F":70   if is_sp("3F", c3F,  has3) else None,
                            "p2T":70   if is_sp("2T", c2T,  has2) else None,
                            "p2F":70   if is_sp("2F", c2F,  has2) else None,
                            "pTT":70   if is_sp("TT", cTT,  has1) else None,
                           "pFF1":70   if is_sp("FF", cFF1, has1) else None,
                           "pFF2":70   if is_sp("FF", cFF2, has1) else None,
                           "pKK1":70   if is_sp("KK", cKK1, has3) else None,
                           "pKK2":70   if is_sp("KK", cKK2, has3) else None,
                           "pKK3":70   if is_sp("KK", cKK3, has3) else None, })

        rows.append({ "label":label,
                        "c3T":c3T,   "c3F":c3F,   "c2T":c2T,   "c2F":c2F,   "cTT":cTT,
                       "cFF1":cFF1, "cFF2":cFF2, "cKK1":cKK1, "cKK2":cKK2, "cKK3":cKK3,
                        "p3T":po("3T", c3T,  has3),  "p3F":po("3F", c3F,  has3),
                        "p2T":po("2T", c2T,  has2),  "p2F":po("2F", c2F,  has2),
                        "pTT":po("TT", cTT,  has1),
                       "pFF1":po("FF", cFF1, has1), "pFF2":po("FF", cFF2, has1),
                       "pKK1":po("KK", cKK1, has3), "pKK2":po("KK", cKK2, has3),
                       "pKK3":po("KK", cKK3, has3),                                     })

    sql = """
            INSERT INTO Payouts( race_id, date, venue_id, race_no, status,
                                 combo_3T,   combo_3F,   combo_2T,   combo_2F,   combo_TT,
                                 combo_FF1,  combo_FF2,  combo_KK1,  combo_KK2,  combo_KK3,
                                 payout_3T,  payout_3F,  payout_2T,  payout_2F,  payout_TT,
                                 payout_FF1, payout_FF2, payout_KK1, payout_KK2, payout_KK3 )

            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

       ON CONFLICT(race_id, status)
                DO UPDATE SET combo_3T   = excluded.combo_3T,
                              combo_3F   = excluded.combo_3F,
                              combo_2T   = excluded.combo_2T,
                              combo_2F   = excluded.combo_2F,
                              combo_TT   = excluded.combo_TT,
                              combo_FF1  = excluded.combo_FF1,
                              combo_FF2  = excluded.combo_FF2,
                              combo_KK1  = excluded.combo_KK1,
                              combo_KK2  = excluded.combo_KK2,
                              combo_KK3  = excluded.combo_KK3,
                              payout_3T  = excluded.payout_3T,
                              payout_3F  = excluded.payout_3F,
                              payout_2T  = excluded.payout_2T,
                              payout_2F  = excluded.payout_2F,
                              payout_TT  = excluded.payout_TT,
                              payout_FF1 = excluded.payout_FF1,
                              payout_FF2 = excluded.payout_FF2,
                              payout_KK1 = excluded.payout_KK1,
                              payout_KK2 = excluded.payout_KK2,
                              payout_KK3 = excluded.payout_KK3
          """

    params = [ ( race_id,  d_iso, venue_id, race_no,
                 r["label"],
                 r["c3T"],  r["c3F"],  r["c2T"],  r["c2F"],  r["cTT"],
                 r["cFF1"], r["cFF2"], r["cKK1"], r["cKK2"], r["cKK3"],
                 r["p3T"],  r["p3F"],  r["p2T"],  r["p2F"],  r["pTT"],
                 r["pFF1"], r["pFF2"], r["pKK1"], r["pKK2"], r["pKK3"], ) for r in rows ]

    dal.executemany(sql, params)

# ------------------------------------------------------------
def build_ids(d_iso:str, venue_id:int, race_no:int):

    _date    = dt.strptime(d_iso, "%Y-%m-%d")
    ymd      = _date.strftime("%y%m%d")
    race_id  = int(f"{ymd}{venue_id:02d}{race_no:02d}")

    return race_id

#=====================================================================
def main(argv=None):

    p = argparse.ArgumentParser()
    p.add_argument("--date",  required=True, help="対象日(yyyy-mm-dd)")
    p.add_argument("--venue", required=True, help="対象開催場(int)")
    p.add_argument("--race",  required=True, help="対象レース(int)")
    p.add_argument("--overwrite", action="store_true",  help="上書きﾓｰﾄﾞ")
    args = p.parse_args(argv)

    upsert_payouts(args.date, int(args.venue), int(args.race))

#=====================================================================
if __name__ == "__main__":
    sys.exit(main())
