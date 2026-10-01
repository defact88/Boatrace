# -*- coding: utf-8 -*-
# C:\boatrace\Import\ETL_k_results.py

from pathlib   import Path
from datetime  import datetime as dt, timedelta
from typing    import List, Optional, Dict, Set, Iterable
from lhafile   import lhafile
from curl_cffi import requests
import argparse, sys, re, sqlite3, shutil, random, time
# ----------------- 外部依存 ---------------------
from parse_and_upsert    import upsert_Races, upsert_Race_entries, upsert_Payouts_from_K
from upsert_Grade        import upsert_Grade
import Dal as dal

# ------------------- パス -----------------------
BASE           = Path(r"C:\boatrace")
DIR_DL         = BASE / r"INBOX\DL\K"
DIR_INBOX      = BASE / r"INBOX\K"
DIR_ARC        = BASE / r"Archive\K"
DIR_ESCAPE_TXT = BASE / r"Archive\Escape\TXT"
DIR_ESCAPE_DL  = BASE / r"Archive\Escape\DL"
DB_PATH        = BASE / "boatrace.db"

HEADERS = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Connection": "keep-alive",
          }

VENUES = [ "桐  生", "戸  田", "江戸川", "平和島", "多摩川", "浜名湖", "蒲  郡", "常  滑",
           "  津  ", "三  国", "びわこ", "住之江", "尼  崎", "鳴  門", "丸  亀", "児  島",
           "宮  島", "徳  山", "下  関", "若  松", "芦  屋", "福  岡", "唐  津", "大  村"  ]

#---------------- ユーティリティ -----------------
def daterange(d0:dt, d1:dt):

    cur = d0
    while cur <= d1:
        yield cur
        cur = cur +timedelta(days=1)
#-----------------------------
def date_from_filename(name:str):

    m = re.search(r"K(\d{2})(\d{2})(\d{2})\.TXT", name, re.I)
    y2, mo, da = map(int, m.groups())

    return f"20{y2:02d}-{mo:02d}-{da:02d}"
#-----------------------------
def ask_yes_no(prompt:str) -> bool:

    try:
        ans = input(prompt).strip().lower()
        if ans in ("y", "yes"): return True
        if ans in ("n", "no"):  return False
    except: return False
#-----------------------------------------------------------
def ensure_empty_delete(path:Path, label:str, external:bool) -> bool:

    items = list(path.glob("*"))
    if not items: return True

    if external:
        [p.unlink(missing_ok=True) for p in items if p.is_file()]
        return True

    print(f"[注意] {label} に {len(items)} 件ファイルが残っています")
    ans = ask_yes_no("全削除して処理を開始しますか？ [Y/N]: ")
    if not ans:
        print("選択により実行中止しました")
        return False

    [p.unlink(missing_ok=True) for p in items if p.is_file()]

    return True

#-----------------------------------------------------------
def ensure_empty_escape(path:Path, label:str, external:bool, ) -> bool:
 
    items = list(path.glob("*"))
    if not items: return True
    #---------------
    def move_to_escape(p:Path):

        if path is DIR_INBOX: dir_esc = DIR_ESCAPE_TXT / p.name
        if path is DIR_DL:    dir_esc = DIR_ESCAPE_DL / p.name

        dst = dir_esc / p.name

        if dst.exists():
            stem, suf = dst.stem, dst.suffix
            i = 1
            while True:
                cand = dir_esc / f"{stem}_{i}{suf}"
                if not cand.exists():
                    dst = cand
                    break
                i += 1

        shutil.move(str(p), str(dst))
    # --------------
    if external:
        for p in items:
            try: move_to_escape(p)
            except Exception: pass
        return True

    print(f"[注意] {label} に {len(items)} 件ファイルが残っています")
    ans = ask_yes_no("退避フォルダへ移動して処理を開始しますか？ [Y/N]: ")

    if not ans:
        print("選択により実行中止しました")
        return False

    for p in items:
        try: move_to_escape(p)
        except Exception: pass

    return True

#-----------------------------------------------------------
def bring_from_archive(d:dt):

    ymd  = d.strftime("%y%m%d")
    name = f"K{ymd}.TXT"
    src  = DIR_ARC / name
    dest = DIR_INBOX / name

    try:
        shutil.move(str(src), str(dest))
        print(f"Archive -> INBOX: {name}")
        return dest
    except Exception as e:
        print(f"[警告] Archive -> INBOX 失敗: {name} ({e})")

        return None

