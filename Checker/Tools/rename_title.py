
import sqlite3, sys, argparse
from pathlib import Path

DB_PATH = Path(r"C:\boatrace\boatrace.db")
#-----------------------------------------------------------
def parse_args():

    p = argparse.ArgumentParser(description="rename_title.py")
    p.add_argument("--date_from", help="期間開始(YYYY-MM-DD)")
    p.add_argument("--date_to",   help="期間終了(YYYY-MM-DD)")

    return p.parse_args()
#-----------------------------------------------------------
def main():

    conn      = sqlite3.connect(DB_PATH)
    cursor    = conn.cursor()
    args      = parse_args()
    date_from = args.date_from
    date_to   = args.date_to

    try:
        select_query = """
            SELECT rowid, series_title
              FROM Races
             WHERE date BETWEEN ? AND ?
               AND grade IN (2, 3, 4, 5)
        """
        cursor.execute(select_query, (date_from, date_to))
        records = cursor.fetchall()

        update_data   = []
        replace_words = ("Ｇ２", "ＧＩ", "Ｇ１", "ＰＧ１", "ＳＧ")

        for rowid, title in records:
            if title is None:
                continue

            new_title = title
            for word in replace_words:
                new_title = new_title.replace(word, "　")

            new_title = new_title.strip()

            if new_title != title:
                update_data.append((new_title, rowid))

        if update_data:
            update_query = """
                UPDATE Races
                   SET series_title = ?
                 WHERE rowid = ?
            """
            cursor.executemany(update_query, update_data)
            conn.commit()

            print(f"{len(update_data)} 件のレコードを成型して上書きしました。")
        else:
            print("成型が必要なレコードはありませんでした。")

    except sqlite3.Error as e:
        print(f"データベースエラーが発生しました: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())