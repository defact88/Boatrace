# -*- coding: utf-8 -*-
# C:\boatrace\UI\Subprocess\get_today_info.py

import sqlite3, re, sys, argparse, warnings, random, time
from datetime  import datetime as dt
from pathlib   import Path
from bs4       import BeautifulSoup, XMLParsedAsHTMLWarning
from curl_cffi import requests
from multiprocessing import Process

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BASE_DIR  = Path(r"C:\boatrace")
DB_PATH   = BASE_DIR / "boatrace.db"
URL_INDEX = "https://www.boatrace.jp/owpc/pc/race/index?hd={hd}"
URL_BASE  = "https://www.boatrace.jp/owpc/pc/race/racelist?rno=1&jcd={jcd:02d}&hd={hd}"
URL_RNO   = "https://www.boatrace.jp/owpc/pc/race/racelist?rno={rno}&jcd={jcd:02d}&hd={hd}"
HEADERS   = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
              "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
              "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
              "Upgrade-Insecure-Requests": "1",
              "Sec-Fetch-Dest": "document",
              "Sec-Fetch-Mode": "navigate",
              "Sec-Fetch-Site": "none",
              "Sec-Fetch-User": "?1",
              "Connection": "keep-alive",
}  
# --------------------------------------
def yyyymmdd(d_iso:str) -> str:
    return d_iso.replace("-", "")
# --------------------------------------
def fetch_index_html(d_iso:str) -> str:
    hd = yyyymmdd(d_iso)
    sess = requests.Session(impersonate="firefox")
    res = sess.get(URL_INDEX.format(hd=hd), headers=HEADERS, timeout=15)
    res.raise_for_status()
    return res.text
# --------------------------------------------------------------------
def build_race_id(d_iso:str, venue_id:int, race_no:int) -> int:

    _date = dt.strptime(d_iso, "%Y-%m-%d")
    ymd   = _date.strftime("%y%m%d")

    return int(f"{ymd}{venue_id:02d}{race_no:02d}")
# --------------------------------------------------------------------
def parse_cancellations(html_text: str) -> list[tuple[int, int]]:

    soup = BeautifulSoup(html_text, "lxml")
    out:list[tuple[int, int]] = []

    for td in soup.select("td.is-p10-10.is-attentionColor1"):
        txt = td.get_text(strip=True)

        from_rno = None
        m = re.search(r"(\d{1,2})R以降中止", txt)
        if m:
            from_rno = int(m.group(1))

        elif "中止順延" or "中止" in txt:
            from_rno = 1

        if from_rno is None:
            continue

        tr = td.find_parent("tr")
        if not tr:
            continue

        a = tr.find("a", href=re.compile(r"/owpc/pc/race/raceindex\?jcd=(\d{2})"))
        if not a:
            continue

        m2 = re.search(r"jcd=(\d{2})", a.get("href", ""))
        if not m2:
            continue

        jcd = int(m2.group(1))
        out.append((jcd, from_rno))

    return out

# --------------------------------------------------------------------
def fetch_race_meta(conn:sqlite3.Connection, d_iso:str, venue_id:int, race_no:int):

    row = conn.execute("""
        SELECT MIN(series_title) AS series_title,
               MIN(grade)        AS grade,
               MIN(day_no)       AS day_no,
               MIN(race_title)   AS race_title
          FROM Race_programs
         WHERE date=? AND venue_id=? AND race_no=?
        """, (d_iso, venue_id, race_no)).fetchone()

    return { "series_title": row[0],
             "grade":        row[1],
             "day_no":       row[2],
             "race_title":   row[3], }

# --------------------------------------------------------------------
def insert_cancelled(conn:sqlite3.Connection, d_iso:str, venue_id:int, from_rno:int) -> int:

    inserted = 0
    for rno in range(from_rno, 13):

        row = conn.execute("""
                  SELECT 1 
                    FROM Races
                   WHERE date=? AND venue_id=? AND race_no=?
                   LIMIT 1
                  """,
                  (d_iso, venue_id, rno)).fetchone()

        if row: continue

        meta    = fetch_race_meta(conn, d_iso, venue_id, rno)
        race_id = build_race_id(d_iso, venue_id, rno)
    
        cur = conn.execute("""
                  INSERT
                    INTO Races
                        ( race_id,  date,       venue_id, series_title, grade,   day_no,
                          race_no,  race_title, is_final, distance    , weather, wind_dir,
                          wind_spd, wave_hgt,   status                                     )
                  VALUES(?, ?, ?, ?, ?, ?, ?, ?, 0, 1600, NULL, NULL, NULL, NULL, 'cancelled')
                  """,
                 ( race_id, d_iso,  venue_id, meta["series_title"], meta["grade"],
                    meta["day_no"], rno,  meta["race_title"],                  )           )

        inserted  += cur.rowcount

    return inserted 

