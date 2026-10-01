# -*- coding: utf-8 -*-
# C:\boatrace\UI\Updata\ETL_get_payouts_data.py

import argparse, time, os, sys
import Dal as dal
from datetime    import datetime as dt, timedelta

from get_payouts import upsert_payouts
import ETL_K_results

VENUES = [ "桐  生", "戸  田", "江戸川", "平和島", "多摩川", "浜名湖", "蒲  郡", "常  滑",
           "  津  ", "三  国", "びわこ", "住之江", "尼  崎", "鳴  門", "丸  亀", "児  島",
           "宮  島", "徳  山", "下  関", "若  松", "芦  屋", "福  岡", "唐  津", "大  村"  ]

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
def exists_payouts(d_iso:str, venue_id:int, race_no:int) -> bool:

    rows = dal.fetch_all("""
        SELECT COUNT(*) AS cnt
          FROM Payouts
         WHERE date     =?
           AND venue_id =?
           AND race_no  =?
      GROUP BY date
    """,
    (d_iso, venue_id, race_no))

    for r in rows:
        if r["cnt"] >= 1:
            return True

    return False
#-------------------------------------------------
def delete_existing_payouts(d_iso:str, venue_id:int, race_no:int):

    dal.execute("""
        DELETE
          FROM Payouts
         WHERE date     =?
           AND venue_id =?
           AND race_no  =?
    """,
    (d_iso, venue_id, race_no))

#=====================================================================
def main(argv=None):

    p = argparse.ArgumentParser()
    p.add_argument("--date",      required=False, help="指定日 (YYYY-MM-DD)")
    p.add_argument("--date_from", required=True,  help="開始日 (YYYY-MM-DD)")
    p.add_argument("--date_to",   required=True,  help="終了日 (YYYY-MM-DD)")
    p.add_argument("--venue",     required=False, help="場(venue_id)指定")
    p.add_argument("--race",      required=False, help="レース(race_no)指定")
    p.add_argument("--from_html", action="store_true", help="公式ページHTMLから取得")
    p.add_argument("--overwrite", action="store_true", help="既存データを上書き")
    args = p.parse_args(argv)

    if args.date and (args.date_from or args.date_to):
        print("date / (date_from , date_to) 両方の指定はできません")
        raise SystemExit()
    if (args.date_from and not args.date_to) or (args.date_to and not args.date_from):
        print("(date_from , date_to) を併せて指定してください")
        raise SystemExit()

    if args.date:
        d_from, d_to = args.date, args.date
    elif args.date_from and args.date_to:
        d_from, d_to = args.date_from, args.date_to
    else:
        _today       = dt.today().strftime("%Y-%m-%d")
        d_from, d_to = _today, _today

    if not args.from_html:
        ETL_K_results.run_ETL(d_from, d_to, overwrite=args.overwrite, payouts_only=True)
        return

    current_date = dt.strptime(d_from, "%Y-%m-%d").date()

    while current_date <= dt.strptime(d_to, "%Y-%m-%d").date():

        d_iso = current_date.strftime("%Y-%m-%d")

        print(f"\n[{d_iso}] 対象レースの確認中...")
        target_races = get_target_races(d_iso, args.venue, args.race)

        if not target_races:
            print(f"  -> 対象レースが見つかりません。")
            current_date += timedelta(days=1)
            continue

        for row in target_races:
            venue_id = row["venue_id"]
            race_no  = row["race_no"]

            exists = exists_payouts(d_iso, venue_id, race_no)

            if exists:
                if not args.overwrite:
                    print( f"  [{d_iso} {VENUES[int(venue_id)-1]} {race_no:02d}R] "
                           f"既存データあり スキップ。"                             )
                    continue
                else:
                    print( f"  [{d_iso} {VENUES[int(venue_id)-1]} {race_no:02d}R] "
                           f"既存データ削除 上書き更新します。"                     )

                    delete_existing_payouts(d_iso, venue_id, race_no)

            else:
                print( f"  [{d_iso} {VENUES[int(venue_id)-1]} {race_no:02d}R] "
                       f"既存データ無し 取得開始..."                             )

            try:
                data = upsert_payouts(d_iso, venue_id, race_no)

                if data < 1:
                    print(f"    [WARN] データ取得失敗")
                else:
                    print(f"    -> 取得完了") 

                time.sleep(1.0)

            except Exception as e:
                print(f"    [Error] 処理中に例外発生: {e}")

        current_date += timedelta(days=1)

    print("\n全期間の処理が完了しました。")

#=====================================================================
if __name__ == "__main__":
    sys.exit(main())