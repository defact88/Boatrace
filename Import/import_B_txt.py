# -*- coding: utf-8 -*-
# C:\boatrace\Inport\import_B_txt.py

from __future__ import annotations
from datetime   import datetime as dt, timedelta, timezone, date
from pathlib    import Path
from typing     import Iterable, Iterator, List, Optional, Tuple, Dict
from curl_cffi  import requests
from bs4        import BeautifulSoup, FeatureNotFound, XMLParsedAsHTMLWarning
import argparse, re, sqlite3, shutil, lhafile, warnings, time, random

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# ----------------------------------------------------------
BASE         = Path(r"C:\boatrace")
DB_PATH      = BASE / "boatrace.db"
DIR_DL       = BASE / r"INBOX\DL\B"
DIR_B_TXT    = BASE / r"Archive\B\B_TXT"
DIR_HTML     = BASE / r"Archive\B\HTML"
DIR_TEXT     = BASE / r"Archive\B\TEXT"

ZEN_DIGITS   = str.maketrans("０１２３４５６７８９", "0123456789")
ZEN_TIME     = str.maketrans("０１２３４５６７８９：", "0123456789:")
RE_TEL_CLOSE = re.compile(r"電話投票締切予定(?P<hhmm>[０-９]{2}：[０-９]{2})")

HEADERS = { "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Connection": "keep-alive",
}
# ------ ユーティリティ ------
def zhhmm_to_hhmm(s:str):

    return s.translate(ZEN_TIME)
# ----------------------------
def to_halfwidth_digits(s:str):

    return s.translate(ZEN_DIGITS)
# ----------------------------
def make_program_id(d:date, venue_id:int, race_no:int, frame_no:int):

    yymmdd = d.strftime("%y%m%d")

    return int(f"{yymmdd}{venue_id:02d}{race_no:02d}{frame_no:d}")
# ----------------------------
def jst_today():

    JST = timezone(timedelta(hours=9))

    return dt.now(JST).date()
# ----------------------------
def target_date(args:argparse.Namespace):

    return dt.strptime(args.date, "%Y-%m-%d").date() if args.date else jst_today()
# ----------------------------
def url_candidates(d:date):

    yyyymm = d.strftime("%Y%m")
    yymmdd = d.strftime("%y%m%d")

    return f"http://www1.mbrace.or.jp/od2/B/{yyyymm}/b{yymmdd}.lzh"
# ----------------------- DL/展開 --------------------------
def download(url:str, out:Path):

    with requests.Session(impersonate="firefox") as session:
        session.headers.update(HEADERS)
        try:
            time.sleep(random.uniform(1.6,2.4))
            r = session.get(url, timeout=30)
            if r.status_code != 200 or not r.content:
                print(f"    not found : {url} (status={r.status_code})")
                return None

            out.write_bytes(r.content)
            print(f"    downloaded : {url} -> {out}")
            return out

        except Exception as e: print(f"  download失敗 : {url} ({e})")

        return None

# ----------------------------------------------------------
def ensure_txt_for_date(d:date):

    yymmdd   = d.strftime("%y%m%d")
    arch_txt = DIR_B_TXT / f"B{yymmdd}.TXT"

    if arch_txt.exists():
        print(f"   [use archive] : {arch_txt}")
        return arch_txt, None

    lzh_path = None
    u        = url_candidates(d)
    suffix   = Path(u).suffix.lower()
    out      = DIR_DL / f"B{yymmdd}{suffix.upper()}"
    got      = download(u, out)

    if got: lzh_path = got
    else: raise FileNotFoundError("Bファイルを取得できませんでした。")

    txt_path:Optional[Path] = None
    lhf                     = lhafile.Lhafile(str(lzh_path))

    for info in lhf.infolist():
        nm = Path(info.filename).name

        if nm.upper().endswith(".TXT"):
            data     = lhf.read(info.filename)
            txt_path = DIR_DL / nm.upper()
            txt_path.write_bytes(data)
            print(f"        extracted : {lzh_path.name} -> {txt_path}")
            break

    if txt_path is None:
        raise FileNotFoundError("LZH内にTXTが見つかりませんでした。")

    return txt_path, lzh_path

