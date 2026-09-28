# -*- coding: utf-8 -*-
# C:\boatrace\UI\Subprocess\get_results_today.py

import Dal as dal
import argparse, re, sqlite3, sys, warnings, unicodedata, random, time
from datetime  import datetime as dt
from pathlib   import Path
from bs4       import BeautifulSoup, FeatureNotFound, XMLParsedAsHTMLWarning
from curl_cffi import requests

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
# ------------------------------------------------------------
BASE_DIR = Path(r"C:\boatrace")
DB_PATH  = BASE_DIR / "boatrace.db"
URL_TPL  = "https://www.boatrace.jp/owpc/pc/race/raceresult?rno={rno}&jcd={jcd:02d}&hd={hd}"
FW2H     = str.maketrans("０１２３４５６７８９", "0123456789")

HEADERS = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Connection": "keep-alive",                  }

# ----------------------------
def yyyymmdd(s: str) -> str:

    return s.replace("-", "")
# ----------------------------------------------------------
def build_ids(d_iso:str, venue_id:int, race_no:int, frame_no:int):

    _date = dt.strptime(d_iso, "%Y-%m-%d")
    ymd   = _date.strftime("%y%m%d")
    race_id  = int(f"{ymd}{venue_id:02d}{race_no:02d}")
    entry_id = int(f"{ymd}{venue_id:02d}{race_no:02d}{frame_no}")

    return race_id, entry_id

# ----------------------------------------------------------
def fetch_program(d_iso:str, venue_id:int, race_no:int):

    rows = dal.fetch_all("""
               SELECT frame_no, player_id, motor_no, boat_no
                 FROM Race_programs
                WHERE     date=?
                  AND venue_id=?
                  AND  race_no=?
             ORDER BY frame_no
               """,
               (d_iso, venue_id, race_no))

    return {r[0]:{"player_id":r[1], "motor_no":r[2], "boat_no":r[3]} for r in rows}

# ------------------------------------------------------------
def fetch_venues(d_iso:str):

    rows = dal.fetch_all("""
               SELECT DISTINCT venue_id
                 FROM Race_programs
                WHERE    date=?
                  AND race_no=?
           """,
           (d_iso, 1))

    return tuple(row[0] for row in rows)

# ------------------------------------------------------------
def fetch_cancelled(d_iso:str, venue_id:int, race_no:int):

    row = dal.fetch_one("""
              SELECT status
                FROM Races
               WHERE     date=?
                 AND venue_id=?
                 AND  race_no=?
              """,
              (d_iso, venue_id, race_no))

    out = True if row and row[0] == 'cancelled' else False

    return out

# ----------------------------------------------------------
def fetch_race_meta(d_iso:str, venue_id:int, race_no:int):

    row = dal.fetch_one("""
              SELECT MIN(series_title) AS series_title,
                     MIN(grade)        AS grade,
                     MIN(day_no)       AS day_no,
                     MIN(race_title)   AS race_title
                FROM Race_programs
               WHERE     date=?
                 AND venue_id=?
                 AND  race_no=?
              """,
              (d_iso, venue_id, race_no))

    if not row: return None

    return {"series_title": row[0],
                   "grade": row[1],
                  "day_no": row[2],
              "race_title": row[3], }

# ------------ (周回短縮/安定板使用)取得 -------------------
def parse_distance_and_stabilizer(soup:BeautifulSoup) -> tuple[int | None, int]:

    stabilizer = 1 if any( "安定板使用" in el.get_text(strip=True)
                           for el in soup.select("span.label2.is-type1")  ) else 0

    distance = None
    h3       = soup.select_one("h3.title16_titleDetail__add2020")

    if h3:
        t = h3.get_text(" ", strip=True)
        if "1200m" in t:
            distance = 1200
        elif "1800m" in t:
            distance = 1800

    return distance, stabilizer

