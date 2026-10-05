# -*- coding: utf-8 -*-
# C:\boatrace\Import\parse_and_upsert.py

from __future__ import annotations
from typing     import Dict, Set, List, Tuple
import re, sqlite3, math

import Dal as dal

DB = r"C:\boatrace\boatrace.db"

TXT2DEG = {    "東": 0,   "南": 90,   "西":180,   "北":270,
             "南東":45, "南西":135, "北西":225, "北東":315, "無風": None,
           "東南東":22.5,  "南南東":67.5,  "南南西":112.5, "西南西":157.5, 
           "西北西":202.5, "北北西":247.5, "北北東":292.5, "東北東":337.5, } 

#=====================================================================
RE_DATE_LINE = re.compile(r"^\s*第\s*(\d+)日.*?(\d{4})/\s*(\d{1,2})/\s*(\d{1,2}).*$", re.M)
RE_RACE_HEAD = re.compile(
    r"^\s*(\d{1,2})R\s+(.*?)\s+H(\d{3,4})m\s+(\S+).*?風\s+(\S+)\s*(\d+)m\s+波\s+(\d+)cm", re.M)

RE_FINAL = re.compile(r"(?:"
    r"優勝戦"
    r"|優\s*勝\s*戦"
    r"|決勝戦"
    r"|王将位決定戦"
    r"|初優勝決定戦"
    r"|Ｇ・Ａ決定戦"
    r"|賞金女王決定"
    r"|賞金王決定戦"
    r"|是政女王決定"
    r"|是政王子決定"
    r"|海の王者決定"
    r"|是政名人決定"
    r"|波乗り王決定"
    r"|ヘビー級王決"
    r"|王座決定戦"
    r"|関ヶ原決戦"
    r"|団体・優勝"
    r"|オオムラＧＰ"
    r"|是政プリンス"
    r"|澤乃井ファイ"
    r"|ファイナル\s*$"
    r"|(?<=.{4})優勝"
    r"|(?<=.{5})優"
    r")",re.I)

RE_CANCEL_LINE = re.compile(r"^\s*(\d{1,2})R\s*中\s*止\s*$", re.M)
RE_PREFINAL    = re.compile(r"準優(?!進出)|準王将位戦", re.I)

#-------------------------------------------------
def to_upsert(c:dal.transaction, r:Dict):

    pre_cnt = c.total_changes

    cur = c.execute("""
              INSERT INTO races( race_id,  date,       venue_id,    race_no,
                                 day_no,   race_title, grade,       series_title,
                                 weather,  wind_dir,   wind_spd,    wave_hgt,
                                 distance, is_final,   is_prefinal, status        )
              VALUES( :race_id,  :date,       :venue_id,    :race_no,
                      :day_no,   :race_title, :grade,       :series_title,
                      :weather,  :wind_dir,   :wind_spd,    :wave_hgt,
                      :distance, :is_final,   :is_prefinal, :status        )
      
                     ON CONFLICT(race_id) 
                     DO UPDATE SET day_no       = excluded.day_no,
                                   race_title   = excluded.race_title,
                                   grade        = excluded.grade,
                                   series_title = excluded.series_title,
                                   weather      = excluded.weather,
                                   wind_dir     = excluded.wind_dir,
                                   wind_spd     = excluded.wind_spd,
                                   wave_hgt     = excluded.wave_hgt,
                                   distance     = excluded.distance,
                                   is_final     = excluded.is_final,
                                   is_prefinal  = excluded.is_prefinal,
                                   status       = excluded.status  
                      """,r)

    return 1 if c.total_changes > pre_cnt else 0

#-------------------------------------------------
def to_insert(c:dal.transaction, r:Dict):

    pre_cnt = c.total_changes

    c.execute("""
        INSERT OR IGNORE INTO races(
            race_id,  date,       venue_id,    race_no,
            day_no,   race_title, grade,       series_title,
            weather,  wind_dir,   wind_spd,    wave_hgt,
            distance, is_final,   is_prefinal, status       )
        VALUES(
            :race_id,  :date,       :venue_id,    :race_no,
            :day_no,   :race_title, :grade,       :series_title,
            :weather,  :wind_dir,   :wind_spd,    :wave_hgt,
            :distance, :is_final,   :is_prefinal, :status       ) """,r)

    return 1 if c.total_changes > pre_cnt else 0

