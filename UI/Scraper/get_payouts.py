# -*- coding: utf-8 -*-
# get_payouts.py

import sys, argparse, re, warnings, random, time, unicodedata
from datetime  import datetime as dt
from bs4       import BeautifulSoup, FeatureNotFound, XMLParsedAsHTMLWarning
from curl_cffi import requests
import Dal as dal

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# ------------------------------------------------------------
HEADERS = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Connection": "keep-alive",                  }

# ------------------------------------------------------------
def fetch_payout_html(d_iso:str, v_id:int, rno:int) -> str:

    hd  = d_iso.replace("-", "")
    url = f"https://www.boatrace.jp/owpc/pc/race/raceresult?rno={rno}&jcd={v_id:02d}&hd={hd}"

    with requests.Session(impersonate="firefox") as session:
        session.headers.update(HEADERS)
        try:
            time.sleep(random.uniform(1.6,3.2))
            res = session.get(url, timeout=15)
            res.raise_for_status()
            return res

        except Exception as e:
            print(f"HTML取得エラー: {e}")
            return ""

# ------------------------------------------------------------
def parse_payouts_html(soup:BeautifulSoup) -> dict:

    results = { '3T':[], '3F':[], '2T':[], '2F':[], 'KK':[], 'TT':[], 'FF':[] }
    if not soup:
        return results

    tables       = soup.find_all("table", class_="is-w495")
    payout_table = None

    for tbl in tables:
        th = tbl.find("th")
        if th and "勝式" in th.text:
            payout_table = tbl
            break

    if not payout_table:
        return results

    bet_map      = { '3連単':'3T','3連複':'3F','2連単':'2T','2連複':'2F',
                     '拡連複':'KK', '単勝':'TT', '複勝':'FF'              }
    current_type = None

    for tr in payout_table.find_all("tr"):
        tds = tr.find_all("td")
        if not tds: continue

        idx_combo  = 0
        idx_payout = 1
        first_text = tds[0].text.strip()

        if first_text in bet_map:
            current_type = bet_map[first_text]
            idx_combo    = 1
            idx_payout   = 2

        if not current_type or len(tds) <= idx_payout:
            continue

        combo_str  = tds[idx_combo ].text.strip().replace('\xa0', '')
        payout_str = tds[idx_payout].text.strip().replace('\xa0', '')

        if not combo_str and not payout_str:
            continue

        payout_val = None
        if payout_str:
            p_nums = re.findall(r'\d+', payout_str.replace(',', ''))
            if p_nums:
                payout_val = int("".join(p_nums))

        combo_val = None

        if     "特払" in combo_str:
            combo_val = 8
        elif "不成立" in combo_str:
            combo_val = 0
            if payout_val is None: 
                payout_val = 0
        else:
            nums = re.findall(r'\d+', combo_str)
            if nums:
                combo_val = int("".join(nums))

        if combo_val is not None:
            results[current_type].append({'combo':combo_val, 'payout':payout_val})

    return results

# ------------------------------------------------------------
def _get_val(lst, idx, key, default):

    if idx < len(lst):
        v = lst[idx].get(key)
        return v if v is not None else default

    return default