#-----------------------------------------------------------
def try_download(d:dt):

    saved:List[Path] = []
    yyyymm           = d.strftime("%Y%m")
    yymmdd           = d.strftime("%y%m%d")
    url              = f"http://www1.mbrace.or.jp/od2/K/{yyyymm}/k{yymmdd}.lzh"
    out              = DIR_DL / f"K{d.strftime('%y%m%d')}.lzh"

    with requests.Session(impersonate="firefox") as session:
        session.headers.update(HEADERS)
        try:
            time.sleep(random.uniform(1.6,2.2))
            res = session.get(url, timeout=15)
            if res.status_code != 200 or not res.content: return None
    
            out.write_bytes(res.content)
            print(f"downloaded: {url} -> {out}")
            saved.append(out)
    
        except Exception as e:
            print(f"download失敗: {url} ({e})")

    return saved

#-----------------------------------------------------------
def stage_DL_to_INBOX(files:List[Path]):

    staged:List[Path] = []

    for f in files:
        lhf = None
        try:
            lhf = lhafile.Lhafile(str(f))
            for info in lhf.infolist():
                nm   = Path(info.filename).name
                data = lhf.read(info.filename)
                outp = DIR_INBOX / nm.upper()
                outp.write_bytes(data)

                print(f"extracted: {f.name} -> K_Files")
                staged.append(outp)

        except Exception as e:
            print(f"解凍失敗: {f} ({e})")

    return staged
#-----------------------------------------------------------
def archive_and_cleanup(txts:List[Path]):

    cnt_arc = 0

    for t in txts:
        dest = DIR_ARC / t.name
        try:
            if dest.exists(): dest.unlink()
            shutil.move(str(t), str(dest))

            print(f"archived: {t.name} ")
            cnt_arc += 1
        except Exception as e: print(f"archive失敗: {t} ({e})")

    print(f"-> archive {cnt_arc} file(s)")

    for d in (DIR_DL, DIR_INBOX):
        for p in d.glob("*"):
            try:
                if p.is_dir(): shutil.rmtree(p, ignore_errors=True)
                else: p.unlink(missing_ok=True)
            except Exception: pass

# --------------------- SQL Summary ------------------------
def current_counts(dates:Optional[Set[str]]=None) -> Dict[str,int]:

    q_dates = f"({",".join("?" for _ in dates)})" if dates else ""
    params  = tuple(sorted(dates))                if dates else ()

    races   = dal.fetch_one(f"""
                  SELECT COUNT(*)
                    FROM races
                   WHERE 1=1
                     AND date IN {q_dates}
                  """, params)[0]

    cancel  = dal.fetch_one(f"""
                  SELECT COUNT(*)
                    FROM races
                   WHERE status='cancelled'
                     AND date IN {q_dates}
                  """, params)[0]

    entries = dal.fetch_one(f"""
                  SELECT COUNT(*)
                    FROM race_entries
                   WHERE race_id IN ( SELECT race_id
                                        FROM races
                                       WHERE 1=1
                                         AND date IN {q_dates} )
                  """, params)[0]

    return {"races":races, "cancelled":cancel, "entries":entries}

#-----------------------------------------------------------
def decode_sjis(path:Path) -> str:

    b = path.read_bytes()
    for enc in ("cp932", "shift_jis"):
        try: return b.decode(enc)
        except Exception: pass

    return b.decode("cp932", errors="ignore")

#-----------------------------------------------------------
def import_K_txt(paths:Iterable[Path], overwrite:bool, payouts_only:bool=False) -> dict:

    RE_BLOCK = re.compile(r"(?P<vid>\d{2})KBGN(?P<body>.*?)(?:KEND)",re.S)
    total    = {"ins_r":0, "upd_r":0, "cnt_canc":0}
    cnt_f    = 0

    for path in paths:
        cnts  = {"ins_r":0, "upd_r":0, "cnt_canc":0}
        text  = decode_sjis(path)
        _date = date_from_filename(path.name)

        if payouts_only: print(f"[{_date}]")

        for m in RE_BLOCK.finditer(text):
            v_id  = int(m.group("vid"))
            body  =     m.group("body")

            if not payouts_only:
                meta  = upsert_Races(v_id, body, path.name, overwrite)
                cnt_r = meta[1]
                for key in cnts: cnts[key] += cnt_r[key]

                upsert_Race_entries(v_id, body, meta[0])

            p_cnt = upsert_Payouts_from_K(v_id, body, _date)
            if payouts_only: print(f"[{VENUES[int(v_id-1)]}]: {p_cnt} 件 UPSERT")

        for key in total:
            total[key] += cnts[key]

        cnt_f += 1
        print(f"import_K_txt  done: {path.name}")

    sums = (cnt_f, total)

    return sums

