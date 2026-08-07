# check_finals.py  (series-level finals / pre-finals validator)
# ------------------------------------------------------------
# 年度ごとの開催シリーズを検査して
#   ① 優勝戦 (is_final) … 既存基準を維持
#   ② 準優勝戦 (is_prefinal) … ユーザー提示基準
# の有無・個数を判定するスクリプト。
# ------------------------------------------------------------
# 優勝戦 (is_final)
#   * 通常開催            : 1 レース
#   * Ｗ優勝戦開催       : 2 レース
#   * 例外               : 最終日最終Ｒが中止で 0 レース
#
# 準優勝戦 (is_prefinal)
#   * 開催日数 ?3 日      : 検査対象外（無条件 OK）
#   * 開催日数  =4 日      :
#       - 準優あり        : OK
#       - 準優なし        : 「開催4日&準優なし」として [要調査]
#   * 開催日数 ?5 日      :
#       - 準優 2?5R      : OK
#       - 準優 0R かつ 優勝戦前日 8?12R に中止あり : OK
#       - それ以外        : NG
#
# 追加仕様
#   * 同日内で 7R 以上が中止 (status=='cancelled') の日は「順延」とみなし、
#     開催日数カウントから除外する。
#   * series_title が exclude_list に含まれるシリーズは準優検査をスキップ（OK 扱い）
# ------------------------------------------------------------
from __future__ import annotations

import argparse
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from wcwidth import wcswidth

# ====== 設定 =========================================================
DB_PATH: str = r"C:\boatrace\boatrace.db"
DATEFMT: str = "%Y-%m-%d"
MAX_SPAN_DAYS: int = 10          # シリーズを 1 グループとみなす最大カレンダー幅
CANCELLED_DAY_THRESHOLD: int = 7 # 同日 cancel が 7R 以上なら順延日

# Ｗ優勝戦開催を識別するキーワード
RE_W_FINAL = re.compile(
    r"男女Ｗ|男女ダブル|男女ハーフ|Ｗ優勝戦|ダブル優勝戦|オオムラグランプリ|"
    r"グランプリ／グランプリ|チャレンジカップ／Ｇ２レディースＣＣ|クイーンズクライマックス",
    re.M,
)

# 準優検査を除外するシリーズタイトル（完全一致・適宜編集）
exclude_list: List[str] = [
    # "○○オールレディース",
]
# =====================================================================


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - wcswidth(text))