# -------------- 気象情報取得(結果ページ) ------------------
def parse_weather(soup:BeautifulSoup) -> dict:

    weather = None     # 天気
    node = soup.select_one(".weather1 .weather1_body .weather1_bodyUnit.is-weather .weather1_bodyUnitLabel .weather1_bodyUnitLabelTitle")
    if node: weather = node.get_text(strip=True) or None

    wind_spd = None    # 風速
    node = soup.select_one(".weather1 .weather1_body .weather1_bodyUnit.is-wind .weather1_bodyUnitLabel .weather1_bodyUnitLabelData")
    if node:
        m = re.search(r"(\d+)", node.get_text(strip=True))
        wind_spd = int(m.group(1)) if m else None

    wind_dir = None    # 風向
    node = soup.select_one(".weather1 .weather1_body .weather1_bodyUnit.is-windDirection .weather1_bodyUnitImage")
    if node:
        cls      = " ".join(node.get("class") or [])
        m        = re.search(r"is-wind(\d+)", cls)
        wind_dir = m.group(1) if m else None

    wave_hgt = None    # 波高
    for cand in soup.select(".weather1 .weather1_body .weather1_bodyUnit .weather1_bodyUnitLabel .weather1_bodyUnitLabelData"):
        m = re.search(r"(\d+)\s*cm", cand.get_text(strip=True))
        if m:
            wave_hgt = int(m.group(1))
            break

    return {  "weather":  weather,
             "wind_dir": wind_dir,
             "wind_spd": wind_spd,
             "wave_hgt": wave_hgt, }

# ------------- ﾚｰｽ結果取得(着順テーブル) ------------------
def parse_finish_table(soup:BeautifulSoup):

    out    = {}
    target = None

    for tbl in soup.select("div.grid.is-type2 div.grid_unit div.table1 table"):
        thead = tbl.find("thead")
        if not thead: continue
        heads = [th.get_text(strip=True) for th in thead.select("th")]
        if {"着", "枠", "ボートレーサー", "レースタイム"}.issubset(set(heads)):
            target = tbl
            break

    if not target: return out
    # --------------
    def fault_from_token(tok: str):

        if tok in ("転", "落", "エ", "不", "沈", "失"):  return "S", 1
        if tok == "妨":                                  return "S", 2
        if tok in ("F", "Ｆ", "L", "Ｌ"):                return tok, 1
        if tok == "欠":                                  return "K", 0

        return "N", None
    # --------------
    for tb in target.find_all("tbody", recursive=False):

        tr = tb.find("tr")
        if not tr: continue

        tds = tr.find_all("td", recursive=False)
        if len(tds) < 4: continue

        # 1列目: 着順セル（is-fs14）
        rk_cell     = tds[0].select_one(".is-fs14")
        rk_txt      = ( rk_cell.get_text(strip=True) if rk_cell else
                         tds[0].get_text(strip=True)                 ).translate(FW2H)
        finish_rank = None
        fault_code, fault_level = "N", None

        if rk_txt.isdigit(): finish_rank = int(rk_txt)
        elif rk_txt == "＿": finish_rank = 0
        else:                fault_code, fault_level = fault_from_token(rk_txt)

        # 2列目: 枠番（クラス is-boatColorN 優先）
        frame_no = None
        cls2     = " ".join(tds[1].get("class") or [])
        m_fr     = re.search(r"is-boatColor(\d)", cls2)

        if m_fr: frame_no = int(m_fr.group(1))
        else:
            fr_txt = (tds[1].get_text(strip=True) or "").translate(FW2H)
            if fr_txt.isdigit(): frame_no = int(fr_txt)

        if not frame_no: continue

        # 3列目: 登番
        pid_span  = tds[2].select_one("span.is-fs12")
        player_id = None

        if pid_span:
            pid_txt = pid_span.get_text(strip=True).translate(FW2H)
            if pid_txt.isdigit(): player_id = int(pid_txt)

        # 4列目: レースタイム
        race_time     = tds[3].get_text(strip=True) or None
        out[frame_no] = {"finish_rank": finish_rank,
                           "player_id":   player_id,
                           "race_time":   race_time,
                          "fault_code":  fault_code,
                         "fault_level": fault_level,  }

    return out