#-------------------------------------------------
def _deg_from_txt(txt:str|None):
    if not txt: return None

    return TXT2DEG.get(txt.strip(), None)
#-----------------------------
def _venue_dir_deg(c:sqlite3.Connection, venue_id:int):

    cur = c.execute("SELECT direction FROM Venues WHERE venue_id=?", (venue_id,))
    row = cur.fetchone()
    if not row or row[0] is None: return None

    return _deg_from_txt(str(row[0]))
#-----------------------------
def _get_title(body:str):
    m = re.search(r"競走成績[^\n]*\n\s*(.+?)\n", body)

    return m.group(1).strip() if m else ""
#-----------------------------
def _get_date(name:str):

    dt = re.search(r"K(\d{2})(\d{2})(\d{2})\.TXT", name, re.I)
    if not dt: return None
    y, m, d = map(int, dt.groups())

    return f"20{y:02d}-{m:02d}-{d:02d}"
#-----------------------------
def _get_subblocks(body: str):

    ms = list(RE_RACE_HEAD.finditer(body))
    out:List[Tuple[int,int,int]] = []

    for i, m in enumerate(ms):
        rno   = int(m.group(1))
        start = m.start()
        end   = ms[i+1].start() if i+1 < len(ms) else len(body)
        out.append((rno, start, end))

    return out
#-----------------------------
def _is_final(title:str):

    if any(word in title for word in ["準", "進出", "進"]):
        return 0

    return 1 if RE_FINAL.search(title) else 0

#=================== Entry =======================
def upsert_Races(venue_id:int, body:str, filename:str, overwrite:bool=False):

    md = RE_DATE_LINE.search(body)

    if md:
        day_no       = int(md.group(1))
        yyyy, mm, dd = map(int, md.groups()[1:4])
        date_iso     = f"{yyyy:04d}-{mm:02d}-{dd:02d}"
    else:
        date_iso     = _get_date(filename)

    s_title       = _get_title(body)
    cancelled_set = {int(m.group(1)) for m in RE_CANCEL_LINE.finditer(body)}
    subblocks     = _get_subblocks(body)
    header_set    = {rno for (rno, _s, _e) in subblocks}

    with dal.transaction() as c:
        cnt_ins, cnt_upd, cnt_canc = 0, 0, 0
        vdeg                       = _venue_dir_deg(c, venue_id)

        for (race_no, start, end) in subblocks:
            head = RE_RACE_HEAD.search(body, start, end)
            if not head: continue

            race_title    = head.group(2)[:6].strip()
            distance      = int(head.group(3))
            weather       = head.group(4).strip()
            wind_dir_text = head.group(5).strip()
            wdeg          = _deg_from_txt(wind_dir_text)

            if wdeg is None or vdeg is None: wind_dir = None
            else:
                relative = ((wdeg + 180) % 360 - vdeg + 360) % 360
                step     = int(round(relative / 22.5)) % 16
                wind_dir = step + 1 

            wind_spd    = int(head.group(6))
            wave_hgt    = int(head.group(7))
            is_final    = _is_final(race_title)
            is_prefinal = 1 if RE_PREFINAL.search(race_title) else 0
            status      = "held"
            race_id     = int(f"{yyyy % 100:02d}{mm:02d}{dd:02d}{venue_id:02d}{race_no:02d}")

            d = dict( race_id      = race_id,
                      date         = date_iso,
                      venue_id     = venue_id,
                      race_no      = race_no,
                      day_no       = day_no,
                      race_title   = race_title,
                      grade        = None,
                      series_title = s_title,
                      weather      = weather,
                      wind_dir     = wind_dir,
                      wind_spd     = wind_spd,
                      wave_hgt     = wave_hgt,
                      distance     = distance,
                      is_final     = is_final,
                      is_prefinal  = is_prefinal, 
                      status       = status,      )

            if overwrite: cnt_upd += to_upsert(c, d)
            else:         cnt_ins += to_insert(c, d)

        for race_no in sorted(n for n in cancelled_set if n not in header_set):
            can_rid = int(f"{yyyy % 100:02d}{mm:02d}{dd:02d}{venue_id:02d}{race_no:02d}")

            to_upsert( c, dict(
                race_id  = can_rid, date         = date_iso, venue_id    = venue_id,
                race_no  = race_no, day_no       = day_no,   race_title  = None,
                grade    = None,    series_title = s_title,  weather     = None,
                wind_dir = None,    wind_spd     = None,     wave_hgt    = None,
                distance = None,    is_final     = 0,        is_prefinal = 0,     
                status   = "cancelled",                                               ))

            cnt_canc += 1

    return (date_iso, {"ins_r":cnt_ins, "upd_r":cnt_upd, "cnt_canc":cnt_canc})

