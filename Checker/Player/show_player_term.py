# show_player_term.py 

import argparse, sqlite3

DB_PATH = r"C:\boatrace\boatrace.db"
#----------------------------------------------------------
def fmt_avg_st(v):
    return f"{v/100:.2f}" if isinstance(v, int) else "-"

def fmt_rate_x100(v):
    return f"{v/100:.2f}" if isinstance(v, int) else "-"

def fmt_percent_x10(v):
    return f"{v/10:.1f}%" if isinstance(v, int) else "-"
#-----------------------------------------------------------
def fmt_birthday_ymd(yyyymmdd):

    if not isinstance(yyyymmdd, int):
        return "-"
    s = f"{yyyymmdd:08d}"
    yyyy, mm, dd = int(s[:4]), int(s[4:6]), int(s[6:8])

    if not (1 <= mm <= 12 and 1 <= dd <= 31):
        return "-"
    return f"{yyyy}年{mm:02d}月{dd:02d}日"
#-----------------------------------------------------------
def fetch(player_id, year, season):

    con             = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    with con:
        row = con.execute("""
            SELECT p.player_id, p.name,   p.name_kana,  p.sex,      p.regist_period, p.regions,
                   p.height,    p.weight, p.blood_type, p.birthday, p.birthplace,

                   s.year,      s.season,   s.class_in,
                   s.score_ave, s.top2_ave, s.st_ave,   s.overall_rating

              FROM Players p
         LEFT JOIN Season_result s
                ON s.player_id = p.player_id
               AND s.year      = ? 
               AND s.season    = ?
             WHERE s.player_id = ?
            """,
              (year, season, player_id),).fetchone()

    return row
#-----------------------------------------------------------
def print_row(r):

    if not r:
        print("該当データが見つかりません。")
        return

    print(f" === 基本情報 (players) ===\n")
    print(f" 登録番号   : {r['player_id']}")
    print(f" 氏名       : {r['name'] or '-'}  ( {r['name_kana'] or '-'} )")
    print(f" 性別       : {r['sex'] or '-'}")
    print(f" 支部       : {r['regions'] or '-'}")
    print(f" 登録期     : {r['regist_period'] or '-'}")
    print(f" 身長/体重  : {r['height'] or '-'} cm / {r['weight'] or '-'} kg")
    print(f" 血液型     : {r['blood_type'] or '-'}")
    print(f" 出身地     : {r['birthplace'] or '-'}")
    print(f" 生年月日   : {fmt_birthday_ymd(r['birthday'])}")

    print("\n ======= 期別 成績 =======\n")

    if r['year'] is None or r['season'] is None:
        print("この年・期の期別データは未登録です。")
        return

    if    r['season'] == 1: season = "前"
    elif  r['season'] == 2: season = "後"

    print(f" 適用期     : {r['year']}年  {season}期")
    print(f" 適用級     : {r['class_in'] or '-'}")
    print(f" 能力指数   : {fmt_rate_x100(r['overall_rating'])}")
    print(f" 平均ST     : {fmt_avg_st(r['st_ave'])}")
    print(f" 勝率       : {fmt_rate_x100(r['score_ave'])}")
    print(f" 複勝率     : {fmt_percent_x10(r['top2_ave'])}")

#===========================================================
def main():

    ap = argparse.ArgumentParser(description="Players.Season_resultを出力")
    ap.add_argument("--player", type=int, required=True, help="登録番号(player_id)")
    ap.add_argument("--year",   type=int, required=True, help="対象年(yyyy)")
    ap.add_argument("--season", type=int, required=True, help="対象期(1:前期/2:後期)")
    args = ap.parse_args()

    row = fetch(args.player, args.year, args.season)
    print_row(row)
#-----------------------------------------------------------
if __name__ == "__main__":
    main()
