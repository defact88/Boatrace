# -*- coding: utf-8 -*-
# C:\boatrace\UI\Scraper\get_oriten_info.py

import Dal as dal
import argparse, sys, re, random, time
from datetime  import datetime as dt, date
from bs4       import BeautifulSoup
from curl_cffi import requests

#=====================================================================
VENUE = {  1:"kiryu-kyotei.com",         2:"boatrace-toda.jp",       3:"boatrace-edogawa.com",
           4:"heiwajima.gr.jp",          5:"boatrace-tamagawa.com",  6:"boatrace-hamanako.jp",
           7:"gamagori-kyotei.com",      8:"boatrace-tokoname.jp",   9:"boatrace-tsu.com",
          10:"boatrace-mikuni.jp",      11:"boatrace-biwako.jp",    12:"boatrace-suminoe.jp",
          13:"boatrace-amagasaki.jp",   14:"n14.jp",                15:"marugameboat.jp",
          16:"kojimaboat.jp",           17:"boatrace-miyajima.com", 18:"boatrace-tokuyama.jp",
          19:"boatrace-shimonoseki.jp", 20:"wmb.jp",                21:"boatrace-ashiya.com",
          22:"boatrace-fukuoka.com",    23:"boatrace-karatsu.jp",   24:"omurakyotei.jp"        }

_GRP   = "/modules/yosou/group-cyokuzen.php?day={ymd}&race={r}&kind=2&if=1"
_ASP   = "/asp/kyogi/{v:02d}/pc/{page}{r:02d}.htm"

SPEC = {  1: ("/modules/yosou/cyokuzen.php?day={ymd}&race={r}",                   False),
          4: (_ASP.replace("{page}", "yoso05"),                                   True ),
          5: ("/modules/yosou/oriten.php?day={ymd}&race={r}",                     False),
          6: (_GRP,                                                               False),
          8: (_GRP,                                                               False),
          9: ("/modules/yosou/group-tenji.php?day={ymd}&race={r}&kind=1&if=1",    False),
         10: (_GRP,                                                               False),
         11: ("/modules/yosou/cyokuzen.php?day={ymd}&race={r}&kind=2&if=1",       False),
         12: (_ASP.replace("{page}", "st02"),                                     True ),
         13: (_GRP,                                                               False),
         14: (_GRP,                                                               False),
         15: (_ASP.replace("{page}", "yoso05"),                                   True ),
         16: (_ASP.replace("{page}", "st02"),                                     True ),
         18: ("/modules/yosou/tenji.php?day={ymd}&race={r}&if=1",                 False),
         19: (_GRP,                                                               False),
         20: (_GRP,                                                               False),
         21: (_GRP,                                                               False),
         23: (_GRP,                                                               False),
         24: ("/yosou/include/new_top_iframe_chokuzen_2.php?day={ymd}&race={r}",  False), }

# 2, 7, 17

NO_WWW = frozenset({24})

SUPPORTED = frozenset(SPEC)

HEADERS = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3", }

FIELDS = ("time_lap", "time_turning", "time_acceleration")

_LABELS = ( ("time_lap",          ("一周", "半周", "1周") ),
            ("time_turning",      ("まわり足", "回り足")  ),
            ("time_acceleration", ("直線",)               ), )

_NUM = re.compile(r"^\d+(?:\.\d+)?$")

# ----------------------------------------------------------
def is_today_only(venue_id:int) -> bool:

    return SPEC[venue_id][1]

# ----------------------------------------------------------
def build_url(venue_id:int, ymd:str, race_no:int) -> str:

    tpl = SPEC[venue_id][0]
    host = VENUE[venue_id] if venue_id in NO_WWW else "www." + VENUE[venue_id]

    return "https://" + host + tpl.format(ymd=ymd, r=race_no, v=venue_id)
# ----------------------------------------------------------
def fetch_html(url:str) -> str:

    with requests.Session(impersonate="firefox") as s:
        s.headers.update(HEADERS)
        time.sleep(random.uniform(1.0, 2.0))
        res = s.get(url, timeout=10)
        res.raise_for_status()

        return res.text
# ----------------------------------------------------------
def _to_float(s):

    s = (s or "").strip()

    return float(s) if _NUM.match(s) else None

# ----------------------------------------------------------
def _span(tag, name):

    try:               return max(1, int(tag.get(name, 1)))
    except ValueError: return 1