#=====================================================================
RE_WIN_MOVE    = re.compile(r"ﾚｰｽﾀｲﾑ[ 　]+([^\s　]{2,6})")
RE_ENTRY_HEAD  = re.compile(r"^\s*(\d{1,2})R\s+.*?H\d{4}m\s+\S+\s+風\s+\S*?\s*\d+m\s+波\s+\d+cm", re.M)
RE_RESULT_HEAD = re.compile(r"^\s*着\s+艇\s+登番", re.M)

RE_ROW_LINE    = re.compile(r"""
    ^\s*
    (?P<head>(?:\d{2}|F|L[01]|K[01]?|S[012])) \s+
    (?P<frame_no>[1-6])      \s+
    (?P<player_id>\d{4})     \s+
    (?P<name>.{1,16}?)       \s+
    (?P<motor_no>\d{1,3})    \s+
    (?P<boat_no>\d{1,3})     \s+
    (?:K|\s*)
    (?P<exhibition>(?:\d{1,2}\.\d{2})|(?:\s+\.\s{2})) \s+
    (?P<course>(?:[1-6]|\s)) \s+
    (?:F|L|K|\s)
    (?P<st>(?:\d\.\d{2})|(?:\s\.\s{2})) \s+
    (?P<race_time>(?:\d\.\d{2}\.\d)|(?:\s+\.\s{2}\.\s)) ?\s*$
""", re.X | re.M)

#-----------------------------
def _parse_time(s:str):
    s = s.strip()
    return float(s) if s and s[0].isdigit() else None
#-----------------------------
def _parse_course(s:str):
    s = s.strip()
    return int(s) if s.isdigit() else None
#-------------------------------------------------
def _subblocks_by_race(body:str):

    ms                            = list(RE_ENTRY_HEAD.finditer(body))
    subs:List[Tuple[int,int,int]] = []

    for i, m in enumerate(ms):
        rno   = int(m.group(1))
        start = m.end()
        end   = ms[i+1].start() if i+1 < len(ms) else len(body)
        subs.append((rno, start, end))

    return subs

#-------------------------------------------------
def _parse_fin_head(head:str):

    h = head.strip()
    if h.isdigit() and len(h) == 2:
        fr = int(h)
        if 1 <= fr <= 6: return fr, 'N', None
        elif    fr == 0: return 0,  'N', 0

    if h == 'F':                 return None, 'F', None
    if h.startswith('L'):
        lve = h[1:2]
        if lve in ('0','1'):     return None, 'L', int(lve)
    if h.startswith('K'):
        lve = h[1:2]
        if lve in ('0','1'):     return None, 'K', int(lve)
    if h.startswith('S'):
        lve = h[1:2]
        if lve in ('0','1','2'): return None, 'S', int(lve)

    return None, None, None

#-------------------------------------------------
def _not_all_ladies(c:dal.transaction, race_id:int) -> bool:

    row = c.execute("""
        SELECT 1
          FROM Race_entries e
          JOIN Players p
            ON p.player_id = e.player_id
         WHERE e.race_id =?
           AND p.sex='男'
      GROUP BY e.race_id
    """, (race_id,)).fetchone()

    return bool(row)

#-------------------------------------------------
def _update_all_ladies_day(c:dal.transaction, date_iso:str, venue_id:int):

    rows = c.execute("""
        SELECT race_no, race_id
          FROM Races
         WHERE date     = ?
           AND venue_id = ?
           AND status   = 'held'
      ORDER BY race_no
        """,
        (date_iso, venue_id) ).fetchall()

    for race_no, race_id in rows:
        is_ladies = not _not_all_ladies(c, race_id)

        c.execute("""
            UPDATE Races
               SET all_ladies = ?
             WHERE date       = ?
               AND venue_id   = ?
               AND race_no    = ?
            """,
            (1 if is_ladies else 0, date_iso, venue_id, race_no) )

