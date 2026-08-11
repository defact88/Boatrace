
1) 起点

実行: C:\boatrace\UI\boatrace_gui.py

起動直後：当日Race_programsが無ければdaily_insert.pyをｻﾌﾞﾌﾟﾛｾｽ実行(モーダル待機)
          summarize_today_info.pyを起動し、各ｻﾌﾞﾌﾟﾛｾｽの実行・当日情報の更新を管理

2) ディレクトリ構成

C:\boatrace/
  boatrace.db                       # SQLite3 DB
  UI/
    boatrace_gui.py                 # エントリ / ルータ / 共通設定
    Dal.py                          # UI用DAL(sqlite3簡易ラッパ)
    summarize_today.py              # 本体起動時に実行するｻﾌﾞﾌﾟﾛｾｽ(当日情報取得各pyの実行管理)
    odds_window.pyw                 # RaceWindow起動時に別ﾌﾟﾛｾｽで実行されるｵｯｽﾞ表示画面

    Subprocess/
      import_Display_run.py         # 展示航走ﾃﾞｰﾀの取得,抽出,挿入
      import_Result_today.py        # ﾚｰｽ結果ﾃﾞｰﾀの取得,抽出,挿入(翌日日時更新時に正規ﾃﾞｰﾀでUPDATE)
      get_today_info.py/
        get_change_info            # 当日変更情報(締切時刻,欠場艇等)の取得,抽出,挿入
        get_cancel_info            # 当日中止ﾚｰｽの取得,抽出,挿入

    Screens/                        # 画面クラス
      DB_ops.py                     # DBOpsScreen(DB参照GUI)クラス
      DB_schem.py                   # DBSchemScreen(DB作成,ｶﾗﾑ追加・削除・更新等UIで操作)クラス
      DB_query.py                   # DBQueryScreen(統計的抽出条件でのDB閲覧GUI)クラス
      Analysis_player.py            # 選手詳細情報画面
      Analysis_venue.py             # レース場詳細情報画面
      RaceSerectScreen.py           # boatrace_bui.pyの表示レース選択画面クラス

    Helpers/
      Custum_func.py                # tk.Frame tk.Label のｵﾘｼﾞﾅﾙ短縮表記ｸﾗｽ

      queries.py/                   # 汎用クエリクラス
          _pack                     # パッキングメソッド

      build_rows.py/
          make_rows                 # 各参照クエリを纏めてentry_rows, data_rowsを生成
          make_sub_rows             # 各参照クエリを纏めてsub_rowsを生成
          query_Race_programs       # Header ﾃﾞｰﾀ参照クエリ
          query_Players             # 選手基本ﾃﾞｰﾀ参照クエリ
          query_result              # 結果ﾃﾞｰﾀ参照クエリ
          query_Display_run         # 展示航走ﾃﾞｰﾀ参照クエリ

      series_idx.py/
          uodate_series_idx         # Mein Right の節間成績表示・更新
          build_day_labels          # 日程ラベルの構築

      scraper_odds.py/
          fetch_all_odds            # odds_window.pywのｵｯｽﾞ取得/ﾊﾟｰｽ ﾍﾙﾊﾟｰ

      ev_scanner.py/
          evaluate_ev               # 予想ｴﾝｼﾞﾝ（未完成）
          persist_odds_snapshot     # oddsﾃﾞｰﾀ挿入ﾍﾙﾊﾟｰ

    Widgets/
      widgets.py/                   # ｻﾌﾞﾌﾟﾚｰｽﾎﾙﾀﾞｰ表示のｳｨｼﾞｪｯﾄ
          framing_graph             # 当該ｺｰｽ別1,2,3着率ｸﾞﾗﾌの表示、主観選手からのｻﾌﾞｸﾞﾗﾌの表示
          framing_figure            # ｽﾘｯﾄ予想図、展示航走ｽﾘｯﾄ、結果ｽﾘｯﾄ の表示
          framing_weather           # 天候ｳｨｼﾞｪｯﾄ(天気、風向)の表示
          framing_held_type_icon    # ﾚｰｽ選択画面開催種別ｱｲｺﾝの表示・更新
          clear_all_lanes           # ﾒｲﾝﾌﾟﾚｰｽﾎﾙﾀﾞｰ内の各ｳｨｼﾞｪｯﾄをｸﾘｱ
          images.py                 # 画像読込/等倍比フィット

  Import/
    import_B_txt.py                 # 出走表ﾃﾞｰﾀ取得ｽｸﾘﾌﾟﾄ
    daily_insert.py                 # 日時更新(全日K,当日Bﾌｧｲﾙのｲﾝﾎﾟｰﾄ:ｽｹｼﾞｭｰﾗ起動ｽｸﾘﾌﾟﾄ)

    ETL_K_results.py                # Races/Race_entries の各ﾃﾞｰﾀ取得・挿入ﾌﾟﾛｾｽのﾗｯﾊﾟｰ
    upsert_Race_result.py           # K_TEXT(公式レース結果情報)ﾌｧｲﾙからRace_resultへのﾃﾞｰﾀ抽出・挿入
    upsert_Result_entry.py          # K_TEXTﾌｧｲﾙからResult_entryへのﾃﾞｰﾀ抽出・挿入ﾌﾟﾛｾｽ
    upsert_Grade.py                 # 公式ﾍﾟｰｼﾞHMLからRace_result.gradeへのﾃﾞｰﾀ抽出・挿入

    import_Fan_txt.py               # FAN_TEXTﾌｧｲﾙからPlayers/Season_resultへのﾃﾞｰﾀ抽出・挿入
    DL_player_img.py                # 公式ﾍﾟｰｼﾞから選手画像の取得ﾌﾟﾛｾｽ
    update_FLstate.py               # Race_entriesからPlayers.flying_st/late_st(今期ﾌﾗｲﾝｸﾞ/出遅れ情報)のﾃﾞｰﾀ算出・挿入ﾌﾟﾛｾｽ
    insert_newcomer.py              # 期始めﾃﾞﾋﾞｭｰ選手ﾃﾞｰﾀ(正式FAN_TEXT公開までの間)の仮取得・挿入


