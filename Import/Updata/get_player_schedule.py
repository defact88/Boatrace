# -*- coding: utf-8 -*-
# C:\boatrace\Import\Updata\get_player_schedule.py

import sys, argparse, re, warnings, random, time
from bs4       import BeautifulSoup, XMLParsedAsHTMLWarning
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

URL = "https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban={player_id}"

GRADE_IDX = {"一般":0, "G3":1, "G2":2, "G1":3, "PG1":4, "SG":5, "ippan":0}
GRADE_RE  = re.compile(r"is-(SG|PG1|G1|G2|G3|ippan)")

# ------------------------------------------------------------
def fetch_profile_html(player_id:int):

    url = URL.format(player_id=player_id)

    with requests.Session(impersonate="firefox") as session:
        session.headers.update(HEADERS)
        try:
            time.sleep(random.uniform(1.2, 1.8))
            res = session.get(url, timeout=15)
            res.raise_for_status()
            return res

        except Exception as e:
            print(f"HTML取得エラー(player_id={player_id}): {e}")
            return None

# ------------------------------------------------------------
def _grade_from_td(td) -> int|None:
    # 戻り値はDB規約に合わせたグレードコード(0-5): GRADE_IDX参照

    if td is None: return None

    cls = " ".join(td.get("class", []))
    m   = GRADE_RE.search(cls)

    return GRADE_IDX.get(m.group(1)) if m else None

# ------------------------------------------------------------
def _venue_id_from_jcd(a_tag) -> int|None:
    # jcd=01-24 はそのままDBのvenue_idと一致する

    if a_tag is None: return None

    href = a_tag.get("href", "")
    m    = re.search(r"jcd=(\d+)", href)
    if not m: return None

    jcd = int(m.group(1))
    return jcd if 1 <= jcd <= 24 else None

# ------------------------------------------------------------
def _find_table(soup:BeautifulSoup, label:str):

    for h3 in soup.find_all("h3", class_="title9_title"):
        span = h3.find("span", class_="title9_mainLabel")
        if not (span and label in span.text):
            continue

        title_div = h3.find_parent("div", class_="title9")
        if not title_div: continue

        table_div = title_div.find_next_sibling("div", class_="table1")
        return table_div.find("table") if table_div else None

    return None

# ------------------------------------------------------------
def parse_schedule_today(soup:BeautifulSoup) -> str|None:

    table = _find_table(soup, "本日出走予定")
    if not table: return None

    tbody = table.find("tbody")
    if not tbody: return None

    tr = tbody.find("tr")
    if not tr: return None

    tds = tr.find_all("td")
    if len(tds) < 7: return None

    d_text = tds[0].get_text(strip=True)
    grade  = _grade_from_td(tds[2])
    title  = tds[4].get_text(strip=True)
    venue  = _venue_id_from_jcd(tds[4].find("a"))
    rno1   = tds[5].get_text(strip=True)
    rno2   = tds[6].get_text(strip=True)

    rno_text = rno2 if rno2 and rno2 != "-" else rno1
    if not rno_text or rno_text == "-": return None

    m = re.search(r"\d+", rno_text)
    if not m: return None

    d_iso = d_text.replace("/", "-")

    return f"{d_iso},{title},{grade},{venue},{int(m.group())}"

# ------------------------------------------------------------
def parse_schedule_upcoming(soup:BeautifulSoup) -> list[str]:

    table = _find_table(soup, "出場予定")
    if not table: return []

    out = []
    for tbody in table.find_all("tbody"):
        tr = tbody.find("tr")
        if not tr: continue

        tds = tr.find_all("td")
        if len(tds) < 5: continue

        period = tds[0].get_text(separator="", strip=True)
        dates  = [p.strip() for p in period.split("～") if p.strip()]
        if len(dates) != 2: continue

        d_from = dates[0].replace("/", "-")
        d_to   = dates[1].replace("/", "-")
        grade  = _grade_from_td(tds[2])
        title  = tds[4].get_text(strip=True)
        venue  = _venue_id_from_jcd(tds[4].find("a"))

        out.append(f"{d_from},{d_to},{title},{grade},{venue}")

    return out[:4]

# ------------------------------------------------------------
def parse_player_schedule(soup:BeautifulSoup) -> dict:

    upcoming  = parse_schedule_upcoming(soup)
    upcoming += [None] * (4 - len(upcoming))

    return { "schedule_today": parse_schedule_today(soup),
             "schedule_1":     upcoming[0],
             "schedule_2":     upcoming[1],
             "schedule_3":     upcoming[2],
             "schedule_4":     upcoming[3],              }

# ------------------------------------------------------------
def upsert_player_schedule(player_id:int, soup:BeautifulSoup=None):

    if soup is None:
        res = fetch_profile_html(player_id)
        if not res: return
        soup = BeautifulSoup(res.text, "lxml")

    data = parse_player_schedule(soup)

    sql = """
            UPDATE Players
               SET schedule_today = ?,
                   schedule_1     = ?,
                   schedule_2     = ?,
                   schedule_3     = ?,
                   schedule_4     = ?
             WHERE player_id      = ?
          """

    params = ( data["schedule_today"], data["schedule_1"], data["schedule_2"],
               data["schedule_3"],     data["schedule_4"], player_id          )

    return dal.execute(sql, params)

# ------------------------------------------------------------
def active_player_ids(days:int=365) -> list[int]:

    rows = dal.fetch_all(
              """
                SELECT DISTINCT player_id
                  FROM Race_entries
                 WHERE date >= date('now', ?)
              """,
              (f"-{days} days",) )

    return [r[0] for r in rows]

# ------------------------------------------------------------
def update_all_schedules(days:int=365):

    ids = active_player_ids(days)
    n   = len(ids)

    for i, pid in enumerate(ids, 1):
        upsert_player_schedule(pid)
        print(f"[{i}/{n}] player_id={pid} 更新完了")

# ------------------------------------------------------------
def get_schedule(player:int=None, all:bool=False, regist_player:bool=False):

    if all:
        update_all_schedules()
    elif player:
        upsert_player_schedule(args.player)
    else:
        print("assignment player")

#=====================================================================
def main(argv=None):

    p = argparse.ArgumentParser()
    p.add_argument("--player",        type=int,            help="対象選手(player_id)")
    p.add_argument("--all",           action="store_true", help="直近1年出走選手を一括更新")
    p.add_argument("--regist_player", action="store_true", help="登録注目選手を一括更新")
    args = p.parse_args(argv)

    if args.all:
        update_all_schedules()
    elif args.player:
        upsert_player_schedule(args.player)
    else:
        print("assignment player")

#=====================================================================
if __name__ == "__main__":
    sys.exit(main())