#-------------------------------------------------
def upsert_entry(c:dal.transaction, race_id:int, venue_id:int, e:Dict):

    e = {"race_id":race_id, "venue_id":venue_id, **e}

    c.execute("""
        INSERT INTO Race_entries( race_id,    entry_id, venue_id,  race_no,  date, frame_no,
                                  player_id,  course,    win_move, finish_rank, fault_code,
                                  fault_level, motor_no, boat_no,  slit_ADJ,  race_time      )

             VALUES( :race_id,    :entry_id,    :venue_id, :race_no,  :date, 
                     :frame_no,   :player_id,   :course,   :win_move, :finish_rank,
                     :fault_code, :fault_level, :motor_no, :boat_no,  :slit_ADJ,    :race_time )

            ON CONFLICT(entry_id) DO UPDATE SET
                date       = excluded.date,
                boat_no    = excluded.boat_no,
                motor_no   = excluded.motor_no,
                course     = excluded.course,
                win_move   = excluded.win_move,
                slit_ADJ   = excluded.slit_ADJ,
               finish_rank = excluded.finish_rank,
                fault_code = excluded.fault_code,
               fault_level = excluded.fault_level,
                race_time  = excluded.race_time
              """, e)

#=================== Entry =======================
def upsert_Race_entries(venue_id:int, body:str, date_iso:str):

    total     = 0
    subblocks = _subblocks_by_race(body)

    with dal.transaction() as c:
        for race_no, start, end in subblocks:

            row = dal.fetch_one("""
                      SELECT race_id,
                             status
                        FROM races
                       WHERE date     =?
                         AND venue_id =?
                         AND race_no  =?
                      """,
                      (date_iso, venue_id, race_no) )

            if not row: continue

            race_id, status = row
            if status == 'cancelled': continue

            sub = body[start:end]
            mh  = RE_RESULT_HEAD.search(sub)
            if not mh: continue

            tail = sub[mh.end():]
            rows = list(RE_ROW_LINE.finditer(tail))[:6]
            if not rows: continue

            w_mov = None
            WM    = RE_WIN_MOVE.search(body[start:end])
            if WM: w_mov = WM.group(1).strip()

            for r in rows:
                frame_no   = int(r.group("frame_no"))
                entry_id   = race_id*10 + frame_no
                player_id  = int(r.group("player_id"))
                head       =     r.group("head").strip()
                course     = _parse_course(r.group("course"))
                motor_no   = int(r.group("motor_no"))
                boat_no    = int(r.group("boat_no"))
                finish_rank, fault_code, fault_level = _parse_fin_head(head)

                if   fault_code in ('L','K'): slit_ADJ = None
                elif fault_code == 'F':       slit_ADJ = _parse_time(r.group("st")) *-1
                else:                         slit_ADJ = _parse_time(r.group("st"))

                RT_raw    = r.group("race_time")
                race_time = RT_raw.strip() if RT_raw and any(ch.isdigit() for ch in RT_raw) else None
                win_move  = w_mov if finish_rank == 1 else None

                upsert_entry(c, race_id, venue_id,
                             dict( entry_id    = entry_id,
                                   race_no     = race_no,
                                   date        = date_iso,
                                   frame_no    = frame_no,
                                   player_id   = player_id,
                                   course      = course,
                                   win_move    = win_move,
                                   finish_rank = finish_rank,
                                   fault_code  = fault_code,
                                   fault_level = fault_level,
                                   motor_no    = motor_no,
                                   boat_no     = boat_no,
                                   slit_ADJ    = slit_ADJ,
                                   race_time   = race_time    ) )

                total += 1

        _update_all_ladies_day(c, date_iso, venue_id)

    return total

