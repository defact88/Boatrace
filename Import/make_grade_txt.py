# -*- coding: utf-8 -*-
# C:\boatrace\Inport\make_grade_txt.py

import re, argparse, gzip, io, time, random
from curl_cffi import requests
from pathlib   import Path

VENUES = ["桐生","戸田","江戸川","平和島","多摩川","浜名湖","蒲郡","常滑","津",
          "三国","びわこ","住之江","尼崎","鳴門","丸亀","児島","宮島","徳山",
          "下関","若松","芦屋","福岡","唐津","大村"]
GRADE_IDX = {"一般": 0, "G3": 1, "G2": 2, "G1": 3, "PG1": 4, "SG": 5}

PG1_KEYWORDS = ["マスターズチャンピオン", "レディースチャンピオン", "ヤングダービー", "ボートレースバトルチャンピオン", "レディースオールスター"]

OUTPUT_DIR = Path(r"C:\boatrace\Archive\Grade\TEXT")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
#---------------------------------------------------------------------
def fetch_html(url):

    with requests.Session(impersonate="firefox") as session:
        session.headers.update(HEADERS)
        try:
            time.sleep(random.uniform(1.6,3.2))
            res = session.get(url, timeout=15)
            res.raise_for_status()
        except Exception as e:
            print(f"[ERR] Page access failed: {e}")
            return None
    return res.text
#---------------------------------------------------------------------
def clean_series_title(title):

    title = re.sub(r'<[^>]+>', '', title)
    title = re.sub(r'^[GＧ][1-3１-３]\s*', '', title)
    title = re.sub(r'^[SＳ][GＧ]\s*', '', title)
    title = re.sub(r'第\d+回', '', title)
    title = re.sub(r'開設\d+周年記念(競走)?', '', title)

    return title.strip()
#---------------------------------------------------------------------
def get_start_date_from_detail(detail_url):

    html = fetch_html(f"https://boatrace-db.net{detail_url}")
    if not html: return None

    m_txt = re.search(r'初日<br>(\d{4})/(\d{1,2})/(\d{1,2})', html)
    if m_txt:
        return f"{int(m_txt.group(1)):04d}-{int(m_txt.group(2)):02d}-{int(m_txt.group(3)):02d}"

    return None
#---------------------------------------------------------------------
def process_year(year):

    base_url = f"https://boatrace-db.net/result/gwinner/year/{year}/"
    print(f"Target Year: {year}")
    
    html = fetch_html(base_url)
    if not html: return

    rows = re.findall(r'<tr\b[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
    results = []
    
    for row in rows:
        cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
        if len(cols) < 5: continue

        link_match = re.search(r'href="(/race/detail/date/(\d{8})/pid/(\d{2})/[^"]+)"', row)
        if not link_match: continue

        venue_name = re.sub(r'<[^>]+>', '', cols[2]).strip()
        raw_grade = re.sub(r'<[^>]+>', '', cols[3]).strip()
        raw_title = re.sub(r'<[^>]+>', '', cols[4]).strip()
        
        detail_url = link_match.group(1)
        end_date_str = link_match.group(2)
        end_date = f"{end_date_str[:4]}-{end_date_str[4:6]}-{end_date_str[6:8]}"
        v_id = int(link_match.group(3))

        start_date = get_start_date_from_detail(detail_url)
        
        if not start_date:
            print(f"  [!] {venue_name}: 開始日抽出失敗（終了日を代用）")
            start_date = end_date
        else:
            print(f"  -> {venue_name}: {start_date} ～ {end_date}")

        series_title = clean_series_title(raw_title)
        grade_name = raw_grade
        if any(kw in series_title for kw in PG1_KEYWORDS):
            grade_name = "PG1"

        grade_no = GRADE_IDX.get(grade_name, 0)
        
        line = f"{start_date}\t{end_date}\t{v_id}\t{grade_no}\t{grade_name}\t{series_title}"
        results.append(line)
        time.sleep(1.0)

    if results:
        results.sort()
        output_file = OUTPUT_DIR / f"G{year}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(results) + "\n")
        print(f"\n完了: {output_file}")
#---------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", required=True)
    args = parser.parse_args()
    process_year(args.year)
#---------------------------------------------------------------------
if __name__ == "__main__":
    main()