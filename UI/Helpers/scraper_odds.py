# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\scraper_odds.py

import re, time, random, sys, argparse, os, warnings
from datetime           import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request     import urlopen
from curl_cffi          import requests
from bs4                import BeautifulSoup, FeatureNotFound, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BASE = "https://www.boatrace.jp/owpc/pc/race"

PAGES = { "3T"   : "/odds3t",
          "3F"   : "/odds3f",
          "2T_2F": "/odds2tf",
          "KK"   : "/oddsk",
          "TT_FF": "/oddstf", }

HEADERS = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Connection": "keep-alive", }

#----------- 低レベルヘルパ ------------
def _clean(txt:str) -> str:

    return re.sub(r'<[^>]+>', '', txt).strip()

#-----------------------------
def _is_int(v:str) -> bool:
    try:
        int(v)
        return True
    except:
        return False

#-----------------------------
def _boatno_cls(cls:str):

    m = re.search(r'is-boatColor(\d)', cls)

    return int(m.group(1)) if m else None

#-----------------------------
def _get_html(url:str, retry:int=3, wait:float=1.5) -> str:

    for i in range(retry):
        with requests.Session(impersonate="firefox") as session:
            session.headers.update(HEADERS)
            try:
                time.sleep(random.uniform(wait,2.5))
                res = session.get(url, timeout=12)
                return res.text
            except Exception:
                if i < retry - 1: time.sleep(wait)
                else: raise

#--------- テーブル構造ヘルパ ----------
def _get_col_headers(table_html:str) -> list:

    thead_m = re.search(r'<thead[^>]*>(.*?)</thead>', table_html, re.S)
    if not thead_m:
        return []
    ths = re.findall(r'<th([^>]*)>(.*?)</th>', thead_m.group(1), re.S)

    return [ int(_clean(t)) for c, t in ths
             if _boatno_cls(c) and 'borderLeftNone' not in c and _is_int(_clean(t)) ]

#-----------------------------
def _get_tbody_trs(table_html:str, cls_name:str = "is-p3-0") -> list:

    m = re.search(rf'<tbody class="{cls_name}">(.*?)</tbody>', table_html, re.S)
    if not m:
        return []

    return re.findall(r'<tr[^>]*>(.*?)</tr>', m.group(1), re.S)

#-----------------------------
def _find_table(page_html:str, title:str) -> str:

    m = re.search(title + r'.*?<table[^>]*>(.*?)</table>', page_html, re.S)

    return m.group(1) if m else ''

#---------------------- 3連単パーサ ------------------------
def parse_3T(table_html:str) -> dict:

    col       = _get_col_headers(table_html)
    trs       = _get_tbody_trs(table_html)
    result    = {}
    col_first = [None] * 6

    for tr_html in trs:
        tds = re.findall(r'<td([^>]*)>(.*?)</td>', tr_html, re.S)
        ci = 0
        i  = 0

        while i < len(tds):
            cls, txt = tds[i]
            v        = _clean(txt)
            rwsp     = bool(re.search(r'rowspan=', cls))
            op       = 'oddsPoint' in cls

            if rwsp:
                if _is_int(v) and ci < 6:
                    col_first[ci] = int(v)
                i += 1

            elif op:
                first  = col[ci] if ci < len(col) else None
                second = col_first[ci] if ci < 6 else None
                if i > 0 and second is not None and first and v:
                    sv = _clean(tds[i - 1][1])
                    if _is_int(sv):
                        third = int(sv)
                        if len({first, second, third}) == 3:
                            result[(first, second, third)] = v
                ci += 1
                i  += 1
            else:
                i  += 1

    return result

#---------------------- 3連複パーサ ------------------------
def parse_3F(table_html:str) -> dict:

    soup  = BeautifulSoup(table_html, "lxml")
    tbody = soup.find("tbody")
    rows  = tbody.find_all("tr")
    grid  = [[None] * 18 for _ in range(10)]

    for r_idx, tr in enumerate(rows):
        c_idx = 0
        for td in tr.find_all("td"):
            while c_idx < 18 and grid[r_idx][c_idx] is not None:
                c_idx += 1
            if c_idx >= 18:
                break

            rowspan     = int(td.get("rowspan", 1))
            colspan     = int(td.get("colspan", 1))
            is_disabled = "is-disabled" in td.get("class", [])
            val         = None if is_disabled else td.get_text(strip=True)

            for r in range(r_idx, r_idx + rowspan):
                for c in range(c_idx, c_idx + colspan):
                    if r < 10 and c < 18:
                        grid[r][c] = val
            c_idx += colspan

    result = {}

    for b in range(5):
        b1        = b + 1
        col_start = b * 3

        for r in range(10):
            b2_val   = grid[r][col_start]
            b3_val   = grid[r][col_start + 1]
            odds_val = grid[r][col_start + 2]

            if b2_val and b3_val and odds_val:
                try:
                    b2            = int(b2_val)
                    b3            = int(b3_val)
                    combo         = tuple(sorted([b1, b2, b3]))
                    result[combo] = odds_val

                except ValueError:
                    continue

    return result

