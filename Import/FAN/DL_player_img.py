# -*- coding: utf-8 -*-
# C:\boatrace\Inport\DL_player_img.py

import re, time, sqlite3, argparse, sys, random
from pathlib   import Path
from typing    import List, Optional
from curl_cffi import requests

import Dal as dal

DB_PATH   = Path(r"C:\boatrace\boatrace.db")
SAVE_DIR  = Path(r"C:\boatrace\tmp\Assets\players")
PROFILE   = "https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban={pid}"

HEADERS = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Connection": "keep-alive",               }

#-------------------------------------------------------------------------------
def is_jpeg(b:bytes):

    return len(b) >= 3 and b[0]==0xFF and b[1]==0xD8 and b[2]==0xFF

#-------------------------------------------------------------------------------
def download_one(player_id:int, overwrite:bool=False, sleep_sec:float=0.6):

    outpath  = SAVE_DIR / f"{player_id}.jpg"
    img_url  = f"https://www.boatrace.jp/racerphoto/{player_id}.jpg"
    prof_url = PROFILE.format(pid=player_id)

    with requests.Session(impersonate="firefox") as s:
        s.headers.update(HEADERS)
        try:
            time.sleep(random.uniform(1.6,2.1))
            res = s.get(img_url, headers={"Referer":prof_url}, timeout=10)
            res.raise_for_status()
            html = res.text
            if res.status_code != 200:
                debug = SAVE_DIR / f"{player_id}.profile.html"
                debug.write_text(html, encoding="utf-8", errors="ignore")
                return False

            ctype = res.headers.get("Content-Type", "").lower()
            data  = res.content
            if "image" in ctype and is_jpeg(data):
                tmp = outpath.with_suffix(".jpg.part")
                tmp.write_bytes(data)
                tmp.replace(outpath)
                print(f"[OK] {player_id} -> {outpath.name} ({img_url})")
                time.sleep(sleep_sec)

                return True

        except Exception:
            print(f"[NG] 画像取得失敗: {player_id}")
            return False

#-------------------------------------------------------------------------------
def parse_args():

    ap = argparse.ArgumentParser(description="選手画像取得(対象:指定選手/DB内全選手)")
    ap.add_argument("--player_id", type=int,                help="対象=登録番号(単発実行)")
    ap.add_argument("--overwrite", action="store_true",     help="既存ﾌｧｲﾙも再取得")
    ap.add_argument("--sleep",     type=float, default=0.6, help="待機秒")
    args = ap.parse_args()

    main(args.player_id, args.overwrite, args.sleep)

#-------------------------------------------------------------------------------
def main(player_id:int=None, overwrite:bool=False, sleep=0.6):

    del_id = "profile.html"    # 仮(引退情報取得ﾌﾟﾛｾｽ追加後に適正化)

    if player_id:
        if not overwrite:
            target = [ player_id if not (SAVE_DIR / f"{player_id}.{del_id}").exists()
                                and not (SAVE_DIR / f"{player_id}.jpg").exists()
                               else None                                              ]
        else:
            target = [player_id]
    else:
        rows = dal.fetch_all("""
               SELECT player_id
                 FROM Players
             ORDER BY player_id
               """)

        pids = [int(r[0]) for r in rows]

        if not overwrite:
            target = [ pid for pid in pids if not (SAVE_DIR / f"{pid}.{del_id}").exists()
                                          and not (SAVE_DIR / f"{pid}.jpg").exists()      ]
        else:
            target = [pid for pid in pids]

    if not target or target[0] == None:
        print("[OK] 画像は取得済, 処理はありません。")
        return 0

    done, updated, failed = 0, 0, 0

    for pid in target:
        try:
            changed  = download_one(pid, sleep_sec=sleep)
            updated += int(changed)
            done    += 1

        except Exception as e:
            print(f"[ERR] {pid}: {e}")
            failed  += 1

    print(f"targets={len(target)}, updated={updated}, failed={failed}")

    if player_id:
        return 1 if done == 1 else 0

    else: sys.exit(0)

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    parse_args()