# ----------------------------------------------------------
def _header_columns(table):

    thead = table.find("thead")
    rows  = thead.find_all("tr") if thead else []
    if not rows:
        rows = [tr for tr in table.find_all("tr") if tr.find("th") and not tr.find("td")]

    grid = {}
    for r, tr in enumerate(rows):
        c = 0
        for th in tr.find_all(["th", "td"], recursive=False):
            while (r, c) in grid: c += 1
            text = th.get_text("", strip=True)
            for dr in range(_span(th, "rowspan")):
                for dc in range(_span(th, "colspan")):
                    grid[(r + dr, c + dc)] = text
            c += _span(th, "colspan")

    ncols = max((c for _, c in grid), default=-1) + 1
    cols  = {}
    for c in range(ncols):
        for r in range(len(rows) - 1, -1, -1):
            t   = grid.get((r, c), "")
            hit = next((f for f, keys in _LABELS if t in keys), None)
            if hit:
                cols[c] = hit
                break

    return cols

# ----------------------------------------------------------
def _find_table(soup):

    for t in soup.find_all("table"):
        heads = " ".join(th.get_text("", strip=True) for th in t.find_all("th"))
        if ("まわり足" in heads or "回り足" in heads) and ("一周" in heads or "半周" in heads):
            return t

    return None

# ----------------------------------------------------------
def parse_heiwajima(html:str) -> dict:

    soup  = BeautifulSoup(html, "lxml")
    table = soup.select_one("table.table_yoso06")
    if table is None: return {}

    out = {}
    for tr in table.find_all("tr"):
        th = tr.find("th", class_="col3")
        if th is None or th.get_text("", strip=True) != "タイム": continue

        tds   = tr.find_all("td", recursive=False)
        first = tds[0].get_text("", strip=True) if tds else ""
        if not first.isdigit() or not 1 <= int(first) <= 6: continue

        vals = [td.get_text("", strip=True) for td in th.find_next_siblings("td")]
        if len(vals) < 3: continue

        out[int(first)] = { "time_lap":          _to_float(vals[0]),
                            "time_turning":      _to_float(vals[1]),
                            "time_acceleration": _to_float(vals[2]), }

    return out

# ----------------------------------------------------------
def parse_omura(html:str) -> dict:

    soup  = BeautifulSoup(html, "lxml")
    table = soup.select_one("table#tblchokuzen_detail")
    if table is None: return {}

    cols, out = {}, {}
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"], recursive=False)
        if not cells: continue

        if not cols:
            for i, c in enumerate(cells):
                t = c.get_text("", strip=True)
                for f, keys in _LABELS:
                    if t in keys: cols[i] = f
            continue

        m = None
        for c in cells:
            m = next((re.fullmatch(r"tei([1-6])", k) for k in (c.get("class") or [])
                      if re.fullmatch(r"tei([1-6])", k)), None)
            if m: break
        if not m: continue

        rec = {f: None for f in FIELDS}
        for ci, field in cols.items():
            if ci < len(cells): rec[field] = _to_float(cells[ci].get_text("", strip=True))
        out[int(m.group(1))] = rec

    return out

PARSERS = {4:parse_heiwajima, 24:parse_omura}
# ----------------------------------------------------------
def parse_oriten(html:str, venue_id:int=None) -> dict:

    if venue_id in PARSERS:
        return PARSERS[venue_id](html)

    soup  = BeautifulSoup(html, "lxml")
    table = _find_table(soup)
    if table is None: return {}
    cols  = _header_columns(table)
    if not cols:      return {}

    out = {}
    for tr in table.find_all("tr"):
        tds = tr.find_all("td", recursive=False)
        if not tds: continue

        wk    = next((td for td in tds if "waku" in (td.get("class") or [])), tds[0])
        first = wk.get_text("", strip=True)
        if not first.isdigit() or not 1 <= int(first) <= 6: continue

        cells, c = {}, 0
        for td in tds:
            for _ in range(_span(td, "colspan")):
                cells[c] = td.get_text("", strip=True)
                c += 1

        rec = {f: None for f in FIELDS}
        for ci, field in cols.items():
            rec[field] = _to_float(cells.get(ci))
        out[int(first)] = rec

    return out

# ----------------------------------------------------------
def build_ids(d_iso:str, venue_id:int, race_no:int, frame_no:int):

    ymd      = dt.strptime(d_iso, "%Y-%m-%d").strftime("%y%m%d")
    race_id  = int(f"{ymd}{venue_id:02d}{race_no:02d}")
    entry_id = int(f"{ymd}{venue_id:02d}{race_no:02d}{frame_no}")

    return race_id, entry_id

# ----------------------------------------------------------
def fetch_frames(d_iso:str, venue_id:int, race_no:int) -> dict:

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

    parsed    = parse_oriten(html, args.venue)
    not_ready = [ fr for fr, absent in frames.items()
                  if not absent and not any( (parsed.get(fr) or {}).get(f) is not None
                                             for f in FIELDS ) ]
    if not_ready:
        print(f"page update yet (not ready frames={not_ready})"); return 2

    upsert_Oriten(args.date, args.venue, args.race, parsed, frames)
    print(f"[OK] Upsert: {args.date} jcd={args.venue} {args.race}R")

    return 0

# ====================================================================
if __name__ == "__main__":
    sys.exit(main())