#------------- 2連単/2連複/拡連複 共通パーサ ---------------
def parse_2boats(table_html:str, bet_type:str) -> dict:

    trs         = _get_tbody_trs(table_html)
    result      = {}
    R2_list     = [2, 1, 1, 1, 1, 1]

    for i, tr_html in enumerate(trs, 1):
        tds = re.findall(r'<td([^>]*)>(.*?)</td>', tr_html, re.S)
        tds = [(c, t) for c, t in tds if 'disabled' not in c]
        if not tds: continue

        fc, ft = tds[0]
        if not ('borderLeftNone' in fc and _is_int(ft)): continue

        odds_list  = [_clean(t) for c, t in tds if 'oddsPoint' in c]
        for R1, R2, odds_v in zip(range(1,7), R2_list, odds_list):
            if not odds_v:            continue
            if bet_type == '2T': key = (R1, R2)
            else:                     key = tuple(sorted([R1, R2]))
            result[key] = odds_v

        R2_list = [i + 2 if idx <= i else i + 1 for idx in range(6)]

    return result

#------------------ 単勝 / 複勝パーサ ----------------------
def parse_sp(page_html:str) -> tuple:

    TT = {}
    FF = {}

    for label, dic in [('単勝オッズ', TT), ('複勝オッズ', FF)]:
        m = re.search(label + r'.*?<table[^>]*>(.*?)</table>', page_html, re.S)
        if not m: continue

        for tb in re.findall(r'<tbody[^>]*>(.*?)</tbody>', m.group(1), re.S):
            for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', tb, re.S):
                tds       = re.findall(r'<td([^>]*)>(.*?)</td>', tr, re.S)
                boat_tds  = [(c, t) for c, t in tds if _boatno_cls(c)]
                odds_tds  = [(c, t) for c, t in tds if 'oddsPoint' in c]
                if boat_tds and odds_tds:
                    nv = _clean(boat_tds[0][1])
                    if _is_int(nv):
                        dic[int(nv)] = _clean(odds_tds[0][1])

    return TT, FF

#----------------- HTMLをページ別に分割 --------------------
def _split_pages(html:str) -> dict:

    parts  = re.split(r'PAGE TOP', html)
    pages  = {}
    labels = { '3連単'        :'3T',
               '3連複'        :'3F',
               '2連単・2連複' :'2T_2F',
               '拡連複'       :'KK',
               '単勝・複勝'   :'TT_FF', }

    for part in parts:
        m = re.search(r'<li class="is-active"><span>([^<]+)</span>', part)
        if m:
            key = labels.get(m.group(1).strip())
            if key:
                pages[key] = part

    return pages

#------------- メイン取得関数（並列フェッチ）---------------
def fetch_all_odds( date_str:str, venue_id:int, race_no:int, on_progress=None,
                    pages:tuple=tuple(PAGES.keys())                            ) -> dict:

    params = f"?rno={race_no}&jcd={venue_id:02d}&hd={date_str}"
    urls   = {key:BASE + PAGES[key] + params for key in pages}

    result = { "TT":{}, "FF":{}, "KK":{},
               "2T":{}, "2F":{}, "3T":{}, "3F":{},
               "updated":"", "final":False, "error":None, }
    errors = []
    htmls  = {}
    # --------------
    def _fetch(key, url):
        return key, _get_html(url)
    # --------------
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(_fetch, k, u):k for k, u in urls.items()}
        for fut in as_completed(futures):
            try:
                key, html  = fut.result()
                htmls[key] = html
                if on_progress:
                    on_progress(key)
            except Exception as e: errors.append(str(e))

    _parse_into(htmls, result)

    result["updated"] = dt.now().strftime("%H:%M:%S")

    if errors: result["error"] = " / ".join(errors)

    return result

#--------------------- パース統合 --------------------------
def _parse_into(htmls:dict, result:dict):

    if "3T" in htmls:
        result["final"] = "tab4_time" in htmls["3T"]
        tbl = _find_table(htmls["3T"], "3連単オッズ")
        result["3T"] = parse_3T(tbl)

    if "3F" in htmls:
        tbl = _find_table(htmls["3F"], "3連複オッズ")
        result["3F"] = parse_3F(tbl)

    if "2T_2F" in htmls:
        h = htmls["2T_2F"]
        result["2T"] = parse_2boats(_find_table(h, "2連単オッズ"), "2T")
        result["2F"] = parse_2boats(_find_table(h, "2連複オッズ"), "2F")

    if "KK" in htmls:
        tbl = _find_table(htmls["KK"], "拡連複オッズ")
        result["KK"] = parse_2boats(tbl, "KK")

    if "TT_FF" in htmls:
        ts, fk = parse_sp(htmls["TT_FF"])
        result["TT"] = ts
        result["FF"] = fk

#========= ローカルHTMLファイルからのパース（テスト用）===============
def parse_from_file(filepath:str) -> dict:

    with open(filepath, encoding="utf-8", errors="replace") as f:
        full_html = f.read()

    pages  = _split_pages(full_html)
    result = { "TT":{}, "FF":{}, "KK":{},
               "2T":{}, "2F":{}, "3T":{}, "3F":{},
               "updated":dt.now().strftime("%H:%M:%S"),
               "final":False,
               "error":None,                            }

    _parse_into(pages, result)

    return result

# -------------------- コマンドライン単体テスト ----------------------
if __name__ == "__main__":

    p = argparse.ArgumentParser(description="test")
    p.add_argument("html", nargs="?", help="file_path")
    args = p.parse_args()

    if os.path.exists(args.html):
        data = parse_from_file(args.html)
        for k, v in data.items():
            if isinstance(v, dict):
                print(f"{k}: {len(v)}件  例: {list(v.items())[:2]}")
            else:
                print(f"{k}: {v}")
    else:
        print("[Error] 指定パスにファイルが存在しません")