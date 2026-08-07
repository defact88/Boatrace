# -*- coding: utf-8 -*-
# C:\boatrace\Inport\upsert_Grade.py

from __future__ import annotations
import re, sqlite3, argparse, random, time
from datetime       import date, timedelta
from pathlib        import Path
from typing         import List, Tuple, Optional
from wcwidth        import wcswidth
from curl_cffi      import requests

DB     = r"C:\boatrace\boatrace.db"

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
CC_LCC = re.compile(r"(チャレンジカップ|レディースＣＣ)", re.I)
QC     = re.compile(r"(クイーンズクライマックス|賞金女王決定戦)", re.I)

VENUES = [  None, "桐生", "戸田",   "江戸川", "平和島", "多摩川", "浜名湖", "蒲郡", "常滑",
            "津", "三国", "びわこ", "住之江", "尼崎",   "鳴門",   "丸亀",   "児島", "宮島",
          "徳山", "下関", "若松",   "芦屋",   "福岡",   "唐津",   "大村"                    ]
VENUE_ID  = {name:i for i, name in enumerate(VENUES)}

GRADE_IDX = {"一般":0, "G3":1, "G2":2, "G1":3, "PG1":4, "SG":5}

ARCHIVE_TEXT_DIR = Path(r"C:\boatrace\archive\Grade\TEXT")
ARCHIVE_TEXT_DIR.mkdir(parents=True, exist_ok=True)

RE_TRIAL    = re.compile(r"トライアル|ＴＲ")
RE_PLACING  = re.compile(r"(?:順位\s*決定(?:\s*戦)?|[QＱ]\s*[CＣ]\s*順位\s*決定\s*戦|賞女\s*順位\s*決定\s*戦)")
RE_QC_FINAL = re.compile(r"(?:賞金\s*女王\s*決定(?:\s*戦)?|[QＱ]\s*[CＣ]\s*優勝\s*戦)")


# ===== DB更新ユーティリティ =====
def conn():
    c             = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row

    return c
#----------------------------------
def pad_display(text: str, width: int):
    disp_len = wcswidth(text)

    return text + " " * max(0, width - disp_len)

#----------------当日別グレード数をSummary_racesへ反映----------------
def update_summary_races_counts(c:sqlite3.Connection, year:int):

    rows = c.execute("""
               SELECT date,
                      SUM(CASE WHEN grade=5 THEN 1 ELSE 0 END) AS cnt_SG,
                      SUM(CASE WHEN grade=4 THEN 1 ELSE 0 END) AS cnt_PG1,
                      SUM(CASE WHEN grade=3 THEN 1 ELSE 0 END) AS cnt_G1,
                      SUM(CASE WHEN grade=2 THEN 1 ELSE 0 END) AS cnt_G2
                FROM races
               WHERE strftime('%Y', date)=?
            GROUP BY date
                     """,
                     (str(year),)).fetchall()

    for row in rows:
        d, sg, pg1, g1, g2 = row
        cur = c.execute("""
                  UPDATE Summary_races
                     SET cnt_SG= ?, cnt_PG1= ?, cnt_G1= ?, cnt_G2= ?
                   WHERE date= ?
                        """,
                        (sg or 0, pg1 or 0, g1 or 0, g2 or 0, d))

#------------------------ 公式ｽｹｼﾞｭｰﾙ取得・抽出 ----------------------
def fetch_html(year: int, hcd: str):

    base_url = "https://www.boatrace.jp/owpc/pc/race/gradesch"
    url      = f"{base_url}?year={year}&hcd={hcd}"

    with requests.Session(impersonate="firefox") as session:
        session.headers.update(HEADERS)
        try:
            time.sleep(random.uniform(1.6,3.2))
            res = session.get(url, timeout=15)
            res.raise_for_status()
        except Exception as e:
            print(f"[WARN] Page access failed: {e}")

        return res.text

#---------------------------------------------------------------------
def detect_grade(row_html:str, is_hcd01:bool):

    m = re.search(r'<td[^>]+class="([^"]+)"[^>]*>\s*</td>', row_html, re.IGNORECASE)
    if not m: return ""

    cls = m.group(1)
    if "is-SG" in cls:return "SG"
    if "is-G1" in cls:return "PG1" if is_hcd01 else "G1"
    if "is-G2" in cls:return "G2"
    if "is-G3" in cls:return "G3"

    return ""