#============================== Main =================================
def main(argv=None):

    ap = argparse.ArgumentParser()
    ap.add_argument("--date_from",                         help="開始日(YYYY-MM-DD)")
    ap.add_argument("--date_to",                           help="終了日(YYYY-MM-DD)")
    ap.add_argument("--overwrite",    action="store_true", help="上書きﾓｰﾄﾞ")
    ap.add_argument("--no_grade",     action="store_true", help="Skip grade upsert")
    ap.add_argument("--external",     action="store_true", help="外部実行ﾓｰﾄﾞ")
    ap.add_argument("--DL_only",      action="store_true", help="DL→展開→archiveのみ")
    ap.add_argument("--payouts_only", action="store_true", help="payouts only mode")
    args = ap.parse_args(argv)

    run_ETL( args.date_from, args.date_to, args.overwrite, args.no_grade,
                            args.payouts_only, args.external, args.DL_only )

#=====================================================================
def run_ETL( date_from:int, date_to:int, overwrite:bool=False, no_grade:bool=False,
                   payouts_only:bool=False, external:bool=False, DL_only:bool=False ):

    range_mode = bool(date_from and date_to)

    if range_mode:
        if not ensure_empty_escape(DIR_DL,  "Downloads", external): return 1
        if not ensure_empty_escape(DIR_INBOX, "INBOX/K", external): return 1

    total_f                = 0
    staged_txts:List[Path] = []

    if range_mode:
        try:
            d0 = dt.strptime(date_from, "%Y-%m-%d")
            d1 = dt.strptime(date_to,   "%Y-%m-%d")
        except ValueError:
            print("日付は YYYY-MM-DD で指定してください"); return 2

        if d1 < d0:
            print("終了日以前に開始日は指定できません");   return 2

        downloaded:List[Path] = []

        for d in daterange(d0, d1):
            ymd      = d.strftime("%y%m%d")
            arc_path = DIR_ARC / f"K{ymd}.TXT"
            total_f += 1

            if arc_path.exists():
                if not DL_only:
                    moved = bring_from_archive(d)
                    if moved: staged_txts.append(moved)
                continue

            saved = try_download(d)
            if not saved:
                print(f"[警告] {d.strftime('%Y-%m-%d')}の Kﾌｧｲﾙ 取得失敗")
                continue

            downloaded.extend(saved)

        if downloaded: staged_txts.extend(stage_DL_to_INBOX(downloaded))
        else: print("DL対象なし(全日 archive 済み)\n")

    else: staged_txts = sorted(DIR_INBOX.glob("K*.TXT"))

    if DL_only:
        if staged_txts:
            archive_and_cleanup(staged_txts)
            print( f"[INFO] --DL_only-- : import/grade を実行せず "
                   f"DL/展開分を Archive へ移動しました。"           )
        else:
            print("[INFO] --DL_only-- : 処理対象がありません。")
        return 0

    target_dates:set[str] = set()

    for p in staged_txts:
        _date = date_from_filename(p.name)
        if _date: target_dates.add(_date)

    before = current_counts(target_dates if target_dates else None)

    if staged_txts:
        sums = import_K_txt(staged_txts, overwrite, payouts_only)
        print(f"imported {len(staged_txts)} file(s).\n")
    else:
        sums = (0, {"ins_r":0,"upd_r":0,"cnt_canc":0})
        print("INBOX に K*.TXT がありません")

    after = current_counts(target_dates if target_dates else None)

    if staged_txts:
        archive_and_cleanup(staged_txts)

    if not payouts_only:
        # ------------ サマリ --------------
        missing = total_f - sums[0]
        cnts    = sums[1]
        cancell = cnts["cnt_canc"]
        ins_r   = cnts["ins_r"]
        upd_r   = cnts["upd_r"]
        mode    = "Overwrite (Upsert)" if overwrite else "Normal (Insert)"

        print( f"\n== SUMMARY ==\n"
               f" Mode: {mode} \n"
               f" Inport K file   total = {total_f} ( miss  {missing}) \n"
               f"        [Races]:INSERT = {ins_r} (cancelled {cancell})/ UPDATE = {upd_r} \n"
               f" [Race_entries]:INSERT =             / UPDATE = "                            )
 
        # -------- グレード補填 ------------
        if range_mode:
            date_from = date_from
            date_to   = date_to
        else:
            dates = []
            for p in staged_txts:
                d = date_from_filename(p.name)
                if d: dates.append(d)

            date_from = min(dates) if dates else None
            date_to   = max(dates) if dates else None

        years = []
        if date_from and date_to:
            y_s    = int(date_from[:4])
            y_e    = int(  date_to[:4])
            years  = list(range(y_s, y_e +1))

        elif date_from: years = [int(date_from[:4])]
        elif date_to:   years = [int(  date_to[:4])]

        if not no_grade:
            for y in years:
                print( f"\n== upsert_Grade == \n"
                       f" year : {y} / range : ({date_from}～{date_to}) \n" )

                upsert_Grade(year=y, date_from=date_from, date_to=date_to, overwrite=overwrite)
        else:
            print("[INFO] -- no_grade -- :skipping grade upsert. \n")

    return 0

# ==============================================================================
if __name__ == "__main__":
    sys.exit(main())
