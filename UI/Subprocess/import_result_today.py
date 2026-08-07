# -*- coding: utf-8 -*-
# C:\boatrace\UI\Subprocess\import_result_today.py

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
            "Connection": "keep-alive",
}
# ----------------------------
def conn():
    c             = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON;")
    return c
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
def fetch_program(c:sqlite3.Connection, d_iso:str, venue_id:int, race_no:int):

    sql = """
      SELECT frame_no, player_id, motor_no, boat_no
        FROM Race_programs
       WHERE date=? AND venue_id=? AND race_no=?
       ORDER BY frame_no
    """
    rows = c.execute(sql, (d_iso, venue_id, race_no)).fetchall()
    return {r[0]:{"player_id":r[1], "motor_no":r[2], "boat_no":r[3]} for r in rows}

# ------------------------------------------------------------
def fetch_venues(c:sqlite3.Connection, d_iso:str):

    rows = c.execute("""
           SELECT DISTINCT venue_id
             FROM Race_programs
            WHERE date     = ?
              AND race_no  = ?
           """,
           (d_iso, 1),).fetchall()

    return tuple(row[0] for row in rows)

# ------------------------------------------------------------
def fetch_cancelled(c:sqlite3.Connection, d_iso:str, venue_id:int, race_no:int):

    row = c.execute("""
              SELECT status
                FROM Races
               WHERE date=? AND venue_id=? AND race_no=?
              """,
              (d_iso, venue_id, race_no)).fetchone()

    out = True if row and row[0] == 'cancelled' else False

    return out

# ----------------------------------------------------------
def fetch_race_meta(conn:sqlite3.Connection, d_iso:str, venue_id:int, race_no:int):

    row = conn.execute("""
        SELECT MIN(series_title) AS series_title,
               MIN(grade)        AS grade,
               MIN(day_no)       AS day_no,
               MIN(race_title)   AS race_title
          FROM Race_programs
         WHERE date=? AND venue_id=? AND race_no=?

           """, (d_iso, venue_id, race_no)).fetchone()

    if not row: return None

    return {"series_title": row[0],
                   "grade": row[1],
                  "day_no": row[2],
              "race_title": row[3], }

# ------------ (周回短縮/安定板使用)取得 -------------------
def parse_distance_and_stabilizer(soup: BeautifulSoup) -> tuple[int | None, int]:


    stabilizer = 1 if any( "安定板使用" in el.get_text(strip=True)
                           for el in soup.select("span.label2.is-type1")  ) else 0

    distance = None
    h3 = soup.select_one("h3.title16_titleDetail__add2020")
    if h3:
        t = h3.get_text(" ", strip=True)
        if "1200m" in t:
            distance = 1200
        elif "1800m" in t:
            distance = 1800

    return distance, stabilizer

# -------------- 気象情報取得(結果ページ) ------------------
def parse_weather(soup: BeautifulSoup) -> dict:

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
def parse_finish_table(soup: BeautifulSoup):

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
    # ----------------------------------
    def fault_from_token(tok: str):

        if tok in ("転", "落", "エ", "不", "沈", "失"):  return "S", 1
        if tok == "妨":                                  return "S", 2
        if tok in ("F", "Ｆ", "L", "Ｌ"):                return tok, 1
        if tok == "欠":                                  return "K", 0

        return "N", None
    # ----------------------------------
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
        else: fault_code, fault_level = fault_from_token(rk_txt)

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
        pid_span = tds[2].select_one("span.is-fs12")
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
def parse_start_info(soup: BeautifulSoup):

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
def parse_win_move(soup: BeautifulSoup) -> str | None:

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
def insert_race(conn:sqlite3.Connection, d_iso:str, venue_id:int, race_no:int,
                                                                race_meta:dict  ):

    """
    race_meta: { "distance":  1200|1800|None,
                  "weather":   str|None,
                 "wind_dir":   str|None,
                 "wind_spd":   int|None,
                 "wave_hgt":   int|None,
               "stabilizer":     0|1          }
    """

    meta = fetch_race_meta(conn, d_iso, venue_id, race_no)
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

    return (conn.execute(sql, params)).rowcount

# ------------------------------------------------------------
def upsert_results(conn:sqlite3.Connection, d_iso:str, venue_id:int, race_no:int,
                   prog, fin, stinfo, winmv:str|None):

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
        if v.get("finish_rank") == 1: winner_frame = fr; break

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

    return (conn.executemany(sql, params)).rowcount

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

    c        = conn()
    target_v = fetch_venues(c, args.date) if args.ALL_venue else [args.venue]

    for jcd in target_v:
        target_r   = list(range(1, 13)) if args.ALL_race else [args.race]
        r_no1_skip = False

        if args.ALL_race:
            for r in range(1,13):
                if fetch_cancelled(c, args.date, jcd, r):
                    r_no1_skip =True
                    break

        for rno in target_r:
            if r_no1_skip and rno == 1: continue
            if fetch_cancelled(c, args.date, jcd, rno):
                if not args.ALL_race:
                    print(f"[OK] {rno}R is cancelled. skip import_Result.")
                    c.close()
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
                    print(f"[page not update yet] Insert: skip")
                    return 3
                continue

            with conn() as c:
                c.execute("PRAGMA foreign_keys=ON;")

                prog = fetch_program(c, args.date, jcd, rno)
                if not prog:
                    if not args.ALL_race:
                        print("[WARN] Race_programs が未整備です")
                        c.close()
                        return 2
                    continue
 
                inserted = insert_race(c, args.date, jcd, rno, race_meta)
                if not inserted:
                    if not args.ALL_race:
                        print("[WARN] Insert Races error")
                        c.close()
                        return 2
                    continue

                upserted = upsert_results(c, args.date, jcd, rno, prog, fin, stinfo, winmv)
                if not upserted:
                    if not args.ALL_race:
                        print("[WARN] Upsert Race entries error")
                        c.close()
                        return 2
                    continue

            c.commit()
            if args.ALL_race: print(f"[JCD={jcd}  {rno} R] done.")

        if args.ALL_race: rno = "1～12"
        print(f"[OK] Insert: {args.date} jcd={jcd} {rno}R")
        if not args.ALL_venue:
            c.close()
            return 0
    return 0

if __name__ == "__main__":
    sys.exit(main())
