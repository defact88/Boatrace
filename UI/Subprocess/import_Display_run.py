# -*- coding: utf-8 -*-
# C:\boatrace\UI\Subprocess\import_Display_run.py

import argparse, re, sqlite3, sys, warnings, logging, random, time
from datetime  import datetime as dt
from pathlib   import Path
from bs4       import BeautifulSoup, FeatureNotFound, XMLParsedAsHTMLWarning
from curl_cffi import requests

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BASE_DIR = Path(r"C:\boatrace")
DB_PATH  = BASE_DIR / "boatrace.db"
LOG_DIR  = BASE_DIR / r"Archive\logs"
URL_TPL  = "https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={rno}&jcd={jcd:02d}&hd={hd}"

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

logging.basicConfig( filename = LOG_DIR / "import_D_error.log",
                     level    = logging.DEBUG,
                     format   = "%(asctime)s %(levelname)s %(message)s",
                     encoding = "utf-8",                                 )
# ----------------------------
def conn():
    c             = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON;")
    return c
# ----------------------------
def yyyymmdd(s:str) -> str:
    return s.replace("-", "")

# ----------------------------------------------------------
def build_ids(d_iso:str, venue_id:int, race_no:int, frame_no:int):

    _date = dt.strptime(d_iso, "%Y-%m-%d")
    ymd   = _date.strftime("%y%m%d")
    race_id  = int(f"{ymd}{venue_id:02d}{race_no:02d}")
    entry_id = int(f"{ymd}{venue_id:02d}{race_no:02d}{frame_no}")

    return race_id, entry_id

# ----------------------------------------------------------
def parse_absent_flags(soup:BeautifulSoup):

    out    = {}
    bodies = soup.select("tbody")
    frame  = 1
    for tb in bodies:
        cls = " ".join(tb.get("class") or [])
        if tb.find("td", class_=re.compile(r"is-boatColor\d")):
            out[frame] = 1 if ("is-miss" in cls) else 0
            frame     += 1
            if frame > 6: break

    for i in range(1, 7): out.setdefault(i, 0)

    return out
# ------------------------------------------------------------
def parse_lap_and_stabilizer(soup:BeautifulSoup) -> dict:

    lap_reduct = None
    h3         = soup.select_one("h3.title16_titleDetail__add2020")

    if h3:
        t = h3.get_text(" ", strip=True)
        if   "1200m" in t: lap_reduct = 1
        elif "1800m" in t: lap_reduct = 0

    stabilizer = 1 if any( "安定板使用" in el.get_text(strip=True)
                            for el in soup.select("span.label2.is-type1") ) else 0

    return {"lap_reduct":lap_reduct, "stabilizer":stabilizer}

# ------------------------------------------------------------
def parse_weather(soup:BeautifulSoup):

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
             "wind_spd": wind_spd,
             "wind_dir": wind_dir,
             "wave_hgt": wave_hgt, }

# ----------------------------------------------------------
def parse_slit_and_course(soup:BeautifulSoup):

    out    = {}
    rows   = soup.select("div.table1_boatImage1")
    course = 1

    for r in rows:
        num = r.select_one(".table1_boatImage1Number")
        if not num: continue

        try: frame_no = int(num.get_text(strip=True))
        except Exception: continue

        slit_adj = None
        tnode    = r.select_one(".table1_boatImage1Time")

        if tnode:
            tt = tnode.get_text(strip=True)
            if tt.startswith("F"):
                m = re.search(r"F\.(\d+)", tt)
                if m: slit_adj = - float(f"0.{m.group(1)}")
                else: slit_adj = -0.2
            elif tt == "L":
                slit_adj = "L"
            else:
                m = re.search(r"\.(\d+)", tt)
                if m: slit_adj = float(f"0.{m.group(1)}")

        out[frame_no] = {"course":course, "slit_ADJ":slit_adj}
        course       += 1

    return out

