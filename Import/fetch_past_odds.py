# -*- coding: utf-8 -*-
# fetch_past_odds.py

import argparse, time, os
import Dal as dal
from datetime import datetime, timedelta

from scraper_odds import fetch_all_odds
from ev_scanner   import insert_odds_snapshot

VENUES = [ "桐  生", "戸  田", "江戸川", "平和島", "多摩川", "浜名湖", "蒲  郡", "常  滑",
           "  津  ", "三  国", "びわこ", "住之江", "尼  崎", "鳴  門", "丸  亀", "児  島",
           "宮  島", "徳  山", "下  関", "若  松", "芦  屋", "福  岡", "唐  津", "大  村"  ]

#=====================================================================
def get_target_races(d_iso:str) -> list:

    rows = dal.fetch_all("""
        SELECT venue_id, race_no
          FROM Races
         WHERE date    = ? 
           AND status != 'cancelled'
      ORDER BY venue_id, race_no
    """,
    (d_iso,))

    return rows

#-------------------------------------------------
def check_odds_exists(d_iso:str, venue_id:int, race_no:int) -> bool:

    rows = dal.fetch_all("""
        SELECT captured_at,
               COUNT(*) AS cnt
          FROM Odds
         WHERE date     =?
           AND venue_id =?
           AND race_no  =?
      GROUP BY captured_at
    """,
    (d_iso, venue_id, race_no))

    for r in rows:
        if r["cnt"] >= 212:
            return True

    return False
#-------------------------------------------------
def delete_existing_odds(d_iso:str, venue_id:int, race_no:int):

    dal.execute("""
        DELETE
          FROM Odds
         WHERE date     =?
           AND venue_id =?
           AND race_no  =?
    """,
    (d_iso, venue_id, race_no))

#=====================================================================
def main():

    parser = argparse.ArgumentParser(description="オッズ不足データを期間指定で一括取得")
    parser.add_argument("--date_from", required=True, help="開始日 (YYYY-MM-DD)")
    parser.add_argument("--date_to",   required=True, help="終了日 (YYYY-MM-DD)")
    parser.add_argument("--overwrite", action="store_true", help="既存データを上書き(UPDATE相当)")
    
    args = parser.parse_args()
    
    try:
        date_from = datetime.strptime(args.date_from, "%Y-%m-%d").date()
        date_to   = datetime.strptime(args.date_to,   "%Y-%m-%d").date()

    except ValueError:
        print("[Error] 日付フォーマットは YYYY-MM-DD で指定してください。")
        return

    if date_from > date_to:
        print("[Error] --date_from は --date_to と同じか、以前の日付を指定してください。")
        return

    current_date = date_from

    while current_date <= date_to:

        d_iso = current_date.strftime("%Y-%m-%d")
        d_str = current_date.strftime("%Y%m%d")
        print(f"\n[{d_iso}] 対象レースの確認中...")

        target_races = get_target_races(d_iso)
        if not target_races:
            print(f"  -> 対象レースが見つかりません。")
            current_date += timedelta(days=1)
            continue
            
        for row in target_races:
            venue_id = row["venue_id"]
            race_no  = row["race_no"]

            exists = check_odds_exists(d_iso, venue_id, race_no)

            if exists:
                if not args.overwrite:
                    print( f"  [{d_iso} {VENUES[int(venue_id)-1]} {race_no:02d}R] "
                           f"既存データあり スキップ。"                             )
                    continue
                else:
                    print( f"  [{d_iso} {VENUES[int(venue_id)-1]} {race_no:02d}R] "
                           f"既存データ削除 上書き更新します。"                     )
                    delete_existing_odds(d_iso, venue_id, race_no)
            else:
                print( f"  [{d_iso} {VENUES[int(venue_id)-1]} {race_no:02d}R] "
                       f"既存データ無し 取得開始..."                             )

            try:
                data = fetch_all_odds(d_str, venue_id, race_no)
                if data.get("error"):
                    print(f"    [WARN] ページ取得エラー: {data['error']}")

                res = insert_odds_snapshot(data, current_date, venue_id, race_no, hits=[])
                if res == 1:
                    print(f"    -> 取得成功 (212件)")
                elif res == 2:
                    print(f"    -> 取得完了 (インサート件数 212件未満)")
                else:
                    print(f"    -> 取得失敗 (保存対象データなし)")

                time.sleep(1.0)

            except Exception as e:
                print(f"    [Error] 処理中に例外発生: {e}")

        current_date += timedelta(days=1)

    print("\n全期間の処理が完了しました。")

#=====================================================================
if __name__ == "__main__":
    main()