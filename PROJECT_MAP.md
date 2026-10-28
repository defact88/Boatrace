
1) 起点

実行: C:\boatrace\UI\boatrace_gui.py

起動直後：当日Race_programsが無ければdaily_insert.pyをｻﾌﾞﾌﾟﾛｾｽ実行(モーダル待機)
          summarize_today_info.pyを起動し、各ｻﾌﾞﾌﾟﾛｾｽの実行・当日情報の更新を管理

2) ディレクトリ構成

```
boatrace/

  boatrace.db                        # SQLite3 DataBase

  Dal.py                             # UI用Data Access Layer(sqlite3簡易ﾗｯﾊﾟｰ)

  UI/
    boatrace_gui.py/                 
      APP                            # エントリ/ルータ/共通設定
      MainScreen                     # ﾒｲﾝﾒﾆｭｰ/外部ﾌﾟﾛｾｽ連携
    summarize_today.py               # 当日情報取得ｻ各ﾌﾞﾌﾟﾛｾｽの実行管理ﾚｲﾔｰ(botrace_gui.py起動時に実行)
    odds_window.py(OddsWindow)       # RaceWindowと並列でｻﾌﾞﾌﾟﾛｾｽ表示されるｵｯｽﾞ画面
    results_window.py(ResultsWindow) # RaceWindowと並列でｻﾌﾞﾌﾟﾛｾｽ表示されるﾚｰｽ結果画面
    Window/
      race_window.py                 # 出走表メイン
      analysis_player.py             # PlayerAnalysisWindow・・・選手詳細情報ｳｨﾝﾄﾞｳ
      analysis_venue.py              # VenueAnalysisWindow・・・ ﾚｰｽ場詳細情報ｳｨﾝﾄﾞｳ
      analysis_motor.py              # MotorAnalysisWindow・・・モーター詳細情報ｳｨﾝﾄﾞｳ
      classification.py              # PlayerClassificationWindow・・・同期/同支部選手一覧表示ｳｨﾝﾄﾞｳ
    Screens/                         # 遷移画面クラス
      race_serect.py                 # RaceSelectScreen・・・RaceWindow表示レース選択画面
      DB_ops.py                      # DBOpsScreen・・・DB参照
      DB_schem.py                    # DBSchemScreen・・・ﾃｰﾌﾞﾙ/ｶﾗﾑ 追加/削除/更新
      DB_query.py                    # DBQueryScreen・・・特定ﾚｰｽ条件でﾚｰｽ結果の比較検証
      player_Favor.py                # 指定条件成績 選手検索, 注目選手登録/管理画面
    Scraper/                         # summarize_today.pyから管理/実行
      get_Before_info.py             # 展示航走/直前情報ﾃﾞｰﾀの取得/ﾊﾟｰｽ/挿入
      get_results_today.py           # ﾚｰｽ結果ﾃﾞｰﾀの取得/ﾊﾟｰｽ/挿入(翌日の日時更新時に正規ﾃﾞｰﾀでUPDATE)
      get_today_info.py/
          get_change_info            # 当日変更情報(締切時刻変更,欠場艇等)の取得/ﾊﾟｰｽ/挿入
          get_cancel_info            # 当日中止ﾚｰｽの取得/ﾊﾟｰｽ/挿入
      get_payouts.py/
          upsert_payouts             # 払戻情報(Payouts)へのﾃﾞｰﾀ取得/ﾊﾟｰｽ挿入ｽｸﾘﾌﾟﾄ
      get_oriten_info.py             # ｵﾘｼﾞﾅﾙ展示情報 取得/ﾊﾟｰｽ/挿入ｽｸﾘﾌﾟﾄ
      scraper_odds.py/
          fetch_all_odds             # OddsWindowのｵｯｽﾞﾃﾞｰﾀ ｽｸﾚｲﾋﾟﾝｸﾞ/ﾊﾟｰｽ
    Helpers/
      Custum_func.py                 # tkinterのｵﾘｼﾞﾅﾙ短縮表記ｸﾗｽ, ﾒｿｯﾄﾞ
      queries.py/                    # DB 汎用クエリクラス
          _pack                      # パッキングメソッド
      build_rows.py/                 # RaceWindow表示ﾃﾞｰﾀの取得(DB)/構成
          make_rows                  # 各ｸｴﾘからのﾃﾞｰﾀを纏めてentry_rows, data_rowsを生成
          make_sub_rows              # 各ｸｴﾘからのﾃﾞｰﾀを纏めてsub_rowsを生成
          query_Race_programs        # Header ﾃﾞｰﾀ用クエリ
          query_Players              # 選手基本ﾃﾞｰﾀ用クエリ
          query_result               # 結果ﾃﾞｰﾀ用クエリ
          query_before_info          # 直前情報 展示航走ﾃﾞｰﾀ用クエリ
      build_series_idx.py/
          uodate_series_idx          # RaceWindow Main Right の節間成績ﾃﾞｰﾀ 表示/更新
          build_day_labels           # 日程ラベルの構築
      ev_scanner.py/
          evaluate_ev                # 予想ｴﾝｼﾞﾝ（未完成）
          persist_odds_snapshot      # oddsﾃﾞｰﾀ挿入, evaluate_evのﾗｯﾊﾟｰ

    Widgets/
      widgets.py/
          framing_graph              # 当該ｺｰｽ別1,2,3着率ｸﾞﾗﾌ、主観選手からのｻﾌﾞｸﾞﾗﾌ
          framing_figure             # ｽﾘｯﾄ予想図, 展示航走ｽﾘｯﾄ図, ﾚｰｽ結果ｽﾘｯﾄ図
          framing_weather            # 天候ｱｲｺﾝ(天気、風向)
          framing_held_type_icon     # ﾚｰｽ選択画面 開催種別ｱｲｺﾝ
          clear_widgets              # 各ｳｨｼﾞｪｯﾄをｸﾘｱ
          set_player_image           # 画像読込/等倍比フィット
      placeholder.py/
          main_placeholder           # RaceWindowのメイン表示部(上部)枠組み
          sub_placeholder            # RaceWindowのサブ表示部(下部)枠組み
      center_widgets.py/             # RaceWindow/main_placeholder中央部切り替え式可変ウィジェット

  Import/
    B/
      import_B_txt.py                # B_txt(当日出走表ﾃﾞｰﾀ)からRace_programsへの取得/ﾊﾟｰｽ/挿入ｽｸﾘﾌﾟﾄ
    K/
      ETL_K_results.py               # Races/Race_entriesへの各ﾃﾞｰﾀ取得/挿入ﾌﾟﾛｾｽのﾗｯﾊﾟｰ
      parse and upsert.py            # K_TEXT(公式ﾚｰｽ結果ﾌｧｲﾙ)からののﾊﾟｰｽ/挿入ﾌﾟﾛｾｽ
      upsert_Grade.py                # 公式ﾍﾟｰｼﾞHMLからRace_result.gradeへのﾃﾞｰﾀ抽出・挿入
    FAN/
      import_Fan_txt.py              # FAN_TEXTﾌｧｲﾙからPlayers/Season_resultへのﾃﾞｰﾀ抽出/挿入
      DL_player_img.py               # 公式ﾍﾟｰｼﾞから選手画像の取得ﾌﾟﾛｾｽ
      insert_newcomer.py             # 期始めﾃﾞﾋﾞｭｰ選手ﾃﾞｰﾀ(正式FAN_TEXT公開までの間)の仮取得/挿入
    Updata/
      daily_insert.py                # 日時更新(前日Kﾌｧｲﾙ/当日Bﾌｧｲﾙのｲﾝﾎﾟｰﾄ, 前日直線情報ﾃﾞｰﾀ/ｵｯｽﾞﾃﾞｰﾀの補填)
      ETL_odds_data.py               # ｵｯｽﾞﾃﾞｰﾀ(Odds)を指定期間で一括取得
      ETL_Before_info.py             # 展示航走/直線情報(Before_info)を指定期間で一括取得
      update_FLstate.py              # Race_entriesからPlayers.flying_st, late_st(今期ﾌﾗｲﾝｸﾞ,出遅れ)ﾃﾞｰﾀ算出/挿入ﾌﾟﾛｾｽ
      get_player_schedule.py         # 選手の出走予定データの取得/ﾊﾟｰｽ/挿入ｽｸﾘﾌﾟﾄ

  Checker/
    data/
      check_odds_data.py             # テーブルOdds_xxデータの検査スクリプト
      check_K_files                  # 公式配布Kﾌｧｲﾙ過去の不足分を検査
    Player/
      check_score_ave.py             # 期単位で指定選手の公式得点率とDBデータ算出得点率の整合性をチェック
      check_score_ave_ALL.py         # check_score_ave.pyを全選手対象で実行
      list_player_in_final.py        # 指定選手 指定期における優勝戦出走回数と詳細を表示
      show_player_term.py            
    Race/
      check_Before_info.py           # 展示航走データ(Before_info)のデータ欠損チェック
      check_finals.py                # Races.is_final(優勝戦)の取得漏れをチェック
      check_series_title.py          # Races.series_titleの節間の表記揺れをチェック
      update_is_prefinal.py          # 準優勝線(Races.is_prefinal)を更新
```

