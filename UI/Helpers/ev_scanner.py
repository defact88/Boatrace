# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\ev_scanner.py

from datetime import datetime as dt, date
import sqlite3

BET_TYPES_PERSISTED        = ("3T", "3F", "2T", "KK")
FULL_SNAPSHOT_INTERVAL_SEC = 300

class ProbabilityProvider:
    """
    ①(AI予測エンジン)の出力を提供するインターフェース。
    現時点では未実装のため、常に空dictを返す = evaluate_ev は
    ヒットを一切返さない(EV判定を行わないだけで、オッズ収集自体は動作する)。

    ①が完成したら、このクラスを継承した実装(例: DbProbabilityProvider)
    に差し替えるだけで evaluate_ev 側のコードは変更不要。
    """
    def get_probabilities(self, d:date, venue_id:int, race_no:int, bet_type:str) -> dict:
        """
        戻り値: {(boat1,boat2,boat3 or boat1,boat2): predicted_probability, ...}
        該当データが無ければ空dict
        """
        return {}
#-----------------------------
def _build_race_id(d:date, venue_id:int, race_no:int) -> int:
    ymd = d.strftime("%y%m%d")
    return int(f"{ymd}{venue_id:02d}{race_no:02d}")

#-----------------------------
def _parse_odds_value(raw:str):

    if not raw:       return None, 0
    if "欠場" in raw: return None, 1

    s = raw.replace(" ", "").split("-")

    try:              return float(s[0]), 0
    except Exception: return None, 0

#-----------------------------------------------------------
def evaluate_ev( data:dict, d:date, venue_id:int, race_no:int,
                 prob_provider:ProbabilityProvider, ev_threshold=0.0 ):

    """
    data          : scraper_odds.fetch_all_odds() の戻り値(生データ)
    prob_provider : ①の確率供給元(未実装時はProbabilityProvider()のまま渡してOK)
    ev_threshold  : スカラー、または {bet_type: 閾値} の辞書
                    (賭式ごとに控除率が違うため、将来は辞書で個別指定する想定)

    戻り値: [(bet_type, key, predicted_prob, odds, ev), ...]
    """

    get_th = ( (lambda bt: ev_threshold.get(bt, 0.0)) if isinstance(ev_threshold, dict)
                                                      else (lambda bt:ev_threshold)     )
    hits   = []

    for bet_type in BET_TYPES_PERSISTED:
        probs = prob_provider.get_probabilities(d, venue_id, race_no, bet_type)
        if not probs: continue   # ①未接続、またはこのレースの予測が未生成

        threshold = get_th(bet_type)

        for key, raw in data.get(bet_type, {}).items():
            odds_val, is_absent = _parse_odds_value(raw)
            if is_absent or not odds_val: continue

            p = probs.get(key)
            if p is None: continue

            ev = p * odds_val - 1.0
            if ev >= threshold:
                hits.append((bet_type, key, p, odds_val, ev))

    return hits

#-----------------------------------------------------------
def persist_odds_snapshot( conn:sqlite3.Connection, data:dict, d:date, venue_id:int,
                           race_no:int, hits:list, is_final:bool, do_full:bool ):

    now      = dt.now()
    race_id  = _build_race_id(d, venue_id, race_no)
    hit_keys = {(bt, key) for bt, key, *_ in hits} if hits else set()
    rows     = []

    for bet_type in BET_TYPES_PERSISTED:
        for key, raw in data.get(bet_type, {}).items():

            should_write = is_final or do_full or (bet_type, key) in hit_keys
            if not should_write: continue

            b1, b2, b3       = (list(key) + [None, None])[:3]
            odds_val, is_abs = _parse_odds_value(raw)

            rows.append( ( race_id, d.isoformat(), venue_id, race_no, bet_type,
                           b1, b2, b3, odds_val, raw, is_abs,
                           now.strftime("%Y-%m-%d %H:%M:%S"), 1 if is_final else 0 ) )

    if not rows: return 0

    with conn:
        conn.executemany("""
            INSERT INTO Odds_snapshots( race_id, date, venue_id, race_no, bet_type,
                                        boat1, boat2, boat3, odds, raw_odds, is_absent,
                                        captured_at, is_final                          )
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT (date, venue_id, race_no, bet_type, boat1, boat2, boat3, captured_at)
            DO NOTHING
            """, rows)

    return len(rows)