# ----------------------------------------------------------
def parse_exhibition_tilt_parts(soup:BeautifulSoup):

    out  = {i:{"exhibition":None, "tilt":None, "rep_parts":None} for i in range(1, 7)}

    left = None
    for tbl in soup.select("table"):
        txt = tbl.get_text(" ", strip=True)
        if ("展示" in txt and "タイム" in txt) and ("チルト" in txt) and ("部品交換" in txt):
            left = tbl
            break
    if not left: return out

    tilt_ok = {-0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0}

    for tb in left.select("tbody"):
        fcell = tb.select_one("td[class*=is-boatColor]")
        if not fcell: continue

        try: frame_no = int(fcell.get_text(strip=True))
        except Exception: continue

        if not (1 <= frame_no <= 6): continue

        first_tr = tb.find("tr")
        if not first_tr: continue

        texts = [ td.get_text(strip=True)
                  .replace("?", "-").replace("ー", "-").replace("－", "-")
                  for td in first_tr.find_all("td")                        ]

        try:                  start = next(i for i, t in enumerate(texts) if t.endswith("kg"))
        except StopIteration: start = -1

        ex_txt   = texts[start + 1] if (start >= 0 and start +1 < len(texts)) else ""
        tilt_txt = texts[start + 2] if (start >= 0 and start +2 < len(texts)) else ""

        exhibition = None
        if ex_txt and re.fullmatch(r"\d{1,2}\.\d{1,3}", ex_txt):
            try:
                v = float(ex_txt)
                if 5.0 <= v <= 9.0: exhibition = round(v, 2)
            except Exception:       exhibition = None

        tilt = None
        if tilt_txt and re.fullmatch(r"-?\d\.\d", tilt_txt):
            try:
                v = float(tilt_txt)
                if v in tilt_ok: tilt = v
            except Exception:    tilt = None

        rep_list = [li.get_text(strip=True) for li in tb.select("ul.labelGroup1 li")]

        if any(td.get_text(strip=True) == "新" for td in tb.select("td[rowspan]")
               ) and "プロペラ" not in rep_list:
            rep_list.append("プロペラ")

        out[frame_no]["exhibition"] = exhibition
        out[frame_no]["tilt"]       = tilt
        out[frame_no]["rep_parts"]  = (",".join(rep_list) if rep_list else None)

    return out

# ------------------------------------------------------------
def fetch_program_players(c, d_iso:str, venue_id:int, race_no:int):

    rows = c.execute("""
           SELECT frame_no, player_id
             FROM Race_programs
            WHERE date     = ?
              AND venue_id = ?
              AND race_no  = ?
         ORDER BY frame_no
           """,
           (d_iso, venue_id, race_no), ).fetchall()

    return [(int(r[0]), int(r[1])) for r in rows]
# ------------------------------------------------------------
def fetch_venues(c, d_iso:str):

    rows = c.execute("""
           SELECT DISTINCT venue_id
             FROM Race_programs
            WHERE date     = ?
              AND race_no  = ?
           """,
           (d_iso, 1),).fetchall()

    return tuple(row[0] for row in rows)
# ------------------------------------------------------------
def fetch_cancelled(c, d_iso:str, venue_id:int, race_no:int):

    row = c.execute("""
              SELECT status
                FROM Races
               WHERE date=? AND venue_id=? AND race_no=?
              """,
              (d_iso, venue_id, race_no)).fetchone()

    out = True if row and row[0] == 'cancelled' else False

    return out