# ----------- スタート情報(slit_ADJ/course)取得 ------------
def parse_start_info(soup:BeautifulSoup):

    out      = {}
    rows     = soup.select("div.table1_boatImage1")
    course   = 1

    for r in rows:
        cnode    = r.select_one(".table1_boatImage1Number")
        frame_no = int(cnode.get_text(strip=True).translate(FW2H)) if cnode else None
        bnode    = r.select_one(".table1_boatImage1Boat")
        slit     = None

        if bnode:
            style = bnode.get("style", "")
            m     = re.search(r"left:\s*(\d+)\s*%", style)
            if m:
                pct  = int(m.group(1))
                slit = round((65 - pct) * 0.01, 2)

        out[frame_no] = {"course": course, "slit_ADJ": slit}
        course       += 1

        if course > 6: break

    return out

# ----------------------------------------------------------
def parse_win_move(soup:BeautifulSoup) -> str | None:

    for tbl in soup.select("div.table1 > table"):
        thead = tbl.find("thead")
        if not thead: continue

        th    = thead.find("th")
        if not th: continue

        if th.get_text(strip=True) == "決まり手":
            td = tbl.find("tbody")
            if td:
                cell = td.find("td")
                if cell:
                    txt = cell.get_text(strip=True)
                    return txt or None

    return None

# ----------------------------------------------------------
def insert_race(d_iso:str, venue_id:int, race_no:int, race_meta:dict):

    meta = fetch_race_meta(d_iso, venue_id, race_no)
    if not meta: return False

    race_id, _ = build_ids(d_iso, venue_id, race_no, 1)

    sql = """
            INSERT
              INTO Races
                 ( race_id,  date,       venue_id,   series_title, grade,   day_no,
                   race_no,  race_title, is_final,   distance,     weather, wind_dir,
                   wind_spd, wave_hgt,   stabilizer, status                           )
            VALUES
                 (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, 'held')
       ON CONFLICT(race_id)
     DO UPDATE SET series_title = excluded.series_title,
                   grade        = excluded.grade,
                   day_no       = excluded.day_no,
                   race_title   = excluded.race_title,
                   distance     = COALESCE(excluded.distance,  Races.distance),
                   weather      = COALESCE(excluded.weather,   Races.weather),
                   wind_dir     = COALESCE(excluded.wind_dir,  Races.wind_dir),
                   wind_spd     = COALESCE(excluded.wind_spd,  Races.wind_spd),
                   wave_hgt     = COALESCE(excluded.wave_hgt,  Races.wave_hgt),
                   stabilizer   = COALESCE(excluded.stabilizer,Races.stabilizer),
                   is_final     = 0,
                   status       = 'held'
          """

    params = ( race_id, d_iso, venue_id,
               meta["series_title"], meta["grade"], meta["day_no"],
               race_no, meta["race_title"],
               (race_meta.get("distance") or 1600),
               race_meta.get("weather"),
               race_meta.get("wind_dir"),
               race_meta.get("wind_spd"),
               race_meta.get("wave_hgt"),
               race_meta.get("stabilizer"),                          )

    return dal.execute(sql, params)

# ------------------------------------------------------------
def upsert_results(d_iso:str, venue_id:int, race_no:int, prog, fin, stinfo, winmv:str|None):

    sql = """
            INSERT
              INTO Race_entries
                 ( race_id,    entry_id,    race_no,   venue_id, date,
                   frame_no,   player_id,   course,    win_move, finish_rank,
                   fault_code, fault_level, motor_no,  boat_no,
                   slit_ADJ,   race_time,   violation                         )

            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
       ON CONFLICT(entry_id)
     DO UPDATE SET course      = COALESCE(excluded.course, course),
                   finish_rank = COALESCE(excluded.finish_rank, finish_rank),
                   fault_code  = COALESCE(excluded.fault_code, fault_code),
                   slit_ADJ    = COALESCE(excluded.slit_ADJ, slit_ADJ),
                   race_time   = COALESCE(excluded.race_time, race_time)
          """
    params       = []
    winner_frame = None

    for fr, v in fin.items():
        if v.get("finish_rank") == 1:
            winner_frame = fr
            break

    for fr in range(1, 7):
        base = prog.get(fr)
        if not base: continue

        race_id, entry_id = build_ids(d_iso, venue_id, race_no, fr)
        player_id   = base["player_id"]
        motor_no    = base["motor_no"]
        boat_no     = base["boat_no"]
        course      = stinfo.get(fr, {}).get("course")
        win_move    = winmv if (winner_frame is not None and fr == winner_frame) else None
        finish_rank = fin.get(fr, {}).get("finish_rank")
        fault_code  = unicodedata.normalize('NFKC', fin.get(fr, {}).get("fault_code"))
        fault_level = fin.get(fr, {}).get("fault_level")
        slit_adj    = stinfo.get(fr, {}).get("slit_ADJ")
        race_time   = fin.get(fr, {}).get("race_time")
        violation   = 0

        if not finish_rank and not fault_code:
            print("[WARN] rank fault 取得 error")
            return

        params.append((
            race_id,   entry_id, race_no,    venue_id,    d_iso,      fr,
            player_id, course,   win_move,   finish_rank, fault_code, fault_level,
            motor_no,  boat_no, slit_adj,    race_time,  violation                  ))

    return dal.executemany(sql, params)