#---------------------------------------------------------------------
def extract_row_items(row:str, year:int, is_hcd01:bool):

    m_date = re.search( r'<td[^>]*class="[^"]*\btd_date\b[^"]*"[^>]*>(.*?)</td>',
                                                     row, re.IGNORECASE|re.DOTALL )
    if not m_date: return ("",0,0,"","")

    date_html  = m_date.group(1)
    date_text  = re.sub(r"<[^>]+>", "", date_html).strip()
    m          = re.search(r"(\d{2})/(\d{2})-(\d{2})/(\d{2})", date_text)
    if not m: return ""

    due_date   = f"{year:04d}-{m.group(1)}-{m.group(2)}"
    final_date = f"{year:04d}-{m.group(3)}-{m.group(4)}"
    m_venue    = re.search(r'<img[^>]*alt="([^"]+)"', row, re.IGNORECASE)
    venue_name = m_venue.group(1).strip() if m_venue else ""
    venue_id   = VENUE_ID.get(venue_name, 0)
    raw_grade  = detect_grade(row, is_hcd01)
    grade_num  = GRADE_IDX.get(raw_grade, 0)
    m_title_td = re.search( r'<td[^>]*class="[^"]*\bis-p10-10\b[^"]*"[^>]*>(.*?)</td>',
                                                           row, re.IGNORECASE|re.DOTALL )
    if m_title_td:
        inner        = m_title_td.group(1)
        m_a          = re.search(r'<a[^>]*>([^<]+)</a>', inner, re.IGNORECASE|re.DOTALL)
        txt          = re.sub(r"<[^>]+>", "", inner).strip()
        series_title = (m_a.group(1) if m_a else txt).strip()
    else:
        series_title = ""

    return (due_date, final_date , venue_id, grade_num, raw_grade, series_title)

#---------------------------------------------------------------------
def parse_html_to_schedules(html:str, year:int, is_hcd01:bool ):

    i                                     = html.lower().find("<tr")
    sub                                   = html[i:] if i >= 0 else ""
    recs:List[Tuple[str,int,int,str,str]] = []

    for row in re.findall(r"<tr\b[\s\S]*?<\/tr>", sub, re.IGNORECASE):
        rec = extract_row_items(row, year, is_hcd01)
        if rec[0] and rec[1] and rec[4]: recs.append(rec)

    return recs

#---------------------------------------------------------------------
def build_schedule_lines(year:int):

    combined:List[Tuple[str,int,int,str,str]] = []

    for hcd in ("01", "02"):

        html = fetch_html(year, hcd)
        if not html: continue

        is_hcd01 = (hcd == "01")
        combined.extend(parse_html_to_schedules(html, year, is_hcd01))

    combined.sort(key=lambda x:(x[0], x[1], -x[2], x[4]))
    out = ARCHIVE_TEXT_DIR / f"G{year}.txt"

    with out.open("w", encoding="utf-8", newline="\n") as f:
        for due_date, final_date, venue_id, grade_num, raw_grade, series_title in combined:
            f.write( f"{due_date}\t{final_date}\t{int(venue_id)}\t"
                     f"{int(grade_num)}\t{raw_grade}\t{series_title}\n" )

    return combined

#---------------------------------------------------------------------
def load_schedule_lines(year:int):

    src = ARCHIVE_TEXT_DIR / f"G{year}.txt"
    if not src.exists(): return None

    lines:List[Tuple[str,int,int,str,str]] = []
    with src.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip("\r\n")
            if not ln: continue

            parts = ln.split("\t")
            if len(parts) < 6: continue

            due_date, final_date, vid, gnum, raw_grade, title = parts[:6]
            try:
                venue_id  = int(vid)
                grade_num = int(gnum)
            except ValueError: continue

            lines.append((due_date, final_date, venue_id, grade_num, raw_grade, title))

    lines.sort(key=lambda x:(x[0], x[1], -x[2], x[4]))

    return lines