# ----------------------------------------------------------
def upsert_Display_run(c, d_iso:str, v_id:int, r_no:int, per_frame, w):

    sql = """
        INSERT INTO Display_run( race_id,  entry_id,  venue_id,   date,       race_no,
                                 weather,  wind_dir,  wind_spd,   wave_hgt,   player_id,
                                 frame_no, is_absent, course,     exhibition, slit_ADJ,
                                 tilt,     rep_parts, lap_reduct, stabilizer             )

             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

        ON CONFLICT(entry_id)
            DO UPDATE SET weather    = excluded.weather,
                          wind_dir   = excluded.wind_dir,
                          wind_spd   = excluded.wind_spd,
                          wave_hgt   = excluded.wave_hgt,
                          is_absent  = excluded.is_absent,
                          course     = excluded.course,
                          exhibition = excluded.exhibition,
                          slit_ADJ   = excluded.slit_ADJ,
                          tilt       = excluded.tilt,
                          rep_parts  = excluded.rep_parts,
                          lap_reduct = excluded.lap_reduct,
                          stabilizer = excluded.stabilizer
               """
    params = []

    for fr in range(1, 7):
        p          = per_frame.get(fr, {})
        r_id, e_id = build_ids(d_iso, v_id, r_no, fr)

        pid    = p.get("player_id")  ;is_ms = p.get("is_absent", 0)
        course = p.get("course")     ;slit  = p.get("slit_ADJ")
        ex     = p.get("exhibition") ;tilt  = p.get("tilt")
        parts  = p.get("rep_parts")
        weath  = w.get("weather")    ;w_dir = w.get("wind_dir")
        w_spd  = w.get("wind_spd")   ;wave  = w.get("wave_hgt")
        lap    = w.get("lap_reduct") ;stabi = w.get("stabilizer")

        params.append(( r_id, e_id,  v_id,   d_iso, r_no, weath, w_dir, w_spd, wave,  pid,
                        fr,   is_ms, course, ex,    slit, tilt,  parts, lap,   stabi       ))

    #print(params)
    c.executemany(sql, params)
    c.commit()

# ----------------------------------------------------------
def upsert_Display_run_partial(c, d_iso:str, v_id:int, r_no:int, per_frame, w ):

    sql = """
        INSERT INTO Display_run( race_id,   entry_id,   venue_id,   date,       race_no,
                                 weather,   wind_dir,   wind_spd,   wave_hgt,   player_id,
                                 frame_no,  is_absent,  course,     exhibition, slit_ADJ,
                                 tilt,      rep_parts,  lap_reduct, stabilizer             )

             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

        ON CONFLICT(entry_id)
            DO UPDATE SET weather    = COALESCE(excluded.weather,   weather  ),
                          wind_dir   = COALESCE(excluded.wind_dir,  wind_dir ),
                          wind_spd   = COALESCE(excluded.wind_spd,  wind_spd ),
                          wave_hgt   = COALESCE(excluded.wave_hgt,  wave_hgt ),
                          is_absent  = COALESCE(excluded.is_absent, is_absent),
                          tilt       = COALESCE(excluded.tilt,      tilt     ),
                          rep_parts  = COALESCE(excluded.rep_parts, rep_parts),
                          lap_reduct = COALESCE(excluded.lap_reduct, Display_run.lap_reduct),
                          stabilizer = COALESCE(excluded.stabilizer, Display_run.stabilizer)
           """
    params = []

    for fr in range(1, 7):
        p          = per_frame.get(fr, {})
        r_id, e_id = build_ids(d_iso, v_id, r_no, fr)

        pid    = p.get("player_id")  ;is_ms = p.get("is_absent", 0)
        tilt   = p.get("tilt")       ;parts = p.get("rep_parts")
        weath  = w.get("weather")    ;w_dir = w.get("wind_dir")
        w_spd  = w.get("wind_spd")   ;wave  = w.get("wave_hgt")
        lap    = w.get("lap_reduct") ;stabi = w.get("stabilizer")

        params.append(( r_id, e_id,  v_id, d_iso, r_no, weath, w_dir, w_spd, wave, pid,
                        fr,   is_ms, None, None,  None, tilt,  parts, lap,   stabi      ))

    c.executemany(sql, params)
    c.commit()