# ------------------------------------------------------------
# combo整数を生成するヘルパー
def _combo(*frames) -> int:
    return int("".join(str(f) for f in frames))

# ------------------------------------------------------------
# Race_entriesからfinish_rank順に枠番を取得
# 返値: {1: [frame_no, ...], 2: [...], ...}  (同着は同rank内に複数)
def _get_finish_frames(race_id: int) -> dict:

    rows = dal.fetch_all("""
               SELECT finish_rank, frame_no, fault_code
                 FROM Race_entries
                WHERE race_id = ?
                  AND finish_rank IS NOT NULL
             ORDER BY finish_rank, frame_no
               """, (race_id,))

    result = {}
    for rk, fr, fc in rows:
        result.setdefault(rk, []).append((fr, fc))

    return result

# ------------------------------------------------------------
# Oddsテーブルからcomboに対応するoddsを取得
def _get_odds(race_id: int, bet_type: str, combo: int):

    row = dal.fetch_one("""
              SELECT odds
                FROM Odds
               WHERE race_id  = ?
                 AND bet_type = ?
                 AND combo    = ?
              """, (race_id, bet_type, combo))

    return row[0] if row else None

# ------------------------------------------------------------
# 払い戻し金額を計算 (odds -> 100円単位で切り捨て、最低70円)
def _payout(odds) -> int | None:

    if odds is None:
        return None

    return max(70, int(odds * 10) * 10)