# ------------------- ﾚﾃﾞｨｰｽCC/ﾁｬﾚﾝｼﾞｶｯﾌﾟ個別UPSERT ------------------
def upsert_cc_lcc(c:sqlite3.Connection, schedule:List, overwrite:bool):

    processed_cnt, upd_g2, upd_sg = 0, 0, 0

    targets = {(dd, fd, vid) for (dd, fd, vid, _, _, title) in schedule if CC_LCC.search(title)}
    if not targets:
        print("[CC / LCC] 対象開催なし") ;return 0, 0

    for due_date, final_date, venue_id in sorted(targets):
        exe_dates = get_exe_dates(c, venue_id, due_date, 6)
        if not exe_dates:
            print(f"[CC / LCC] 対象外") ;continue

        processed_cnt  += 1
        qmarks = ",".join(["?"] * len(exe_dates))
        rows   = c.execute(f"""
                     SELECT race_id, series_title
                       FROM races
                      WHERE venue_id = ?
                        AND date     IN ({qmarks})
                        AND status   = 'held'
                     """,
                     (venue_id, *exe_dates)).fetchall()

        for race_id, sname in rows:
            sexes = [r[0] for r in c.execute("""
                                       SELECT p.sex
                                         FROM Race_entries e
                                         JOIN players p
                                           ON p.player_id = e.player_id
                                        WHERE e.race_id = ?
                                       """,
                                       (race_id,)).fetchall()           ]

            if all(s == "女" for s in sexes):
                sql = "UPDATE races SET grade=2 WHERE race_id=?"
                if not overwrite: sql += " AND grade IS NULL"
                cur     = c.execute(sql, (race_id,))
                upd_g2 += cur.rowcount
            else:
                sql = "UPDATE races SET grade=5 WHERE race_id=?"
                if not overwrite: sql += " AND grade IS NULL"
                cur     = c.execute(sql, (race_id,))
                upd_sg += cur.rowcount

            c.commit()

    if processed_cnt:
        summs = f"( {exe_dates[0]:>}～{exe_dates[-1]} )\t{len(exe_dates)}日間：総更新数"

        print(f"SG\t{pad_display('チャレンジカップ',30)}\t{VENUES[venue_id]}\t{summs}{upd_sg}")
        print(f"G2\t{pad_display('レディースCC',    30)}\t{VENUES[venue_id]}\t{summs}{upd_g2}")

    return upd_g2, upd_sg, processed_cnt

# ----------------- クイーンズCLIMAX(PG1)個別 UPSERT -----------------
def upsert_climax(c:sqlite3.Connection, schedule:List, overwrite:bool):
    # --------------
    def _get_title_held(date_:str, venue_id_:int, race_no_:int):

        r = c.execute("""
            SELECT race_title
              FROM races
             WHERE date=? AND venue_id=? AND race_no=? AND status='held'
             LIMIT 1
            """,
            (date_, venue_id_, race_no_)).fetchone()

        return (r[0] if r else "") or ""
     # -------------
    targets = [(dd, fd, vid, title) for (dd, fd, vid, _, _, title) in schedule if QC.search(title)]
    if not targets:
        print("[Q_CLIMAX] 対象開催なし") ;return 0, 0

    total_updated, processed_cnt = 0, 0

    for (due_date, final_date, venue_id, title) in targets:

        exe_dates = get_exe_dates(c, venue_id, due_date, 6)
        if not exe_dates:
            print(f"[Q_CLIMAX] 対象外") ;continue

        base_trial_start_day              = 3
        base_final_day                    = 6
        max_shift                         = 2
        target_pairs:List[Tuple[str,int]] = []
        trials_found                      = 0
        last_trial_day                    = None
        search_last_day_for_trials        = base_final_day + max_shift
        day                               = base_trial_start_day

        while day <= search_last_day_for_trials and trials_found < 6:
            idx = day - 1
            if 0 <= idx < len(exe_dates):
                d   = exe_dates[idx]
                t11 = _get_title_held(d, venue_id, 11)
                t12 = _get_title_held(d, venue_id, 12)
                if RE_TRIAL.search(t11) and RE_TRIAL.search(t12):
                    target_pairs.append((d, 11))
                    target_pairs.append((d, 12))
                    trials_found  += 2
                    last_trial_day = day
            day += 1

        if trials_found < 6:
            print(f"[Q_CLIMAX] 警告  トライアル通常数: 6  実数: {trials_found}")
            continue

        finals_found               = 0
        total_days                 = 0
        search_start_for_finals    = (last_trial_day or base_final_day - 1) + 1
        search_last_day_for_finals = base_final_day + max_shift
        day                        = search_start_for_finals

        while day <= search_last_day_for_finals and finals_found < 2:
            idx         = day - 1
            total_days += 1
            if 0 <= idx < len(exe_dates):
                d   = exe_dates[idx]
                t10 = _get_title_held(d, venue_id, 10)
                t12 = _get_title_held(d, venue_id, 12)
                if (RE_PLACING.search(t10) is not None) and (RE_QC_FINAL.search(t12) is not None):
                    target_pairs.append((d, 10))
                    target_pairs.append((d, 12))
                    finals_found = 2
                    break
            day += 1

        if trials_found == 6 and finals_found == 2:
            processed_cnt  += 1
            updated = 0
            for dt_str, rno in target_pairs:
                where_null = "AND grade IS NULL" if not overwrite else ""
                cur = c.execute(f"""
                          UPDATE races
                             SET grade = 4
                           WHERE venue_id = ?
                             AND date     = ?
                             AND race_no  = ?
                             AND status   = 'held'
                     {where_null}
                          """,(venue_id, dt_str, rno))

                updated += cur.rowcount

            c.commit()

            total_updated += updated

            print(f"PG1\t{pad_display(title, 30)}\t{VENUES[venue_id]}\t"
                  f"( {due_date}～{final_date} )\t{day}日間：総更新数{updated}")

        else:
            print(f"[Q_CLIMAX] 警告: 8レース確定できず (trial={trials_found}, "
                  f"finals={finals_found} {title} ({due_date}～{final_date})")

    return total_updated, processed_cnt

