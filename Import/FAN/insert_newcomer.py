# -*- coding: utf-8 -*-
# C:\boatrace\Import\insert_newcomer.py
from __future__ import annotations

import argparse, time, sqlite3, re, sys, time, warnings
from pathlib   import Path
from typing    import Optional, Dict
from bs4       import BeautifulSoup, XMLParsedAsHTMLWarning
from curl_cffi import requests

import DL_player_img
import Dal as dal

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

ARCHIVE_DIR = Path(r"C:\boatrace\Archive\FAN\Newcomer")
PROFILE_URL = "https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban={pid}"

HEADERS = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",                   }

# --------------- Parse ---------------
RE_CM = re.compile(r"(\d+)cm")
RE_KG = re.compile(r"(\d+)kg")
RE_KI = re.compile(r"^(\d+)\s*期$")

def _text(el) -> str:
    return (el.get_text(strip=True) if el else "").strip()
#-------------------------------------------------------------------------------
def parse_profile(html:str) -> Dict[str, str]:

    soup  = BeautifulSoup(html, "lxml")
    name  = _text(soup.select_one(".racer1_bodyName"))
    kana  = _text(soup.select_one(".racer1_bodyKana"))
    items = {}

    for dl in soup.select("dl.list3"):
        dts = dl.find_all("dt")
        dds = dl.find_all("dd")
        for dt, dd in zip(dts, dds):
            items[_text(dt)] = _text(dd)

    pid_txt   = items.get("登録番号", "")
    birthday  = items.get("生年月日", "")
    height    = items.get("身長",     "")
    weight    = items.get("体重",     "")
    blood     = items.get("血液型",   "")
    regions   = items.get("支部",     "")
    birthplace= items.get("出身地",   "")
    rp_txt    = items.get("登録期",   "")
    class_now = items.get("級別",     "")

    player_id = int(re.sub(r"\D", "", pid_txt)) if pid_txt   else None
    birthday  = birthday.replace("/", "-")      if birthday  else None
    class_now = class_now.replace("級","")      if class_now else None
    m_h = RE_CM.search(height or "");  height_cm     = int(m_h.group(1))  if m_h else None
    m_w = RE_KG.search(weight or "");  weight_kg     = int(m_w.group(1))  if m_w else None
    m_rp= RE_KI.search(rp_txt or "");  regist_period = int(m_rp.group(1)) if m_rp else None

    return dict(
        player_id     = player_id,     name      = name,      name_kana = kana,
        birthday      = birthday,      height_cm = height_cm, weight_kg = weight_kg,
        blood_type    = blood,         regions   = regions,  birthplace = birthplace,
        regist_period = regist_period, class_now = class_now,  )

# --------------- DB ---------------
def insert_player(row:Dict[str, Optional[str]]) -> bool:

    sql = """
    INSERT INTO Players( player_id, name,    name_kana,  sex,        age,      regist_period,
                         regions,   height,  weight,     blood_type, birthday, birthplace,
                         flying_st, late_st, class_now                                        )
    VALUES (?, ?, ?, '男', NULL, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
    """

    cur = dal.execute(sql, (
        row["player_id"],     row["name"],       row["name_kana"],
        row["regist_period"], row["regions"],    row["height_cm"],
        row["weight_kg"],     row["blood_type"], row["birthday"],
        row["birthplace"],    row["class_now"],                    ))

    return cur

# --------------- Archive (TSV) ---------------
TSV_ORDER = ["player_id","name","name_kana","sex","regist_period","regions",
             "height_cm","weight_kg","blood_type","birthday","birthplace","class_now"]

def save_tsv(regist_period: int, row:Dict[str, Optional[str]]) -> None:

    outdir = ARCHIVE_DIR / str(regist_period)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{row['player_id']}.txt"

    vals = [ str(row["player_id"] or ""),
             row.get("name","")       or "",
             row.get("name_kana","")  or "",
             "男",
             str(regist_period),
             row.get("regions","")    or "",
             row.get("height_cm")     or "",
             row.get("weight_kg")     or "",
             row.get("blood_type","") or "",
             row.get("birthday","")   or "",
             row.get("birthplace","") or "",
             row.get("class_now","")  or "", ]

    path.write_text("\t".join(vals) + "\n", encoding="utf-8")

# --------------- CLI ---------------
def parse_args():

    ap = argparse.ArgumentParser(description="新人選手取得→Players INSERT")
    ap.add_argument("--rp",                   type=int, required=True, help="登録期")
    ap.add_argument("--from", dest="from_id", type=int, required=True, help="登番～")
    ap.add_argument("--to",   dest="to_id",   type=int, required=True, help="～登番")
    ap.add_argument("--sleep",                type=float, default=0.6, help="待機秒")

    return ap.parse_args()

#-------------------------------------------------------------------------------
def main():

    args = parse_args()
    rp   = args.rp
    a, b = int(args.from_id), int(args.to_id)

    total, inserted, dl_img = 0, 0, 0

    with requests.Session(impersonate="firefox") as s:
        s.headers.update(HEADERS)
        for pid in range(a, b+1):
            total += 1
            url    = PROFILE_URL.format(pid=pid)
            try:
                res = s.get(url, timeout=15)
                res.raise_for_status()
                if res.status_code != 200 or not res.text:
                    time.sleep(args.sleep)
                    continue
            except Exception: pass

            row = parse_profile(res.text)
            if not row["player_id"] or not row["name"]:
                time.sleep(args.sleep)
                continue
            row["regist_period"] = rp
            row["player_id"]     = pid

            ok = insert_player(row)
            if ok:
                inserted += 1
                save_tsv(rp, row)

            dl = DL_player_img.main(pid, overwrite=False)
            dl_img += dl
            print(pid)
            print(dl)

    print(f"targets={total}, Inserted={inserted}")
    print(f"targets={total}, Download={dl_img}")

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
