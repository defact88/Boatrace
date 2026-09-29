# -*- coding: utf-8 -*-
# C:\boatrace\Inport\DL_player_img.py

import re, time, sqlite3, argparse, requests
from pathlib            import Path
from requests.adapters  import HTTPAdapter
from urllib3.util.retry import Retry
from typing             import List, Optional

DB_PATH   = r"C:\boatrace\boatrace.db"
SAVE_DIR  = Path(r"C:\boatrace\tmp\Assets\players")
PROFILE   = "https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban={pid}"
#-------------------------------------------------------------------------------
def make_session() -> requests.Session:

    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BoatRaceDB/1.0",
        "Accept-Language": "ja,en;q=0.9",                                        })

    retry = Retry(
        total=5, connect=5, read=5,
        backoff_factor   = 0.6,
        status_forcelist = [429, 500, 502, 503, 504],
        allowed_methods  = ["GET"],
        raise_on_status  = False,                     )

    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://",  adapter)

    return s
#-------------------------------------------------------------------------------
def is_jpeg(b:bytes):
    return len(b) >= 3 and b[0]==0xFF and b[1]==0xD8 and b[2]==0xFF
#-------------------------------------------------------------------------------
def download_one(sess:requests.Session, player_id:int, overwrite:bool=False,
                 sleep_sec:float=0.6):

    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    outpath  = SAVE_DIR / f"{player_id}.jpg"
    prof_url = PROFILE.format(pid=player_id)
    r        = sess.get(prof_url, timeout=(5, 30))
    r.raise_for_status()
    html     = r.text
    img_url  = f"https://www.boatrace.jp/racerphoto/{player_id}.jpg"

    try:
        r2 = sess.get(img_url, headers={"Referer": prof_url}, timeout=(5, 30))
        if r2.status_code != 200:
            save_html(player_id, html); return False

        ctype = r2.headers.get("Content-Type", "").lower()
        data  = r2.content
        if "image" in ctype and is_jpeg(data):
            tmp = outpath.with_suffix(".jpg.part")
            tmp.write_bytes(data)
            tmp.replace(outpath)
            print(f"[OK] {player_id} -> {outpath.name} ({img_url})")
            time.sleep(sleep_sec)

            return True

    except requests.RequestException:
        debug = SAVE_DIR / f"{player_id}.profile.html"
        debug.write_text(html, encoding="utf-8", errors="ignore")
        print(f"[NG] 画像取得失敗: {player_id}  (saved {debug.name})")
        time.sleep(0.6)

        return False

#-------------------------------------------------------------------------------
def main():

    ap = argparse.ArgumentParser(description="選手画像取得(対象:指定選手/DB内全選手)")
    ap.add_argument("--overwrite", action="store_true",     help="既存ﾌｧｲﾙも再取得")
    ap.add_argument("--sleep",     type=float, default=0.6, help="待機秒")
    ap.add_argument("player_id",   type=int,   nargs="?",   help="対象=登録番号(単発実行)")

    args      = ap.parse_args()
    del_id    = "profile.html"    # 仮(引退情報取得ﾌﾟﾛｾｽ追加後に適正化)
    player_id = args.player_id

    if args.player_id:
        if not args.overwrite:
            target   = [player_id if not (SAVE_DIR / f"{player_id}.{del_id}").exists()
                                 and not (SAVE_DIR / f"{player_id}.jpg").exists()
                                else None                                              ]
        else: target = [player_id]
    else:
        with sqlite3.connect(DB_PATH) as c:
            c.execute("PRAGMA foreign_keys=ON;")
            sql     = "SELECT player_id FROM players ORDER BY player_id"
            rows    = c.execute(sql).fetchall()
            pids    = [int(r[0]) for r in rows]

        if not pids:
            print("[Info] Playersにﾃﾞｰﾀがありません。")
            return 0

        if not args.overwrite:
            target = [pid for pid in pids if not (SAVE_DIR / f"{pid}.{del_id}").exists()
                                         and not (SAVE_DIR / f"{pid}.jpg").exists()     ]

    if not target or target[0] == None:
        print("[OK] 画像は取得済, 処理はありません。"); return 0

    sess = make_session()
    done = updated = failed = 0
    for pid in target:
        try:
            changed  = download_one(sess, pid, overwrite=args.overwrite,
                                                    sleep_sec=args.sleep)
            updated += int(changed)
            done    += 1
        except Exception as e:
            print(f"[ERR] {pid}: {e}")
            failed  += 1

    print(f"\n=== SUMMARY ===")
    print(f"targets={len(target)}, downloaded/updated={updated}, failed={failed}")

    if args.player_id: return True if done == 1 else False

    else: return 0
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
    import sys
    rc = main()
    if   isinstance(rc, bool): sys.exit(0 if rc else 1)
    elif isinstance(rc, int):  sys.exit(rc)
    else:                      sys.exit(1)