# --------- パーサ(B) --------
re_day_no      = re.compile(r"第\s*([0-9０-９]{1,2})日")
re_race_header = re.compile(r"^\s*([0-9０-９]{1,2})Ｒ\s+(.+?)\s+Ｈ")
re_detail      = re.compile( r"^\s*(?P<frame>\d)"
                             r"\s(?P<pid>\d{4})"
                             r"\D{1,2}\s*\D{1,2}"
                             r"(?P<age>\d{2})"
                             r"(?P<branch>\D{2})"
                             r"(?P<wt>\d{2})"
                             r"\D\d"
                             r"\s*\d{1,3}\.\d{2}"
                             r"\s*\d{1,3}\.\d{2}"
                             r"\s*\d{1,3}\.\d{2}"
                             r"\s*\d{1,3}\.\d{2}"
                             r"\s*(?P<motor_no>\d{1,3})"
                             r"\s*(?P<motor_ave>\d{1,3}\.\d{2})"
                             r"\s*(?P<boat_no>\d{1,3})"
                             r"\s*(?P<boat_ave>\d{1,3}\.\d{2})"    )

# ----------------------------------------------------------
def split_venue_blocks(text:str):

    lines = text.splitlines()
    i     = 0

    while i < len(lines):

        m = re.match(r"^(\d{2})BBGN$", lines[i].strip())
        if not m:
            i += 1
            continue

        venue_id = int(m.group(1))
        start    = i + 1
        j        = start

        while j < len(lines):
            if lines[j].strip() == f"{venue_id:02d}BEND": break
            j += 1

        block  = lines[start:j]

        yield venue_id, block

        i = j + 1

# ----------------------------------------------------------
def parse_block(venue_id:int, block_lines:List[str], file_date:date):

    series_title = ""
    day_no       = 0

    for idx, line in enumerate(block_lines[:10]):
        if idx == 4: series_title = line.strip()
        if idx == 6:
            m   = re_day_no.search(line)
            if m: day_no = int(to_halfwidth_digits(m.group(1)))

    i = 11

    while i + 10 < len(block_lines):
        head    = block_lines[i : i + 5]
        details = block_lines[i + 5 : i + 11]
        i      += 12
        m       = re_race_header.search(head[0])
        if not m: continue

        race_no       = int(to_halfwidth_digits(m.group(1)))
        race_title    = m.group(2).strip()
        deadline_hhmm = None

        for h in head:
            mt = RE_TEL_CLOSE.search(h)
            if mt:
                deadline_hhmm = zhhmm_to_hhmm(mt.group("hhmm"))
                break

        for dl in details:
            m2 = re_detail.search(dl)
            if not m2: continue

            frame_no   = int(m2.group("frame"))
            player_id  = int(m2.group("pid"))
            weight_tdy = float(to_halfwidth_digits(m2.group("wt")))
            motor_no   = int(m2.group("motor_no"))
            motor_ave  = float(m2.group("motor_ave"))
            boat_no    = int(m2.group("boat_no"))
            boat_ave   = float(m2.group("boat_ave"))
            program_id = make_program_id(file_date, venue_id, race_no, frame_no)

            yield ( program_id, venue_id, day_no,    series_title, race_no,
                    race_title, frame_no, player_id, weight_tdy,   motor_no,
                    motor_ave,  boat_no,  boat_ave,  deadline_hhmm           )