# --------------------------------------------------------------------
def get_cancel_info() -> int:

    ap    = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args  = ap.parse_args()
    d_iso = args.date

    try: html = fetch_index_html(d_iso)
    except Exception as e:
        print(f"[ERR] GET index failed: {e}")
        return 1

    cancels = parse_cancellations(html)
    if not cancels:
        print("[INFO] no cancellations")
        return 0

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys=ON;")

        total_upd = 0
        for (venue_id, from_rno) in cancels:
            upd = insert_cancelled(conn, d_iso, venue_id, from_rno)
            if upd: 
                print(f"[OK] Insert cancelled: jcd={venue_id} rno>={from_rno}")
                total_upd += upd

        conn.commit()

    if total_upd == 0: print("[INFO] no change")

    return 0
# --------------------------------------
def update_deadline(conn:sqlite3.Connection, d_iso:str, jcd:int, rno:int, hhmm:str):
    cursor = conn.cursor()
    sql = """
             UPDATE Race_programs
                SET deadline_vote  = ?
              WHERE date           = ?
                AND venue_id       = ?
                AND race_no        = ?
                AND deadline_vote <> ?  """

    cursor.execute(sql, (f"{d_iso} {hhmm}", d_iso, jcd, rno, f"{d_iso} {hhmm}" ))
    return cursor.rowcount
# --------------------------------------
def set_absent(conn:sqlite3.Connection, d_iso:str, jcd:int, rno:int, frame_no:int):

    sql = """
             UPDATE Race_programs
                SET is_absent = 1
              WHERE date      = ?
                AND venue_id  = ?
                AND race_no   = ?
                AND frame_no  = ?   """
    conn.execute(sql, (d_iso, jcd, rno, frame_no))

# --------------------- 解析 ---------------------
def parse_deadline_grid(html_text:str):

    soup   = BeautifulSoup(html_text, "lxml")
    target = None

    for tbl in soup.select("table"):
        if "締切予定時刻" in tbl.get_text():
            target = tbl
            break
    if not target: return {}
    tbody = target.find("tbody")
    if not tbody: return {}

    row = None
    for tr in tbody.select("tr"):
        tds = tr.select("td")
        if not tds: continue
        if "締切予定時刻" in (tds[0].get_text(strip=True) if tds else ""):
            row = [td.get_text(strip=True) for td in tds]
            break
    if not row: return {}

    out = {}
    for idx, hhmm in enumerate(row[1:], start=1):
        if re.fullmatch(r"\d{1,2}:\d{2}", hhmm):
            out[idx] = hhmm
    return out

# ------------------------------------------------
def parse_absent_frames(html_text:str) -> set[int]:

    soup   = BeautifulSoup(html_text, "lxml")
    absent = set()

    for tb in soup.select("table tbody.is-miss"):
        fcell = tb.find("td", class_=re.compile(r"is-boatColor(\d)"))
        if not fcell: continue
        m = re.search(r"is-boatColor(\d)", " ".join(fcell.get("class") or []))
        if m:
            frame_no = int(m.group(1))
            if 1 <= frame_no <= 6: absent.add(frame_no)

    return absent

# ============= get_change main ==================
def get_change_info():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date",  required=True, help="YYYY-MM-DD")
    ap.add_argument("--venue", required=True, type=int)
    ap.add_argument("--first", action="store_true", help="初回実行")

    args     = ap.parse_args()
    d_iso    = args.date
    jcd      = int(args.venue)
    hd       = yyyymmdd(d_iso)
    sess     = requests.Session(impersonate="firefox")
    sess.headers.update(HEADERS)
    try:
        res = sess.get(URL_BASE.format(jcd=jcd, hd=hd), timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"[ERR] GET grid failed: {e}")
        return 1

    deadlines = parse_deadline_grid(res.text)
    if not deadlines: print("[WARN] racelist grid: no deadline row")
    else:             print(f"[INFO] deadlines: {len(deadlines)} items")

    now                                = dt.now()
    force_all                          = bool(args.first) 
    absents_by_rno:dict[int, set[int]] = {}
    
    for rno in range(1, 13):
        hhmm = deadlines.get(rno)
        if hhmm and (not force_all):
            try:
                dd = dt.strptime(f"{d_iso} {hhmm}", "%Y-%m-%d %H:%M")
                if now >= dd: continue
            except Exception: pass
        try:
            time.sleep(random.uniform(1.6,3.2))
            r = sess.get(URL_RNO.format(rno=rno, jcd=jcd, hd=hd), timeout=15)
            r.raise_for_status()
        except Exception: continue
        frames = parse_absent_frames(r.text)
        if frames: absents_by_rno[rno] = frames

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        upd_d = []
        upd_a = []
        for rno, hhmm in deadlines.items():
             upd = update_deadline(conn, d_iso, jcd, rno, hhmm)
             if upd: upd_d.append(rno)
        for rno, frames in absents_by_rno.items():
            for fr in sorted(frames):
                set_absent(conn, d_iso, jcd, rno, fr)
                upd_a.append(rno) 

        conn.commit()
    if upd_d:
        print(f"[OK] deadlines_updated: {','.join(str(n) for n in sorted(set(upd_d)))}")
    if upd_a:
        print(f"[OK] absents_updated: {','.join(str(n) for n in sorted(set(upd_a)))}")

    return 0

#=====================================================================
def main():
    flag = sys.argv.pop(1) 

    if   flag == "A": get_change_info()
    elif flag == "B": get_cancel_info()

#=====================================================================
if __name__ == "__main__":
    sys.exit(main())