# ------------------------------------------------------------
# 同着を含む全パターンのcomboセットを生成
# 返値: [ {bet_type: combo, ...}, ... ]  len=1 (normal) or 2 (tie1) or 3 (tie2)
def _build_combo_sets(finish: dict) -> list[dict]:

    # 着順ごとの枠番リスト取得 (fault_code不問: 返還判定に必要)
    r1_list = [fr for fr, _ in finish.get(1, [])]
    r2_list = [fr for fr, _ in finish.get(2, [])]
    r3_list = [fr for fr, _ in finish.get(3, [])]

    # fault_codeをframe_noで引けるようにまとめる
    fault_map = {}
    for rank_frames in finish.values():
        for fr, fc in rank_frames:
            fault_map[fr] = fc

    INVALID = {"F", "L", "K"}

    def is_return(combo_int: int) -> bool:
        """comboに含まれる艇番にF/L/Kがあれば返還 → payout=70"""
        for ch in str(combo_int):
            if ch.isdigit() and fault_map.get(int(ch)) in INVALID:
                return True
        return False

    # 同着パターン: 各ランクが複数艇あれば順列展開
    # 1着: r1_list, 2着: r2_list, 3着: r3_list
    # 賭け式ごとに若番基準の正規順(normal)と追加パターン(tie1,tie2)を生成

    sets = []  # list of dict {bet_type -> combo_int or 0 or 9}

    # --- 3T ---
    three_t = []
    for a in r1_list:
        for b in r2_list:
            for c in r3_list:
                three_t.append(_combo(a, b, c))

    # --- 3F ---
    three_f_set = set()
    for a in r1_list:
        for b in r2_list:
            for c in r3_list:
                three_f_set.add(_combo(*sorted([a, b, c])))
    three_f = sorted(three_f_set)

    # --- 2T ---
    two_t = []
    for a in r1_list:
        for b in r2_list:
            two_t.append(_combo(a, b))
    two_t = list(dict.fromkeys(two_t))  # 順序保持で重複除去

    # --- 2F ---
    two_f_set = set()
    for a in r1_list:
        for b in r2_list:
            two_f_set.add(_combo(*sorted([a, b])))
    two_f = sorted(two_f_set)

    # --- TT (単勝: 1着のみ) ---
    tt = sorted(r1_list)

    # --- FF (複勝: 2着以内) ---
    ff_set = set(r1_list) | set(r2_list)
    ff     = sorted(ff_set)

    # --- KK (拡連複: 1着-2着, 1着-3着, 2着-3着 の各ペア昇順) ---
    kk_set = set()
    for a in r1_list:
        for b in r2_list:
            kk_set.add(_combo(*sorted([a, b])))
    for a in r1_list:
        for c in r3_list:
            kk_set.add(_combo(*sorted([a, c])))
    for b in r2_list:
        for c in r3_list:
            kk_set.add(_combo(*sorted([b, c])))
    kk = sorted(kk_set)

    # --- パターン数 (同着による最大分岐) ---
    n = max(len(three_t), len(tt))  # TT/3Tの分岐数が基本

    def _get(lst, i, none_val=9):
        return lst[i] if i < len(lst) else none_val

    for i in range(max(n, 1)):

        label = "normal" if i == 0 else f"tie{i}"

        c3T  = _get(three_t, i, 0) if three_t  else 0
        c3F  = _get(three_f, i, 9) if three_f  else 0
        c2T  = _get(two_t,   i, 9) if two_t    else 0
        c2F  = _get(two_f,   i, 9) if two_f    else 0
        cTT  = _get(tt,      i, 9) if tt        else 0
        cFF1 = _get(ff,      0, 9)              # FF は同着によらず固定2枠
        cFF2 = _get(ff,      1, 9)
        cKK1 = _get(kk,      0, 9) if kk       else 0
        cKK2 = _get(kk,      1, 9) if kk       else 0
        cKK3 = _get(kk,      2, 9) if kk       else 0

        # tie行ではKK/3F/2F/FFの追加パターンが存在しない → 9
        if i > 0:
            if len(three_f) <= 1: c3F  = 9
            if len(two_f)   <= 1: c2F  = 9
            if len(kk)      <= 2: cKK1 = cKK2 = cKK3 = 9  # tie行にKKパターン無し
            cFF1 = cFF2 = 9

        sets.append({
            "label": label,
            "c3T":   c3T,  "c3F":  c3F,
            "c2T":   c2T,  "c2F":  c2F,
            "cTT":   cTT,
            "cFF1":  cFF1, "cFF2": cFF2,
            "cKK1":  cKK1, "cKK2": cKK2, "cKK3": cKK3,
            "fault_map": fault_map,
            "is_return": is_return,
        })

    return sets

