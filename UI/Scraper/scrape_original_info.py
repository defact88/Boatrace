# -*- coding: utf-8 -*-
# C:\boatrace\UI\Scraper\scrape_original_info.py

import re, random, time
from bs4       import BeautifulSoup
from curl_cffi import requests

# -------------------------------------------
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

SPEC = {  1: ("/modules/yosou/cyokuzen.php?day={ymd}&race={r}",                False),
          5: ("/modules/yosou/oriten.php?day={ymd}&race={r}",                  False),
          6: (_GRP,                                                            False),
          8: (_GRP,                                                            False),
          9: ("/modules/yosou/group-tenji.php?day={ymd}&race={r}&kind=1&if=1", False),
         10: (_GRP,                                                            False),
         11: ("/modules/yosou/cyokuzen.php?day={ymd}&race={r}&kind=2&if=1",    False),
         12: (_ASP.replace("{page}", "st02"),                                  True ),
         13: (_GRP,                                                            False),
         14: (_GRP,                                                            False),
         15: (_ASP.replace("{page}", "yoso05"),                                True ),
         16: (_ASP.replace("{page}", "st02"),                                  True ),
         19: (_GRP,                                                            False),
         20: (_GRP,                                                            False),
         21: (_GRP,                                                            False),
         23: (_GRP,                                                            False), }

SUPPORTED = frozenset(SPEC)

HEADERS = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3", }

FIELDS = ("time_lap", "time_turning", "time_acceleration")

_LABELS = ( ("time_lap",          ("一周", "半周", "1周")),
            ("time_turning",      ("まわり足", "回り足" )),
            ("time_acceleration", ("直線",              )), )

_NUM    = re.compile(r"^\d+(?:\.\d+)?$")

# ----------------------------------------------------------
def is_today_only(venue_id:int) -> bool:

    return SPEC[venue_id][1]

# ----------------------------------------------------------
def _to_float(s):

    s = (s or "").strip()

    return float(s) if _NUM.match(s) else None

# ----------------------------------------------------------
def _span(tag, name):

    try:             return max(1, int(tag.get(name, 1)))
    except ValueError: return 1

# ----------------------------------------------------------
def build_url(venue_id:int, ymd:str, race_no:int) -> str:

    tpl = SPEC[venue_id][0]

    return "https://www." + VENUE[venue_id] + tpl.format(ymd=ymd, r=race_no, v=venue_id)

# ----------------------------------------------------------
def fetch_html(url:str) -> str:

    with requests.Session(impersonate="firefox") as s:
        s.headers.update(HEADERS)
        time.sleep(random.uniform(1.0, 2.0))
        res = s.get(url, timeout=10)
        res.raise_for_status()

        return res.text

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

## ----------------------------------------------------------
def parse_original(html:str) -> dict:

    soup  = BeautifulSoup(html, "lxml")
    table = _find_table(soup)
    if table is None: return {}
    cols  = _header_columns(table)
    if not cols:      return {}

    out = {}
    for tr in table.find_all("tr"):
        tds = tr.find_all("td", recursive=False)
        if not tds: continue
        first = tds[0].get_text("", strip=True)
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