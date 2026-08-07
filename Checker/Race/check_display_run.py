# -*- coding: utf-8 -*-
import sqlite3
import argparse
from pathlib import Path

# --- 設定 ---
BASE_DIR = Path(r"C:\boatrace")
DB_PATH  = BASE_DIR / "boatrace.db"

def check_display_data(date_from, date_to):
    """
    Races.status='cancelled' を考慮して不備データを抽出する
    """
    if not DB_PATH.exists():
        print(f"[ERR] データベースが見つかりません: {DB_PATH}")
        return

    # SQLロジックの修正:
    # 1. Race_programs から該当日時のレース一覧を取得
    # 2. Races テーブルと結合して status を取得
    # 3. Display_run を LEFT JOIN してレコード数と内容をチェック
    # 4. HAVING句で「中止ではないのに6艇未満」または「出走艇に空データあり」を抽出
    sql = """
    SELECT 
        p.date, 
        p.venue_id, 
        p.race_no,
        r.status,
        COUNT(d.frame_no) as record_count,
        SUM(CASE WHEN d.is_absent = 0 AND (d.exhibition IS NULL OR d.slit_ADJ IS NULL OR d.tilt IS NULL) THEN 1 ELSE 0 END) as missing_val_count
    FROM (
        SELECT DISTINCT date, venue_id, race_no 
        FROM Race_programs 
        WHERE date BETWEEN ? AND ?
    ) p
    INNER JOIN Races r
        ON  p.date     = r.date
        AND p.venue_id = r.venue_id
        AND p.race_no  = r.race_no
    LEFT JOIN Display_run d 
        ON  p.date     = d.date 
        AND p.venue_id = d.venue_id 
        AND p.race_no  = d.race_no
    GROUP BY p.date, p.venue_id, p.race_no, r.status
    HAVING 
        (r.status != 'cancelled' AND record_count < 6)
        OR 
        (missing_val_count > 0)
    ORDER BY p.date, p.venue_id, p.race_no;
    """

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, (date_from, date_to))
            rows = cursor.fetchall()

        if not rows:
            print(f"指定期間 ({date_from} ～ {date_to}) に不備のあるデータは見つかりませんでした。")
            return

        print(f"{'date':<12} | {'v_id':<4} | {'r_no':<4} | {'status':<10} | {'issue'}")
        print("-" * 65)
        
        for r in rows:
            issue = ""
            if r['record_count'] < 6:
                issue = f"Record missing ({r['record_count']}/6)"
            else:
                issue = f"Value missing ({r['missing_val_count']} boats)"
                
            print(f"{r['date']:<12} | {r['venue_id']:<4} | {r['race_no']:<4} | {r['status']:<10} | {issue}")

        print("-" * 65)
        print(f"合計: {len(rows)} 件の不備が見つかりました。")

    except sqlite3.Error as e:
        print(f"[SQL ERR] {e}")
    except Exception as e:
        print(f"[ERR] {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Display_run データの不備検査ツール（中止考慮版）")
    parser.add_argument("--date_from", required=True, help="開始日 (YYYY-MM-DD)")
    parser.add_argument("--date_to",   required=True, help="終了日 (YYYY-MM-DD)")

    args = parser.parse_args()
    check_display_data(args.date_from, args.date_to)