# ====================================================================
def main():

    ap = argparse.ArgumentParser()
    ap.add_argument("--date",  required=True, help="YYYY-MM-DD")
    ap.add_argument("--venue",                type=int)
    ap.add_argument("--race",                 type=int)
    ap.add_argument("--ALL_venue", action="store_true")
    ap.add_argument("--ALL_race",  action="store_true")

    args = ap.parse_args()
    hd   = yyyymmdd(args.date)

    if not args.venue and not args.ALL_venue:
        print(f"input 'venue_id' or select 「--ALL_venue」") ;return
    if not args.race  and not args.ALL_race:
        print(f"input 'race_no'  or select 「--ALL_race」")  ;return

    try:
        c        = conn()
        target_v = fetch_venues(c, args.date) if args.ALL_venue else [args.venue]

        for jcd in target_v:
            target_r   = list(range(1, 13)) if args.ALL_race else [args.race]

            for rno in target_r:
                if fetch_cancelled(c, args.date, jcd, rno):
                    if not args.ALL_race:
                        print(f"[OK] {rno}R is cancelled. skip Display_run insert.")
                        c.close()
                        return 0
                    print(f"[OK] jcd={jcd}  {rno}R is cancelled")
                    continue

                url = URL_TPL.format(rno=rno, jcd=jcd, hd=hd)

                with requests.Session(impersonate="firefox") as session:
                    session.headers.update(HEADERS)
                    try:
                        time.sleep(random.uniform(1.6,3.2))
                        res = session.get(url, timeout=10)
                        res.raise_for_status()
                    except Exception as e:
                        print(f"[ERR] Page access failed: {e}")
                        c.close()
                        return 1

                soup    = BeautifulSoup(res.text, "lxml")
                meta    = parse_lap_and_stabilizer(soup)
                weather = parse_weather(soup)
                slit    = parse_slit_and_course(soup)
                etc     = parse_exhibition_tilt_parts(soup)
                weather["lap_reduct"] = meta["lap_reduct"]
                weather["stabilizer"] = meta["stabilizer"]

                prog = fetch_program_players(c, args.date, jcd, rno)
                if not prog:
                    if not args.ALL_race:
                        print("[WARN] jcd={jcd} {rno}R  Race_programs が未整備です")
                        c.close()
                        return 2
                    continue

                absent    = parse_absent_flags(soup)
                per_frame = {}
                for frame_no, player_id in prog:
                    per_frame[frame_no] = {
                        "player_id": player_id,
                        "is_absent": absent.get(frame_no, 0),
                           "course": slit.get(frame_no, {}).get("course"),
                         "slit_ADJ": slit.get(frame_no, {}).get("slit_ADJ"),
                       "exhibition":  etc.get(frame_no, {}).get("exhibition"),
                             "tilt":  etc.get(frame_no, {}).get("tilt"),
                        "rep_parts":  etc.get(frame_no, {}).get("rep_parts"),  }

                not_ready_frames = [ fr for fr in range(1, 7)
                                      if per_frame.get(fr,{}).get("is_absent", 0) != 1
                                     and (    per_frame.get(fr,{}).get("exhibition") is None
                                           #or    per_frame.get(fr,{}).get("course")  is None
                                           #or per_frame.get(fr,{}).get("slit_ADJ")   is None 
                                                                                              ) ]

                if not_ready_frames:
                    upsert_Display_run_partial(c, args.date, jcd, rno, per_frame, weather)
                    if not args.ALL_race:
                        print("[page not update yet] Upsert: partial")
                        c.close()
                        return 2
                    continue

                upsert_Display_run(c, args.date, jcd, rno, per_frame, weather)
                if args.ALL_race: print(f"[JCD={jcd}  {rno} R] done.")

            if args.ALL_race: rno = "1～12"
            print(f"[OK] Upsert: {args.date} jcd={jcd} {rno}R")

        c.close()
    except Exception as e:
        logging.error(f"error: {e}", exc_info=True)
        c.close()
        raise

    return 0

# ====================================================================
if __name__ == "__main__":
    sys.exit(main())