#=====================================================================
def _parse_payout_block(sub:str) -> list[dict]|None:

    lines        = sub.split('\n')
    parsed       = {"TT":[], "FF":[], "2T":[], "2F":[], "KK":[], "3T":[], "3F":[]}
    current_type = None

    for line in lines:
        if not line.strip(): continue

        m_type = re.match(r"^\s*(単勝|複勝|２連単|２連複|拡連複|３連単|３連複)", line)

        if m_type:
            bet_name = m_type.group(1)
            if   bet_name == "単勝":   current_type = "TT"
            elif bet_name == "複勝":   current_type = "FF"
            elif bet_name == "２連単": current_type = "2T"
            elif bet_name == "２連複": current_type = "2F"
            elif bet_name == "拡連複": current_type = "KK"
            elif bet_name == "３連単": current_type = "3T"
            elif bet_name == "３連複": current_type = "3F"
            line = line[m_type.end():]

        elif current_type is None:
            continue

        if "人気" in line:
            line = line.split("人気")[0]

        if "不成立" in line:
            parsed[current_type].append((0, None))
            continue
            
        if "特払い" in line:
            parsed[current_type].append((8, 70))
            continue

        matches = re.findall(r"([\d]+(?:-[\d]+)*)\s+(\d+)", line)
        for combo_str, payout_str in matches:
            combo  = int(combo_str.replace("-", ""))
            payout = int(payout_str)
            parsed[current_type].append((combo, payout))

    if all(len(v) == 0 for v in parsed.values()):
        return None

    base_slots = {"TT":1, "FF":2, "2T":1, "2F":1, "KK":3, "3T":1, "3F":1}
 
    max_multiplier = 1
    for ctype, slots in base_slots.items():
        count = len(parsed[ctype])
        if count > 0:
            multiplier = math.ceil(count / slots)
            if multiplier > max_multiplier:
                max_multiplier = multiplier
                
    results = []
    statuses = ["normal", "tie_1", "tie_2", "tie_3", "tie_4"]
    
    for m in range(max_multiplier):
        status  = statuses[m] if m < len(statuses) else f"tie_{m}"
        d_combo = 8 if status == "normal" else 9
        row     = {"status": status}

        for ctype, slots in base_slots.items():
            start_idx = m * slots
            for i in range(slots):
                idx = start_idx + i
                if idx < len(parsed[ctype]):
                    val = parsed[ctype][idx]
                else:
                    if m == 0 and len(parsed[ctype]) == 1 and parsed[ctype][0][0] in (0, 8):
                        val = parsed[ctype][0]
                    else:
                        val = (d_combo, None)

                combo, payout = val

                if ctype in ("TT", "2T", "2F", "3T", "3F"):
                    row[f"combo_{ctype}"]  = combo
                    row[f"payout_{ctype}"] = payout
                elif ctype == "FF":
                    row[f"combo_FF{i+1}"]  = combo
                    row[f"payout_FF{i+1}"] = payout
                elif ctype == "KK":
                    row[f"combo_KK{i+1}"]  = combo
                    row[f"payout_KK{i+1}"] = payout
                    
        results.append(row)

    return results

#=================== Entry =======================
def upsert_Payouts_from_K(venue_id:int, body:str, date_iso:str) -> int:

    total     = 0
    subblocks = _subblocks_by_race(body)

    for race_no, start, end in subblocks:

        row = dal.fetch_one("""
                  SELECT race_id
                    FROM Races
                   WHERE date     = ?
                     AND venue_id = ?
                     AND race_no  = ?
                  """,
                  (date_iso, venue_id, race_no))

        if not row:
            continue

        race_id      = row[0]
        sub          = body[start:end]
        payouts_list = _parse_payout_block(sub)

        if not payouts_list:
            continue

        for pd in payouts_list:
            dal.execute("""
                INSERT INTO Payouts
                    ( race_id,   date,    venue_id, race_no, status,
                      combo_3T,  combo_3F, combo_2T, combo_2F, combo_TT,
                      combo_FF1, combo_FF2,
                      combo_KK1, combo_KK2, combo_KK3,
                      payout_3T, payout_3F, payout_2T, payout_2F, payout_TT,
                      payout_FF1, payout_FF2,
                      payout_KK1, payout_KK2, payout_KK3 )
                VALUES (?,?,?,?,?,
                        ?,?,?,?,?,?,?,?,?,?,
                        ?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(race_id, status) DO UPDATE SET
                      combo_3T   = excluded.combo_3T,
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
                """,
                ( race_id, date_iso, venue_id, race_no, pd["status"],
                  pd["combo_3T"],  pd["combo_3F"],  pd["combo_2T"],
                  pd["combo_2F"],  pd["combo_TT"],
                  pd["combo_FF1"], pd["combo_FF2"],
                  pd["combo_KK1"], pd["combo_KK2"], pd["combo_KK3"],
                  pd["payout_3T"], pd["payout_3F"], pd["payout_2T"],
                  pd["payout_2F"], pd["payout_TT"],
                  pd["payout_FF1"],pd["payout_FF2"],
                  pd["payout_KK1"],pd["payout_KK2"],pd["payout_KK3"], ))

        total += 1

    return total
#=====================================================================