#---------------------------------------------------------------------
def get_exe_dates(c:sqlite3.Connection, venue_id:int, due_date:str, base_days):

    _date         = date.fromisoformat(due_date)
    dates         = []
    processedDays = 0

    for d in range(base_days +2):
        row = c.execute("""
                         SELECT status,
                                series_title
                           FROM Races
                          WHERE date     = ?
                            AND venue_id = ?
                            AND race_no  = 6
                        """,
                         (_date.isoformat(), venue_id)).fetchone()

        if row:
            dates.append(_date.isoformat())
            if row["status"] == "held":
                processedDays += 1
                if processedDays == base_days: break

        _date += timedelta(days=1)

    return dates

#------------- 指定日・指定場の全ﾚｰｽに指定ｸﾞﾚｰﾄﾞを一括投入------------
def upsert_event_grade(c:sqlite3.Connection, venue_id:int, dates:List, g_num:int, overwrite:bool):

    if not dates: return 0

    qmarks     = ",".join(["?"] * len(dates))
    where_null = "AND grade IS NULL" if not overwrite else ""
    sql = f"""
              UPDATE races
                 SET grade    = ?
               WHERE venue_id = ?
                 AND date IN ({qmarks})
         {where_null}
              """
 
    args = [g_num, venue_id, *dates]
    cur  = c.execute(sql, args)

    return cur.rowcount

#---------------------------------------------------------------------
def cnt_grades_inDB(c:sqlite3.Connection, year:int):

    rows = c.execute("""
               SELECT grade,
                COUNT (*) 
                 FROM races
                WHERE strftime('%Y', date) = ?
             GROUP BY grade
             ORDER BY grade
               """,
               (str(year),)).fetchall()

    grades = {i: 0 for i in range(6)}
    for g, cnt in rows:
        if g is not None and 0 <= g < 6:grades[g] += cnt

    return grades 

