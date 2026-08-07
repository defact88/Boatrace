# -*- coding: utf-8 -*-
# C:\boatrace\Import\insert_newcomer.py
from __future__ import annotations

import argparse, time, sqlite3, re, subprocess, sys, requests
from pathlib            import Path
from typing             import Optional, Dict
from bs4                import BeautifulSoup
from requests.adapters  import HTTPAdapter
from urllib3.util.retry import Retry

DB_PATH       = r"C:\boatrace\boatrace.db"
ARCHIVE_DIR   = Path(r"C:\boatrace\archive\FAN_newcomer")
DL_PLAYER_IMG = r"C:\boatrace\Import\DL_player_img.py"
PROFILE_URL   = "https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban={pid}"

HEADERS = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Connection": "keep-alive",}

# --------------- HTTP ---------------
def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    retry = Retry(total            = 5,
                  connect          = 5,
                  read             = 5,
                  backoff_factor   = 0.6,
                  status_forcelist = [429,500,502,503,504],
                  allowed_methods  = ["GET"], raise_on_status=False,  )

    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://",  HTTPAdapter(max_retries=retry))
    return s
# --------------- Parse ---------------
RE_CM = re.compile(r"(\d+)cm")
RE_KG = re.compile(r"(\d+)kg")
RE_KI = re.compile(r"^(\d+)\s*期$")

def _text(el) -> str:
    return (el.get_text(strip=True) if el else "").strip()
#-------------------------------------------------------------------------------
def parse_profile(html: str) -> Dict[str, str]:
    soup  = BeautifulSoup(html, "html.parser")
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
    m_h = RE_CM.search(height or "");  height_cm = int(m_h.group(1)) if m_h else None
    m_w = RE_KG.search(weight or "");  weight_kg = int(m_w.group(1)) if m_w else None
    m_rp= RE_KI.search(rp_txt or "");  regist_period = int(m_rp.group(1)) if m_rp else None

    return dict(
        player_id     = player_id,     name      = name,      name_kana = kana,
        birthday      = birthday,      height_cm = height_cm, weight_kg = weight_kg,
        blood_type    = blood,         regions   = regions,  birthplace = birthplace,
        regist_period = regist_period, class_now = class_now,  )

# --------------- DB ---------------
def insert_player(c:sqlite3.Connection, row:Dict[str, Optional[str]]) -> bool:

    sql = """
    INSERT INTO Players
      (player_id, name,      name_kana,  sex,        age,      regist_period,
       regions,   height,    weight,     blood_type, birthday, birthplace,
       flying_st, late_st,   class_now)
    VALUES (?, ?, ?, '男', NULL, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
    """
    try:
        c.execute(sql, (
            row["player_id"],     row["name"],       row["name_kana"],
            row["regist_period"], row["regions"],    row["height_cm"],
            row["weight_kg"],     row["blood_type"], row["birthday"],
            row["birthplace"],    row["class_now"],
        ))
        return True
    except sqlite3.IntegrityError: return False

# --------------- Archive (TSV) ---------------
TSV_ORDER = ["player_id","name","name_kana","sex","regist_period","regions",
             "height_cm","weight_kg","blood_type","birthday","birthplace","class_now"]
def save_tsv(regist_period: int, row: Dict[str, Optional[str]]) -> None:
    outdir = ARCHIVE_DIR / str(regist_period)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{row['player_id']}.txt"
    vals = [
        str(row["player_id"] or ""),
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
        row.get("class_now","")  or "",
    ]
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
def call_dl_player_img(pid: int) -> None:
    try:
        py        = sys.executable or "python"
        dl_result = subprocess.run([py, DL_PLAYER_IMG, str(pid)],
                                    cwd    = str(Path(DL_PLAYER_IMG).parent),
                                    stdout = subprocess.DEVNULL,
                                    stderr = subprocess.DEVNULL,
                                    check  = False)
    except Exception: pass; return False
    return dl_result
#-------------------------------------------------------------------------------
def main():
    args = parse_args()
    rp   = args.rp
    a, b = int(args.from_id), int(args.to_id)
    if a > b: a, b = b, a

    sess  = make_session()
    total = inserted = dl_img =  0

    with sqlite3.connect(DB_PATH) as c:
        c.execute("PRAGMA foreign_keys=ON;")
        for pid in range(a, b+1):
            total += 1
            url    = PROFILE_URL.format(pid=pid, rp=rp)
            try:
                r = sess.get(url, timeout=(5, 30))
                if r.status_code != 200 or not r.text:
                    time.sleep(args.sleep); continue
                row                  = parse_profile(r.text)
                row["regist_period"] = rp
                row["player_id"]     = row["player_id"] or pid
                if not row["player_id"] or not row["name"]:
                    time.sleep(args.sleep); continue
                ok = insert_player(c, row)
                if ok:
                    inserted += 1
                    save_tsv(rp, row)
                dl_result = call_dl_player_img(row["player_id"])
                if dl_result: dl_img += 1 
            except Exception: pass
            finally: time.sleep(args.sleep)

    print(f"targets={total}, Inserted={inserted}")
    print(f"targets={total}, Download={dl_img}")
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
