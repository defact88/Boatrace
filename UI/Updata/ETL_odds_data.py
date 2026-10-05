# -*- coding: utf-8 -*-
# C:\boatrace\UI\Subprocess\ETL_odds_data.py

import argparse, time, os, sys
import Dal as dal
from datetime import datetime as dt, date, timedelta

from scraper_odds import fetch_all_odds
from ev_scanner   import insert_odds_snapshot

VENUES = [ "桐  生", "戸  田", "江戸川", "平和島", "多摩川", "浜名湖", "蒲  郡", "常  滑",
           "  津  ", "三  国", "びわこ", "住之江", "尼  崎", "鳴  門", "丸  亀", "児  島",
           "宮  島", "徳  山", "下  関", "若  松", "芦  屋", "福  岡", "唐  津", "大  村"  ]

# ===========  共通ヘルパー  ===========
def today_iso() -> str:

    JST = timezone(timedelta(hours=9))
    return dt.now(JST).date().strftime("%Y-%m-%d")

#-------------------
def yesterday(x) -> date:

    if isinstance(x, date): return x -timedelta(days=1)
    if isinstance(x,  str): return to_date(x) -timedelta(days=1)

# ------------------
def to_str(x) -> str:

    if isinstance(x,  str): return x
    if isinstance(x, date): return x.strftime("%Y-%m-%d")

    raise ValueError("str conv error")

# ------------------
def to_date(x) -> date:

    if isinstance(x, date): return x
    if isinstance(x,  str): return date.fromisoformat(x)

    raise ValueError("date conv error")

#=====================================================================
def get_target_races(d_iso:str, venue_id:int|None, race_no:int|None) -> list:

    params = [v for v in (d_iso, venue_id, race_no) if v != None]

    sql = """
        SELECT venue_id, race_no
          FROM Races
         WHERE date    = ?
           AND status != 'cancelled'
        """

    sql += " AND venue_id = ?" if venue_id else ""
    sql += " AND race_no  = ?" if race_no  else ""
    sql += " ORDER BY venue_id, race_no"

    return dal.fetch_all(sql, tuple(params))

#-------------------------------------------------
def check_odds_exists(d_iso:str, venue_id:int, race_no:int) -> bool:

    cnt = 0
    for bt in ("3T", "3F", "2T", "2F", "KK", "TT", "FF"):
        
        row = dal.fetch_one(f"""
            SELECT COUNT(*)
              FROM Odds_{bt}
             WHERE date     =?
               AND venue_id =?
               AND race_no  =?
        """,
        (d_iso, venue_id, race_no) )

        cnt += row[0] if row else 0

    if cnt == 7:
        return True

    return False
#-------------------------------------------------
def delete_existing_odds(d_iso:str, venue_id:int, race_no:int):

    for bt in ("3T", "3F", "2T", "2F", "KK", "TT", "FF"):

        dal.execute(f"""
            DELETE
              FROM Odds_{bt}
             WHERE date     =?
               AND venue_id =?
               AND race_no  =?
        """,
        (d_iso, venue_id, race_no))

#=====================================================================
def main(argv=None):

    p = argparse.ArgumentParser()
    p.add_argument("--date",       type=date.fromisoformat, help="対象日(yyyy)")
    p.add_argument("--date_from",  type=date.fromisoformat, help="開始日(YYYY-MM-DD)")
    p.add_argument("--date_to",    type=date.fromisoformat, help="終了日(YYYY-MM-DD)")
    p.add_argument("--days",       type=int,                help="直近n日間不足日補填")
    p.add_argument("--venue",      type=int,                help="場指定")
    p.add_argument("--race",       type=int,                help="レース指定")
    p.add_argument("--overwrite", action="store_true", help="既存データを上書き")
    args = p.parse_args(argv)

    if args.date and (args.date_from or args.date_to):
        print("date / (date_from , date_to) 両方の指定はできません")
        raise SystemExit(2)
    if (args.date_from and not args.date_to) or (args.date_to and not args.date_from):
        print("(date_from , date_to) を併せて指定してください")
        raise SystemExit(2)

    if args.days:
        date_from = dt.today() -timedelta(days=args.days)
        date_to   = dt.today()
    elif args.date:
        date_from = args.date
        date_to   = args.date
    elif args.date_from and args.date_to:
        date_from = args.date_from
        date_to   = args.date_to
    else:
        date_from = dt.today()
        date_to   = dt.today()

    _date = date_from
    while _date <= date_to:

        d_iso = to_str(_date)
        d_str = _date.strftime("%Y%m%d")

        print(f"\n[{d_iso}] 対象レースの確認中...")

        target_races = get_target_races(d_iso, args.venue, args.race)
        if not target_races:
            print(f"  -> 対象レースが見つかりません。")
            _date += timedelta(days=1)
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

                res, _ = insert_odds_snapshot(data, _date, venue_id, race_no, hits=[])
                if res == 0:
                    print(f"    -> 取得成功 (7 bet_type)")
                elif res == 1:
                    print(f"    -> 取得完了 (7 bet_ryoe未満)")
                else:
                    print(f"    -> 取得失敗 (保存対象データなし)")

                time.sleep(1.0)

            except Exception as e:
                print(f"    [Error] 処理中に例外発生: {e}")

        _date += timedelta(days=1)

    print("\n全期間の処理が完了しました。")

#=====================================================================
if __name__ == "__main__":
    sys.exit(main())