#============================ MAIN ===================================
def upsert_Grade(year:int, date_from:str=None, date_to:str=None, overwrite:bool=False ):

    lines  = load_schedule_lines(year)
    z_from = f"{year}-01-01"
    z_to   = f"{year}-12-31"
    if date_from: z_from = max(z_from, date_from)
    if date_to:   z_to   = min(z_to,   date_to)

    if overwrite:
        with conn() as c:
            pre = c.execute("""
                      UPDATE races
                         SET grade = NULL
                       WHERE date BETWEEN ? AND ?
                      """,
                      (z_from, z_to)).rowcount

            c.commit()

        print(f"[INFO] overwrite: 事前クリア {pre} 件（{z_from}～{z_to}）")

    if lines: print(f"[INFO] 既存アーカイブから読込")
    else: lines = build_schedule_lines(year); print(f"[INFO] 取得して保存")
    print(f"[INFO] 読込 {len(lines)} 行")

    bad_days, cc_esc, qc_esc  = 0, 0, 0
    upd_qc, exe_qc, upd_g2, upd_sg, exe_cc = 0, 0, 0, 0, 0
    cnt_upserted_gr           = {i:0 for i in range(6)}

    with conn() as c:
        grades_bfr = cnt_grades_inDB(c, year)
        for ln in lines:
            due_date, final_date, v_id, g_num, grade, title = ln
            if title == "グランプリシリーズ":     continue
            if QC.search(title):     qc_esc += 1 ;continue
            if CC_LCC.search(title): cc_esc += 1 ;continue

            base_days = 4 if "BBCトーナメント" in title else 6

            exe_date = get_exe_dates(c, v_id, due_date, base_days)
            if not exe_date: continue

            summs1 = f"{grade}\t{pad_display(title, 30)}\t{VENUES[v_id]}"
            summs2 = f"( {exe_date[0]:>}～{exe_date[-1]} )"

            if len(exe_date) > base_days +2:
                print( f"{summs1}\t{summs2} ★★ 警告:期間超過 days = {len(exe_date)} ★★")
                bad_days += 1

            n = upsert_event_grade(c, v_id, exe_date, g_num, overwrite=overwrite)
            print(f"{summs1}\t{summs2}\t{len(exe_date)}日間：総更新数{n}")

            if g_num in cnt_upserted_gr: cnt_upserted_gr[g_num] += n

        if cc_esc: upd_g2, upd_sg, exe_cc = upsert_cc_lcc(c, lines, overwrite=overwrite)
        if qc_esc: upd_qc, exe_qc         = upsert_climax(c, lines, overwrite=overwrite)
        cnt_upserted_gr[4] += upd_qc
        cnt_upserted_gr[2] += upd_g2
        cnt_upserted_gr[5] += upd_sg

        cur = c.execute("""
                  UPDATE races
                     SET grade=0
                   WHERE grade IS NULL 
                     AND date BETWEEN ? AND ?
                  """,
                  (z_from, z_to))

        cnt_upserted_gr[0] += cur.rowcount
        cur = c.execute("""
                  SELECT
                   COUNT(*) 
                    FROM races
                   WHERE date BETWEEN ? AND ?
                  """,
                  (z_from, z_to))

        all_targets = cur.fetchone()[0]

        c.commit()

        grades_aft     = cnt_grades_inDB(c, year)
        total_gr_bfr   = sum(grades_bfr.values())
        total_gr_aft   = sum(grades_aft.values())
        upserted_total = sum(cnt_upserted_gr.values())
        grd_idx        = {0:'－般', 1:' G3 ', 2:' G2 ', 3:' G1 ', 4:' PG1', 5:' SG '}

        print("\n=== サマリ ===")
        print(f"{year}年  対象総数: {all_targets}")
        print(f"全ｸﾞﾚｰﾄﾞ既存総数: {total_gr_aft}")
        print(f"    開催日数異常: {bad_days}")
        if exe_cc:
            print("[ CC/LCC 別処理 ]")
            print(f"対象開催:{exe_qc}  G2 更新:{upd_g2}  SG 更新:{upd_sg}")
        if exe_qc:
            print("[Q_CLIMAX 別処理]")
            print(f"対象開催:{exe_qc}  PG1 更新:{upd_qc}")
        print("\n===DB内総数 実行前 >> 実行後／今回更新数===")

        for i in range(6):
            before   = grades_bfr.get(i, 0)
            after    = grades_aft.get(i, 0)
            upserted = cnt_upserted_gr.get(i, 0)
            grd      = grd_idx.get(i, 0)
            print(f"  {grd}: DB = {before:5} >> {after:5}  更新数 = {upserted}")

        print(f"Total : DB = {total_gr_bfr:5} >> {total_gr_aft:5}  更新数 = {upserted_total}")

        update_summary_races_counts(c, year)

#---------------------------------------------------------------------
if __name__ == "__main__":

    ap = argparse.ArgumentParser(description="公式年間ｽｹｼﾞｭｰﾙでraces.gradeを一括補填")
    ap.add_argument("--year", type=int, required=True,  help="対象年(YYYY)")
    ap.add_argument("--overwrite", action="store_true", help="対象年を上書き")
    args = ap.parse_args()

    upsert_Grade(args.year, None, None, args.overwrite)