# ----------------------- DB: INSERT -----------------------
def insert_programs(rows, overwrite:bool=False):

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    try:
        cur  = conn.cursor()
        verb = "INSERT OR REPLACE" if overwrite else "INSERT OR IGNORE"
        sql  = f"""
            {verb} INTO Race_programs
                       ( program_id, date,       venue_id,  series_title, day_no,
                         race_no,    race_title, frame_no,  player_id,
                         weight_tdy, motor_no,   motor_ave, boat_no, boat_ave,
                         deadline_vote                                            )
                 VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

        count = 0

        for r in rows:
            ( program_id, venue_id,    day_no,      series_title,
              race_no,    race_title,  frame_no,    player_id,
              weight_tdy, motor_no,    motor_ave,   boat_no, boat_ave,
              deadline_hhmm                                            ) = r

            yymmdd       = str(program_id)[:6]
            yyyy         = 2000 + int(yymmdd[:2])
            mm           = int(yymmdd[2:4])
            dd           = int(yymmdd[4:6])
            iso_date     = f"{yyyy:04d}-{mm:02d}-{dd:02d}"
            deadline_iso = f"{iso_date} {deadline_hhmm}" if deadline_hhmm else None

            cur.execute(sql, (
                program_id, iso_date,   venue_id,  series_title, day_no,
                race_no,    race_title, frame_no,  player_id,    weight_tdy,
                motor_no,   motor_ave,  boat_no,   boat_ave,     deadline_iso ) )

            count += cur.rowcount

        conn.commit()

        return count

    finally: conn.close()

# ================ grade / held_type / all_ladies 更新 ==================
GRADE_CLASS_MAP = { 'is-SGa'  : 'SG',
                    'is-SGb'  : 'SG',
                    'is-PG1a' : 'PG1',
                    'is-PG1b' : 'PG1',
                    'is-G1a'  : 'G1',
                    'is-G1b'  : 'G1',
                    'is-G2a'  : 'G2',
                    'is-G2b'  : 'G2',
                    'is-G3a'  : 'G3',
                    'is-G3b'  : 'G3',
                    'is-ippan': '一般' }
RE_JCD          = re.compile(r"[?&]jcd=(\d{2})\b")
RE_HD           = re.compile(r"[?&]hd=(\d{8})\b")
GRADE_TO_NUM    = {"一般":0, "G3":1, "G2":2, "G1":3, "PG1":4, "SG":5}

# ----------------------------------------------------------
def held_type_from_classes(classes:List[str]):

    if 'is-midnight' in classes: return 4
    if 'is-nighter'  in classes: return 3
    if 'is-summer'   in classes: return 2
    if 'is-morning'  in classes: return 1

    return 0
# ----------------------------------------------------------
def fetch_schedule_html(date_iso:str):

    with requests.Session(impersonate="firefox") as session:
        session.headers.update(HEADERS)

        hd  = date_iso.replace("-", "")
        url = f"https://www.boatrace.jp/owpc/pc/race/index?hd={hd}"
        time.sleep(random.uniform(1.6,2.4))
        r   = session.get(url, timeout=20)
        r.raise_for_status()

    return r.text
# ----------------------------------------------------------
def _pick_grade_from_classes(classes:List[str]):

    for cls in classes or []:
        if not cls.startswith("is-"): continue

        for key, val in GRADE_CLASS_MAP.items():
            if cls.startswith(key): return val

    return None
# ----------------------------------------------------------
def parse_schedule_html(html:str):

    soup            = BeautifulSoup(html, "lxml")
    rows:List[Dict] = []

    for tbody in soup.find_all('tbody'):

        a_title = tbody.select_one('a[href*="/owpc/pc/race/raceindex?jcd="]')
        if not a_title: continue

        href = a_title.get('href', '')
        m1   = RE_JCD.search(href); vid = m1.group(1) if m1 else None
        m2   = RE_HD.search(href);  hd  = m2.group(1) if m2 else None
        if not vid: continue

        grade = None

        for td in tbody.find_all('td'):
            classes = td.get('class', [])
            g       = _pick_grade_from_classes(classes)
            if g: grade = g; break

        held_type = 0

        for td in tbody.find_all('td'):
            classes = td.get('class', [])
            ht      = held_type_from_classes(classes)
            if ht  != 0: held_type = ht ; break

        row = {'vid':vid, 'hd':hd, 'grade':grade, 'held_type':held_type}
        rows.append(row)

    return rows

# ----------------------------------------------------------
def parse_venus_from_html(html: str) -> List[Tuple[str, str, str]]:

    soup       = BeautifulSoup(html, "lxml")
    venus_rows = []

    for tr in soup.select('tr'):

        if tr.find('td', class_='is-venus'):
            a_tag = tr.select_one('a[href*="jcd="]')

            if a_tag:
                href        = a_tag.get('href', '')
                series_name = a_tag.get_text(strip=True)
                jcd_match   = re.search(r'jcd=(\d{2})', href)
                hd_match    = re.search(r'hd=(\d{8})', href)
                jcd         = jcd_match.group(1) if jcd_match else ""
                hd          =  hd_match.group(1) if  hd_match else ""

                venus_rows.append((jcd, hd, series_name))

    return venus_rows

# ----------------------------------------------------------
def get_schedule_html_for_date(d: date, date_iso: str) -> str:

    today = jst_today()

    if d != today:
        yyyymmdd = d.strftime("%Y%m%d")
        arch     = DIR_HTML / f"{yyyymmdd}html.txt"

        if arch.exists():
            return arch.read_text(encoding="utf-8", errors="ignore")

    return fetch_schedule_html(date_iso)

# ---------------------------------------------------------
def update_grade_held(date_iso:str, rows:List[Dict], overwrite:bool=False):

    total = 0

    with sqlite3.connect(str(DB_PATH)) as c:
        for r in rows:
            vid = r.get('vid')
            if not vid: continue

            venue_id = int(vid)
            hd       = r.get('hd')

            if hd and len(hd) == 8:
                d2 = f"{hd[:4]}-{hd[4:6]}-{hd[6:8]}"
                if d2 != date_iso: continue

            grade_s = r.get('grade')
            grade_n = GRADE_TO_NUM.get(grade_s) if grade_s else None
            held_t  = r.get('held_type')

            if overwrite:
                sql = """
                    UPDATE Race_programs
                       SET grade     = COALESCE(?,     grade),
                           held_type = COALESCE(?, held_type)
                     WHERE date      = ?
                       AND venue_id  = ?
                      """
                params = (grade_n, held_t, date_iso, venue_id)

            else:
                sql = """
                    UPDATE Race_programs
                       SET grade     = COALESCE(grade,     ?),
                           held_type = COALESCE(held_type, ?)
                     WHERE date      = ?
                       AND venue_id  = ?
                      """
                params = (grade_n, held_t, date_iso, venue_id)

            cur    = c.execute(sql, params)
            total += cur.rowcount
        c.commit()

    return total

# ---------------------------------------------------------
def update_program_all_ladies(date_iso:str, rows:List[Dict]):

    total = 0

    with sqlite3.connect(str(DB_PATH)) as c:

        for r in rows:
            vid = r[0]
            if not vid: continue

            venue_id = int(vid)
            hd       = r[1]

            if hd and len(hd) == 8:
                d2 = f"{hd[:4]}-{hd[4:6]}-{hd[6:8]}"
                if d2 != date_iso: continue

            cur = c.execute("""
                UPDATE Race_programs
                   SET all_ladies = 1
                 WHERE date      = ?
                   AND venue_id  = ?
                """, (date_iso, venue_id))

            total += cur.rowcount

        c.commit()

    return total

# ------------- 取得HTMLと抽出結果ﾘｽﾄをﾃｷｽﾄ出力 ------------
def dump_schedule_files(d:date, html:str, rows:List[Dict]):

    yyyymmdd = d.strftime("%Y%m%d")
    date_iso = d.strftime("%Y-%m-%d")

    ( DIR_HTML / f"{yyyymmdd}html.txt").write_text( html, encoding="utf-8",
                                                                 errors="ignore" )

    lines: List[str] = []
    for r in rows:
        vid       = r.get('vid')   or ''
        grade     = r.get('grade') or ''
        grade_num = GRADE_TO_NUM.get(grade, '') if grade else ''
        held_type = '' if r.get('held_type') is None else str(r['held_type'])
        heldt     = r.get('heldt') or ''

        lines.append( ",".join([date_iso, str(vid), grade, str(grade_num),
                                                        held_type, heldt]) )

    (DIR_TEXT / f"{yyyymmdd}.txt").write_text("\n".join(lines), encoding="utf-8",
                                                                   errors="ignore" )
# ---------------------------------------------------------
def iter_target_dates(args: argparse.Namespace) -> List[date]:

    if args.date and (args.date_from or args.date_to):
        print("date / (date_from , date_to) 両方の指定はできません")
        raise SystemExit(2)

    if (args.date_from and not args.date_to) or (args.date_to and not args.date_from):
        print("期間指定は --date_from と --date_to を併せて指定してください")
        raise SystemExit(2)

    if args.date: return [dt.strptime(args.date, "%Y-%m-%d").date()]

    if args.date_from and args.date_to:
        d0 = dt.strptime(args.date_from, "%Y-%m-%d").date()
        d1 = dt.strptime(args.date_to,   "%Y-%m-%d").date()

        if d1 < d0: d0, d1 = d1, d0

        days = (d1 - d0).days

        return [d0 + timedelta(days=i) for i in range(days + 1)]

    return [jst_today()]

# ==============================================================================
def parse_args():

    p = argparse.ArgumentParser(description="Bﾌｧｲﾙ取得Insert")
    p.add_argument("--date",                           help="対象日(YYYY-MM-DD)")
    p.add_argument("--date_from",                      help="期間開始(YYYY-MM-DD)")
    p.add_argument("--date_to",                        help="期間終了(YYYY-MM-DD)")
    p.add_argument("--overwrite", action="store_true", help="上書きﾓｰﾄﾞ")
    p.add_argument("--html",                           help="HTML(PATH)指定")

    return p.parse_args()

# ============================= メイン ===============================
def main() -> int:

    args   = parse_args()
    dates  = iter_target_dates(args)
    today  = jst_today()

    for d in dates:
        yymmdd   = d.strftime("%y%m%d")
        date_iso = f"20{yymmdd[:2]}-{yymmdd[2:4]}-{yymmdd[4:6]}"

        print(f"        [target] : {date_iso} ({yymmdd})")

        txt_path, lzh_path = ensure_txt_for_date(d)

        raw  = txt_path.read_text(encoding="shift_jis", errors="ignore")
        s    = raw.find("STARTB")
        e    = raw.rfind("FINALB")
        text = raw[s:e] if (s != -1 and e != -1 and e > s) else raw

        rows:List[Tuple[int,int,int,str,int,str,int,int,float,int,float,int,float]] = []

        for venue_id, block in split_venue_blocks(text):
            for r in parse_block(venue_id, block, d): rows.append(r)

        inserted = insert_programs(rows, overwrite=args.overwrite)
        print(f"          INSERT : rows = {inserted} / parsed = {len(rows)}")

        if txt_path.parent != DIR_B_TXT:
            dest = DIR_B_TXT / txt_path.name

            try:
                shutil.move(str(txt_path), str(dest))
                print(f"        archived : {dest}")
            except shutil.Error:
                dest.unlink(missing_ok=True)
                shutil.move(str(txt_path), str(dest))
                print(f"archived(replace): {dest}")

        if lzh_path and lzh_path.exists():
            try: lzh_path.unlink(); print(f"     deleted LZH : {lzh_path.name}")
            except Exception as e:  print(f"     delete 失敗 : {lzh_path} ({e})")

        html       = get_schedule_html_for_date(d, date_iso)
        sched_rows = parse_schedule_html(html)
        dump_schedule_files(d, html, sched_rows)

        updated1   = update_grade_held(date_iso, sched_rows, overwrite=False)
        venus_rows = parse_venus_from_html(html)
        updated2   = update_program_all_ladies(date_iso, venus_rows)
        print(f"          UPDATE : (all_ladies) rows = {updated2}")

        if d == today: time.sleep(1)

    print("done.")

    return 0

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    raise SystemExit(main())