3)主要クラス（コンストラクタ引数）

App(tk.Tk) … ルータ/画面管理
MainScreen(self, parent, app:App)                  … メイン画面
RaceSelectScreen(parent, app)                      … レース選択
RaceWindow(parent, app, date:str, venue_id:int)    … 出走表画面
DBOpsScreen(parent, app, db_path:str)              … DB参照画面
DBQueryScreen(self, parent, app:App, db_path:str)  … ﾃﾞｰﾀ比較検証画面
DBSchemScreen(self, parent, app, db_path)          … スキーマ編集画面


4)共有定数 / パス（代表）

DB_PATH      C:\boatrace\boatrace.db
画像:        C:\boatrace\assets\players\{player_id}.jpg
B-archive:   C:\boatrace\archive\B\TEXT\B{YYMMDD}.TXT
K-archive:   C:\boatrace\archive\K\K{YYMMDD}.TXT
FAN-archive: C:\boatrace\archive\FAN\FAN_TXT\fan{YYMM}.TXT
Temp_file    C:\boatrace\Temp\


5) 依存と約束事

依存方向: App → Screens → Helpers
Screens から Helpers へは相対 import 可：from ..Helpers.images import ...
パッケージ化: UI/, UI/Screens/, UI/Helpers/ に __init__.py 必須
DB接続: 画面側は コンストラクタ引数で db_path を受ける（グローバル直参照しない）

6) 実行フロー（ざっくり）

GUI起動 → App.screens 登録
起動時に当日 Race_programs 有無チェック
無ければ daily_insert.py --date YYYY-MM-DD を実行（モーダル待機）
外部ﾌﾟﾛｾｽsummarize_today_info.pyの起動→メイン画面へ実行ログのミラーリング
レース選択 → 出走表画面（RaceWindow）を開く

7) メモ（運用ルール）

画面分割時は コンストラクタで必要最小の依存を注入（app, db_path, date, venue_id など）
外部依存は Helpers/Screens/Subprocess/Widgets 側で import 集約
指示内容がレイアウトに関わる場合を除いて、UIレイアウトは既存寸法を崩さない
（変更が必要な場合は要確認）