# ------------------------------------------------------------
def upsert_payouts(d_iso: str, venue_id: int, race_no: int, race_id: int):

    finish = _get_finish_frames(race_id)

    if not finish:
        return  # 結果未取得

    # 不成立チェック: 1着・2着・3着それぞれの有効艇数
    r1 = finish.get(1, [])
    r2 = finish.get(2, [])
    r3 = finish.get(3, [])

    has3 = len(r1) > 0 and len(r2) > 0 and len(r3) > 0
    has2 = len(r1) > 0 and len(r2) > 0
    has1 = len(r1) > 0

    combo_sets = _build_combo_sets(finish)

    rows = []

    for s in combo_sets:

        label       = s["label"]
        is_return   = s["is_return"]

        def po(bet_type: str, combo: int, valid: bool) -> int | None:
            if not valid or combo in (0, 9):
                return None
            odds = _get_odds(race_id, bet_type, combo)
            if odds is None:
                return 70   # 特払い
            if is_return(combo):
                return 70   # 返還
            return _payout(odds)

        # special判定: 通常comboのoddがNoneの賭け式があるか
        def is_special(bet_type: str, combo: int, valid: bool) -> bool:
            if not valid or combo in (0, 9): return False
            return _get_odds(race_id, bet_type, combo) is None

        c3T  = s["c3T"];  c3F  = s["c3F"]
        c2T  = s["c2T"];  c2F  = s["c2F"]
        cTT  = s["cTT"]
        cFF1 = s["cFF1"]; cFF2 = s["cFF2"]
        cKK1 = s["cKK1"]; cKK2 = s["cKK2"]; cKK3 = s["cKK3"]

        any_special = any([
            is_special("3T",  c3T,  has3),
            is_special("3F",  c3F,  has3),
            is_special("2T",  c2T,  has2),
            is_special("2F",  c2F,  has2),
            is_special("TT",  cTT,  has1),
            is_special("FF",  cFF1, has1),
            is_special("FF",  cFF2, has1),
            is_special("KK",  cKK1, has3),
            is_special("KK",  cKK2, has3),
            is_special("KK",  cKK3, has3),
        ])

        if any_special:
            # special行: 特払いのcomboのみpayout=70, 他は9/None
            spec_row = {
                "label":     "special",
                "c3T":  c3T  if is_special("3T", c3T,  has3) else 9,
                "c3F":  c3F  if is_special("3F", c3F,  has3) else 9,
                "c2T":  c2T  if is_special("2T", c2T,  has2) else 9,
                "c2F":  c2F  if is_special("2F", c2F,  has2) else 9,
                "cTT":  cTT  if is_special("TT", cTT,  has1) else 9,
                "cFF1": cFF1 if is_special("FF", cFF1, has1) else 9,
                "cFF2": cFF2 if is_special("FF", cFF2, has1) else 9,
                "cKK1": cKK1 if is_special("KK", cKK1, has3) else 9,
                "cKK2": cKK2 if is_special("KK", cKK2, has3) else 9,
                "cKK3": cKK3 if is_special("KK", cKK3, has3) else 9,
                "p3T":  70   if is_special("3T", c3T,  has3) else None,
                "p3F":  70   if is_special("3F", c3F,  has3) else None,
                "p2T":  70   if is_special("2T", c2T,  has2) else None,
                "p2F":  70   if is_special("2F", c2F,  has2) else None,
                "pTT":  70   if is_special("TT", cTT,  has1) else None,
                "pFF1": 70   if is_special("FF", cFF1, has1) else None,
                "pFF2": 70   if is_special("FF", cFF2, has1) else None,
                "pKK1": 70   if is_special("KK", cKK1, has3) else None,
                "pKK2": 70   if is_special("KK", cKK2, has3) else None,
                "pKK3": 70   if is_special("KK", cKK3, has3) else None,
            }
            rows.append(spec_row)

        rows.append({
            "label": label,
            "c3T": c3T,  "c3F": c3F,
            "c2T": c2T,  "c2F": c2F,
            "cTT": cTT,
            "cFF1": cFF1, "cFF2": cFF2,
            "cKK1": cKK1, "cKK2": cKK2, "cKK3": cKK3,
            "p3T":  po("3T", c3T,  has3),
            "p3F":  po("3F", c3F,  has3),
            "p2T":  po("2T", c2T,  has2),
            "p2F":  po("2F", c2F,  has2),
            "pTT":  po("TT", cTT,  has1),
            "pFF1": po("FF", cFF1, has1),
            "pFF2": po("FF", cFF2, has1),
            "pKK1": po("KK", cKK1, has3),
            "pKK2": po("KK", cKK2, has3),
            "pKK3": po("KK", cKK3, has3),
        })

    sql = """
            INSERT INTO Payouts
                      ( race_id,   date,    venue_id,
                        status,
                        combo_3T,  combo_3F, combo_2T, combo_2F, combo_TT,
                        combo_FF1, combo_FF2,
                        combo_KK1, combo_KK2, combo_KK3,
                        payout_3T, payout_3F, payout_2T, payout_2F, payout_TT,
                        payout_FF1, payout_FF2,
                        payout_KK1, payout_KK2, payout_KK3 )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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

    params = [
        ( race_id,  d_iso,  venue_id,
          r["label"],
          r["c3T"],  r["c3F"],  r["c2T"],  r["c2F"],  r["cTT"],
          r["cFF1"], r["cFF2"],
          r["cKK1"], r["cKK2"], r["cKK3"],
          r["p3T"],  r["p3F"],  r["p2T"],  r["p2F"],  r["pTT"],
          r["pFF1"], r["pFF2"],
          r["pKK1"], r["pKK2"], r["pKK3"],  )
        for r in rows
    ]

    dal.executemany(sql, params)

# ------------------------------------------------------------
def main():

    ap = argparse.ArgumentParser()
    ap.add_argument("--date",  required=True, help="YYYY-MM-DD")
    ap.add_argument("--venue",                type=int)
    ap.add_argument("--race",                 type=int)
    ap.add_argument("--ALL_venue", action="store_true")
    ap.add_argument("--ALL_race",  action="store_true")

    args  = ap.parse_args()
    hd   = yyyymmdd(args.date)

    if not args.venue and not args.ALL_venue:
        print(f"input 'venue_id' or select 「--ALL_venue」") ;return
    if not args.race  and not args.ALL_race:
        print(f"input 'race_no'  or select 「--ALL_race」")  ;return

    target_v = fetch_venues(args.date) if args.ALL_venue else [args.venue]

    for jcd in target_v:
        target_r   = list(range(1, 13)) if args.ALL_race else [args.race]
        r_no1_skip = False

        if args.ALL_race:
            for r in range(1,13):
                if fetch_cancelled(args.date, jcd, r):
                    r_no1_skip =True
                    break

        for rno in target_r:
            if r_no1_skip and rno == 1: continue
            if fetch_cancelled(args.date, jcd, rno):
                if not args.ALL_race:
                    print(f"[OK] {rno}R is cancelled. skip import_Result.")
                    return 0
                print(f"[OK] jcd={jcd}  {rno}R is cancelled")
                continue


            url = URL_TPL.format(rno=rno, jcd=jcd, hd=hd)

            with requests.Session(impersonate="firefox") as session:
                session.headers.update(HEADERS)

                try:
                    time.sleep(random.uniform(1.6,3.2))
                    res = session.get(url, timeout=15)
                    res.raise_for_status()
                except Exception as e:
                    print(f"[ERR] GET failed: {e}")
                    return 1

            soup             = BeautifulSoup(res.text,"lxml")
            fin              = parse_finish_table(soup)
            stinfo           = parse_start_info(soup)
            winmv            = parse_win_move(soup)
            wx               = parse_weather(soup)
            dist, stabilizer = parse_distance_and_stabilizer(soup)

            race_meta               = dict(wx)
            race_meta["distance"]   = dist
            race_meta["stabilizer"] = stabilizer

            lack = [fr for fr in range(1, 7) if fr not in fin]
            if lack:
                if not args.ALL_race:
                    print(f"page update yet")
                    return 3
                continue

            prog = fetch_program(args.date, jcd, rno)
            if not prog:
                if not args.ALL_race:
                    print("[WARN] Race_programs が未整備です")
                    return 2
                continue

            inserted = insert_race(args.date, jcd, rno, race_meta)
            if not inserted:
                if not args.ALL_race:
                    print("[WARN] Insert Races error")
                    return 2
                continue

            upserted = upsert_results(args.date, jcd, rno, prog, fin, stinfo, winmv)
            if not upserted:
                if not args.ALL_race:
                    print("[WARN] Upsert Race entries error")
                    return 2
                continue

            race_id, _ = build_ids(args.date, jcd, rno, 1)
            upsert_payouts(args.date, jcd, rno, race_id)

            if args.ALL_race: print(f"[JCD={jcd}  {rno} R] done.")

        if args.ALL_race: rno = "1～12"
        print(f"[OK] Insert: {args.date} jcd={jcd} {rno}R")

        if not args.ALL_venue:
            return 0
    return 0

if __name__ == "__main__":
    sys.exit(main())