3)主要クラス（コンストラクタ引数）

App(tk.Tk) … ルータ/画面管理
MainScreen(self, parent, app:App)                  … メイン画面
RaceSelectScreen(parent, app)                      … レース選択画面
RaceWindow(parent, app, date:str, venue_id:int)    … 出走表画面
DBOpsScreen(parent, app, db_path:str)              … DB参照画面
DBQueryScreen(self, parent, app:App, db_path:str)  … ﾃﾞｰﾀ比較検証画面
DBSchemScreen(self, parent, app, db_path)          … スキーマ編集画面


4)共有定数 / パス（代表）

DB_PATH      C:\boatrace\boatrace.db
選手画像:    C:\boatrace\assets\players\{player_id}.jpg
B-archive:   C:\boatrace\archive\B\TEXT\B{YYMMDD}.TXT
K-archive:   C:\boatrace\archive\K\K{YYMMDD}.TXT
FAN-archive: C:\boatrace\archive\FAN\FAN_TXT\fan{YYMM}.TXT
ログ:        C:\boatrace\Archive\logs\
Temp_file    C:\boatrace\Temp\


5) 依存と約束事

依存方向: App → Screens → Helpers/Widgets
Screens から Helpers へは相対 import 可：(from ..Helpers.images import ...)
パッケージ化: UI/, UI/Screens/, UI/Helpers/, UI/Widgets/ に __init__.py 必須
DB接続: 画面側は コンストラクタ引数で db_path を受ける
DB書込み: Data Access Layer(Dal.py)を使用

6) 実行フロー（ざっくり）

GUI起動 → App.screens 登録
起動時に当日 Race_programs 有無チェック
無ければ daily_insert.py --date YYYY-MM-DD を実行（モーダル待機）
外部ﾌﾟﾛｾｽsummarize_today_info.pyの起動→メイン画面へ実行ログのミラーリング
レース選択 → 出走表画面（RaceWindow）を開く

7) メモ（運用ルール）

・画面分割時は コンストラクタで必要最小の依存を注入（app, db_path, date, venue_id など）
・外部依存は Helpers/Screens/Subprocess/Widgets 側で import 集約
・指示内容がレイアウトに関わる場合を除いて、GUIレイアウトは既存寸法を崩さない（変更が必要な場合は要確認）
・使用/実行は固定PC環境・固定モニター・固定ウィンドウサイズ・固定レイアウト・固定ウィジェットサイズ
・処理/表示において他環境への汎用性は不要。よってttkでしか機能実現しない場合を除いてなるべくtkを使用する