# ---------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------
def verify_year(year: int) -> None:
    """year 年のシリーズ検査結果を標準出力"""

    date_from = f"{year}-01-01"
    date_to   = f"{year}-12-31"
    next_cut  = f"{year + 1}-01-{MAX_SPAN_DAYS:02d}"

    with _conn() as c:
        total_races = c.execute(
            "SELECT COUNT(*) AS cnt FROM Races WHERE strftime('%Y', date)=?",
            (str(year),),
        ).fetchone()["cnt"]

        rows = c.execute(
            """
            SELECT r.series_title, r.venue_id, r.date,
                   r.status, r.is_final, r.is_prefinal, r.race_no,
                   v.venue_name
              FROM Races r
              JOIN venues v ON v.venue_id = r.venue_id
             WHERE r.date BETWEEN ? AND ?
          ORDER BY r.series_title, r.venue_id, r.date, r.race_no
            """,
            (date_from, next_cut),
        )

        # (series_title, venue_id) 単位で MAX_SPAN_DAYS 幅に切る
        buckets: Dict[Tuple[str, int], List[List[sqlite3.Row]]] = defaultdict(list)
        for r in rows:
            key = ((r["series_title"] or "").strip(), int(r["venue_id"]))
            if not buckets[key]:
                buckets[key].append([r])
                continue
            grp = buckets[key][-1]
            if (
                datetime.strptime(r["date"], DATEFMT)
                - datetime.strptime(grp[0]["date"], DATEFMT)
            ).days <= MAX_SPAN_DAYS:
                grp.append(r)
            else:
                buckets[key].append([r])

        # 集計用
        series_total = 0
        # 優勝戦
        final_ok_cnt = 0
        final_ng: List[Tuple[str, str, str, str]] = []
        # 準優勝戦
        pre_ok_cnt   = 0
        pre_ng:   List[Tuple[str, str, str, str]] = []
        pre_todo: List[Tuple[str, str, str, str]] = []

        # ============================= 検査ループ
        for (title, vid), groups in buckets.items():
            title_str = title or ""
            is_mixed  = bool(RE_W_FINAL.search(title_str))
            excluded  = title_str in exclude_list

            for g in groups:
                start_date = g[0]["date"]
                if start_date > date_to:
                    continue  # 翌年分スキップ
                end_date   = g[-1]["date"]
                venue_name = g[0]["venue_name"]

                series_total += 1

                # ---------- 優勝戦判定（既存基準）
                finals_held = sum(
                    1 for rr in g if rr["status"] == "held" and (rr["is_final"] or 0) == 1
                )
                final_ok = False
                fin_reason = ""

                if is_mixed:
                    if finals_held == 2:
                        final_ok = True
                    elif finals_held == 0:
                        # 0R は最終日最終R 中止なら許容
                        last_rows = [rr for rr in g if rr["date"] == end_date]
                        if last_rows:
                            last_r = max(last_rows, key=lambda r: r["race_no"])
                            final_ok = last_r["status"] == "cancelled"
                        if not final_ok:
                            fin_reason = "優勝戦不足(0)"
                    else:
                        fin_reason = "優勝戦不足(1)" if finals_held == 1 else "優勝戦過多"
                else:
                    if finals_held == 1:
                        final_ok = True
                    elif finals_held == 0:
                        last_rows = [rr for rr in g if rr["date"] == end_date]
                        if last_rows:
                            last_r = max(last_rows, key=lambda r: r["race_no"])
                            final_ok = last_r["status"] == "cancelled"
                        if not final_ok:
                            fin_reason = "優勝戦0"
                    else:
                        fin_reason = "優勝戦2~"

                if final_ok:
                    final_ok_cnt += 1
                else:
                    final_ng.append((title_str, venue_name, f"{start_date}～{end_date}", fin_reason))

                # ---------- 準優勝戦判定
                if excluded:
                    pre_ok_cnt += 1
                    continue

                pre_cnt = sum(
                    1 for rr in g if rr["status"] == "held" and (rr["is_prefinal"] or 0) == 1
                )

                # 開催日数（順延日除外）
                unique_dates = {rr["date"] for rr in g}
                postponed_dates = {
                    d
                    for d in unique_dates
                    if sum(1 for rr in g if rr["date"] == d and rr["status"] == "cancelled")
                    >= CANCELLED_DAY_THRESHOLD
                }
                eff_days = len(unique_dates - postponed_dates)

                pre_ok = False
                pre_todo_flag = False
                pre_reason = ""

                if eff_days <= 3:
                    pre_ok = True

                elif eff_days == 4:
                    if pre_cnt == 0:
                        pre_ok = True
                        pre_todo_flag = True
                        pre_reason = "開催4日&準優なし"
                    else:
                        pre_ok = True  # 準優あり

                else:  # eff_days >= 5
                    if 2 <= pre_cnt <= 5:
                        pre_ok = True
                    elif pre_cnt == 0:
                        prev_calendar = (
                            datetime.strptime(end_date, DATEFMT) - timedelta(days=1)
                        ).strftime(DATEFMT)
                        cancelled_prev_day = any(
                            rr["date"] == prev_calendar
                            and 8 <= rr["race_no"] <= 12
                            and rr["status"] == "cancelled"
                            for rr in g
                        )
                        if cancelled_prev_day:
                            pre_ok = True
                        else:
                            pre_reason = "準優不足"
                    else:
                        pre_reason = "準優過多" if pre_cnt > 5 else "準優不足"

                if pre_ok and not pre_todo_flag:
                    pre_ok_cnt += 1
                elif pre_todo_flag:
                    pre_todo.append((title_str, venue_name, f"{start_date}～{end_date}", pre_reason))
                else:
                    pre_ng.append((title_str, venue_name, f"{start_date}～{end_date}", pre_reason))

        # ============================= 結果出力
        print(f"\n=== 優勝戦検査 ({year}年・シリーズ幅≦{MAX_SPAN_DAYS}日) ===")
        print(f"対象全レース数   : {total_races}")
        print(f"対象シリーズ数   : {series_total}")
        print(f"検査OKシリーズ数 : {final_ok_cnt}")
        print(f"検査NGシリーズ   : {len(final_ng)} 件")
        if final_ng:
            print("---- NG一覧 ----")
            for t, v, p, r in final_ng:
                print(f"[{_pad(t, 40)}] [{v}] [{p}] [{r}]")

        print(f"\n=== 準優勝戦検査 ({year}年) ===")
        print(f"対象シリーズ数   : {series_total}")
        print(f"検査OKシリーズ数 : {pre_ok_cnt}")
        print(f"要調査シリーズ   : {len(pre_todo)} 件")
        print(f"検査NGシリーズ   : {len(pre_ng)} 件")
        if pre_todo:
            print("---- 要調査一覧 ----")
            for t, v, p, r in pre_todo:
                print(f"[{_pad(t, 40)}] [{v}] [{p}] [{r}]")
        if pre_ng:
            print("---- NG一覧 ----")
            for t, v, p, r in pre_ng:
                print(f"[{_pad(t, 40)}] [{v}] [{p}] [{r}]")


# ---------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Validate is_final / is_prefinal per series")
    ap.add_argument("--year", type=int, required=True, help="対象年 (YYYY)")
    args = ap.parse_args()
    verify_year(args.year)


if __name__ == "__main__":
    main()