# ------------------------------------------------------------
def build_combo_sets_from_parsed(results:dict) -> list[dict]:

    rows     = []
    n1       = max([len(results[k]) for k in ['3T', '3F', '2T', '2F', 'TT']] + [0])
    n_ff     = (len(results['FF']) + 1) // 2
    n_kk     = (len(results['KK']) + 2) // 3
    num_rows = max(1, n1, n_ff, n_kk)

    for i in range(num_rows):
        label = "normal" if i == 0 else f"tie_{i}"

        # 不在データ(非同着時のtie枠など)は全て None (SQLではNULL) とする
        c3T  = _get_val(results['3T'], i,     'combo', None)
        p3T  = _get_val(results['3T'], i,     'payout', None)
        c3F  = _get_val(results['3F'], i,     'combo', None)
        p3F  = _get_val(results['3F'], i,     'payout', None)
        c2T  = _get_val(results['2T'], i,     'combo', None)
        p2T  = _get_val(results['2T'], i,     'payout', None)
        c2F  = _get_val(results['2F'], i,     'combo', None)
        p2F  = _get_val(results['2F'], i,     'payout', None)
        cTT  = _get_val(results['TT'], i,     'combo', None)
        pTT  = _get_val(results['TT'], i,     'payout', None)

        cFF1 = _get_val(results['FF'], i*2,   'combo', None)
        pFF1 = _get_val(results['FF'], i*2,   'payout', None)
        cFF2 = _get_val(results['FF'], i*2+1, 'combo', None)
        pFF2 = _get_val(results['FF'], i*2+1, 'payout', None)

        cKK1 = _get_val(results['KK'], i*3,   'combo', None)
        pKK1 = _get_val(results['KK'], i*3,   'payout', None)
        cKK2 = _get_val(results['KK'], i*3+1, 'combo', None)
        pKK2 = _get_val(results['KK'], i*3+1, 'payout', None)
        cKK3 = _get_val(results['KK'], i*3+2, 'combo', None)
        pKK3 = _get_val(results['KK'], i*3+2, 'payout', None)

        rows.append( { "label":label,
                         "c3T":c3T,   "c3F":c3F,   "c2T":c2T,   "c2F":c2F,   "cTT":cTT,
                        "cFF1":cFF1, "cFF2":cFF2, "cKK1":cKK1, "cKK2":cKK2, "cKK3":cKK3,
                         "p3T":p3T,   "p3F":p3F,   "p2T":p2T,   "p2F":p2F,   "pTT":pTT,
                        "pFF1":pFF1, "pFF2":pFF2, "pKK1":pKK1, "pKK2":pKK2, "pKK3":pKK3  } )

    return rows

# ------------------------------------------------------------
def build_ids(d_iso:str, venue_id:int, race_no:int) -> int:

    _date   = dt.strptime(d_iso, "%Y-%m-%d")
    ymd     = _date.strftime("%y%m%d")
    race_id = int(f"{ymd}{venue_id:02d}{race_no:02d}")

    return race_id

# ------------------------------------------------------------
def upsert_payouts(d_iso:str, venue_id:int, race_no:int, soup:BeautifulSoup=None):

    race_id = build_ids(d_iso, venue_id, race_no)

    if soup is None:
        res = fetch_payout_html(d_iso, venue_id, race_no)
        if not res: return
        soup = BeautifulSoup(res.text,"lxml")

    results = parse_payouts_html(soup)

    if not any(results.values()):
        return

    combo_sets = build_combo_sets_from_parsed(results)

    sql = """
            INSERT INTO Payouts( race_id, date, venue_id, race_no, status,
                                 combo_3T,   combo_3F,   combo_2T,   combo_2F,   combo_TT,
                                 combo_FF1,  combo_FF2,  combo_KK1,  combo_KK2,  combo_KK3,
                                 payout_3T,  payout_3F,  payout_2T,  payout_2F,  payout_TT,
                                 payout_FF1, payout_FF2, payout_KK1, payout_KK2, payout_KK3 )

            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

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

    params = [ ( race_id,  d_iso, venue_id, race_no,
                 r["label"],
                 r["c3T"],  r["c3F"],  r["c2T"],  r["c2F"],  r["cTT"],
                 r["cFF1"], r["cFF2"], r["cKK1"], r["cKK2"], r["cKK3"],
                 r["p3T"],  r["p3F"],  r["p2T"],  r["p2F"],  r["pTT"],
                 r["pFF1"], r["pFF2"], r["pKK1"], r["pKK2"], r["pKK3"], ) for r in combo_sets ]

    return dal.executemany(sql, params)

#=====================================================================
def main(argv=None):

    p = argparse.ArgumentParser()
    p.add_argument("--date",  required=True, help="対象日(yyyy-mm-dd)")
    p.add_argument("--venue", required=True, help="対象開催場(int)")
    p.add_argument("--race",  required=True, help="対象レース(int)")
    p.add_argument("--overwrite", action="store_true",  help="上書きﾓｰﾄﾞ")
    args = p.parse_args(argv)

    upsert_payouts(args.date, int(args.venue), int(args.race))

#=====================================================================
if __name__ == "__main__":
    sys.exit(main())