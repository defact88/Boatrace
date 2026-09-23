# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\ev_scanner.py

import Dal as dal
from datetime import datetime as dt, date
import sqlite3

BET_TYPES_PERSISTED        = ("3T", "3F", "2T", "2F", "KK", "TT", "FF")
FULL_SNAPSHOT_INTERVAL_SEC = 300

#=====================================================================
class ProbabilityProvider:
    """
    ①(予測エンジン)の出力を提供するインターフェース。
      現時点では未実装のため、常に空dictを返す
    ①が完成したら、このクラスを継承した実装に差し替えるだけで
      evaluate_ev 側のコードは変更不要。
    """
    def get_probabilities(self, d:date, venue_id:int, race_no:int, bet_type:str) -> dict:
        """
        戻り値: {(boat1,boat2,boat3 or boat1,boat2):predicted_probability, ...}
        該当データが無ければ空dict
        """
        return {}
#-----------------------------
def _build_race_id(d:date, venue_id:int, race_no:int) -> int:

    ymd = d.strftime("%y%m%d")

    return int(f"{ymd}{venue_id:02d}{race_no:02d}")

#-----------------------------
def _parse_odds_value(raw:str):

    if not raw:       return None, None
    if "欠場" in raw: return None, "K"

    s = raw.replace(" ", "").split("-")

    try:              return float(s[0]), raw
    except Exception: return None, None

#-----------------------------------------------------------
def evaluate_ev( data:dict, d:date, venue_id:int, race_no:int,
                 prob_provider:ProbabilityProvider, ev_threshold=0.0 ):

    """
    data          : scraper_odds.fetch_all_odds()の戻り値(生データ)
    prob_provider : ①の確率供給元
    ev_threshold  : スカラー、または {bet_type:閾値} の辞書
    戻り値        : [(bet_type, key, predicted_prob, odds, ev), ...]
    """

    get_th = ( (lambda bt:ev_threshold.get(bt, 0.0)) if isinstance(ev_threshold, dict)
                                                     else (lambda bt:ev_threshold)     )
    hits   = []

    for bet_type in BET_TYPES_PERSISTED:
        probs = prob_provider.get_probabilities(d, venue_id, race_no, bet_type)
        if not probs: continue   # ①未実装の為常に空

        threshold = get_th(bet_type)

        for key, raw in data.get(bet_type, {}).items():
            odds, raw_odds = _parse_odds_value(raw)
            if not odds: continue

            p = probs.get(key)
            if p is None: continue

            ev = p * odds - 1.0
            if ev >= threshold:
                hits.append((bet_type, key, p, odds, ev))

    return hits

#-----------------------------------------------------------
def insert_odds_snapshot(data:dict, d:date, venue_id:int, race_no:int, hits:list):

    now      = dt.now()
    race_id  = _build_race_id(d, venue_id, race_no)
    hit_keys = {(bt, key) for bt, key, *_ in hits} if hits else set()
    rows     = []

    for bet_type in BET_TYPES_PERSISTED:
        for key, raw in data.get(bet_type, {}).items():

            hit = 1 if (bet_type, key) in hit_keys else 0 # ①未実装の為常に0

            key            = [key] if isinstance(key, int) else list(key)
            b1, b2, b3     = (key + [0, 0])[:3]
            odds, raw_odds = _parse_odds_value(raw)


            rows.append( ( race_id, d.isoformat(), venue_id, race_no, bet_type,
                           b1, b2, b3, odds, raw_odds, hit, now.strftime("%Y-%m-%d %H:%M:%S") ) )

    if not rows: return 0

    cnt = dal.executemany("""
        INSERT INTO Odds( race_id, date, venue_id, race_no, bet_type,
                          boat1, boat2, boat3, odds, raw_odds, hit, captured_at )
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT (race_id, bet_type, boat1, boat2, boat3)
                 DO UPDATE SET odds        = excluded.odds,
                               raw_odds    = excluded.raw_odds,
                               hit         = excluded.hit,
                               captured_at = excluded.captured_at
        """, rows)

    if cnt == 212: return 1
    else:          return 2

