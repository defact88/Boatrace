# -*- coding: utf-8 -*-
# C:\boatrace\Management\word_replacer_gui.pyw

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import os
import csv
import shutil
import datetime
import ctypes
import sys
import re  # 正規表現モジュールを追加

def minimize_console():
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd != 0:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass

minimize_console()

BASE_DIR     = Path(r"C:\boatrace\Management")
CSV_FILEMAP  = BASE_DIR / "file_map.csv"
BACKUP_ROOT  = Path(r"C:\boatrace\BACKUP")
ICON_PATH    = BASE_DIR / r"Icon\GUI.ico"

MUI          = "Meiryo UI"
BG_COLOR     = "#222222"
PANEL_BG     = "#252525"
ENTRY_BG     = "#333333"
TEXT_BG      = "#1e1e1e"
FG_COLOR     = "#FFFFFF"
SELCOL       = "#b1dbcc"
EXEC_BTN_BG  = "#AACCFF"
LOG_FG       = "#66CCFF"
SUCCESS_FG   = "#66CC99"
WARN_FG      = "#FFCC66"
ERR_FG       = "#FF6666"

GUI, MUI, HNH, CBR     = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, SK, BD = "groove", "solid", "ridge", "raised", "sunken", "bold"
ALL, CT                = "nsew", "center"
#===============================================================================
class WordReplacerGUI(tk.Tk):

    def __init__(self):
        super().__init__()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.title("")
        self.geometry("820x750+1750+420")
        self.configure(bg=BG_COLOR)
        self.resizable(True, True)

        try:
            self.iconbitmap(ICON_PATH)
        except Exception:
            pass

        self.option_add("*Font", (MUI, 10))
        self.option_add("*Foreground", FG_COLOR)
        self.option_add("*Background", BG_COLOR)

        self.file_map     = []
        self.file_vars    = {}
        self.file_records = {}

        self.create_widgets()
        self.load_file_map()
    #-------------------------------------------------------
    def create_widgets(self):

        # ヘッダー & 設定エリア (上部)
        frame_top = tk.Frame(self, bg=PANEL_BG, bd=1, relief="ridge")
        frame_top.pack(fill="x", padx=10, pady=(10, 5))

        # CSVパス指定
        fr_csv = tk.Frame(frame_top, bg=PANEL_BG)
        fr_csv.pack(fill="x", padx=10, pady=5)
        tk.Label(fr_csv, text="CSV FileMap:", font=(MUI, 10, "bold"), bg=PANEL_BG, fg=LOG_FG).pack(side="left")
        self.lbl_csv_path = tk.Label(fr_csv, text=str(CSV_FILEMAP), bg=PANEL_BG, fg="#AAAAAA", anchor="w")
        self.lbl_csv_path.pack(side="left", padx=10, fill="x", expand=True)
        tk.Button(fr_csv, text="再読込", bg="#444444", fg=FG_COLOR, command=self.load_file_map).pack(side="right")

        # 置換設定
        fr_words = tk.Frame(frame_top, bg=PANEL_BG)
        fr_words.pack(fill="x", padx=10, pady=5)

        tk.Label(fr_words, text="置換前ワード:", bg=PANEL_BG).grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.entry_old = tk.Entry(fr_words, bg=ENTRY_BG, fg=FG_COLOR, insertbackground=FG_COLOR, width=25)
        self.entry_old.grid(row=0, column=1, sticky="w", padx=5, pady=3)

        tk.Label(fr_words, text="置換後ワード:", bg=PANEL_BG).grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.entry_new = tk.Entry(fr_words, bg=ENTRY_BG, fg=FG_COLOR, insertbackground=FG_COLOR, width=25)
        self.entry_new.grid(row=1, column=1, sticky="w", padx=5, pady=3)

        # 一致条件トグルボタン
        self.match_mode = tk.StringVar(value="部分一致")

        def toggle_match_mode():
            if self.match_mode.get() == "部分一致":
                self.match_mode.set("単語")
                self.btn_toggle.config(text="一致条件: 単語\n(スペース等で独立)", bg="#779977")
            else:
                self.match_mode.set("部分一致")
                self.btn_toggle.config(text="一致条件: 部分一致\n(文字の一部でも対象)", bg="#555555")

        self.btn_toggle = tk.Button(
            fr_words, text="一致条件: 部分一致\n(文字の一部でも対象)", bg="#555555", fg=FG_COLOR,
            command=toggle_match_mode, width=17, font=(MUI, 9)
        )
        self.btn_toggle.grid(row=0, column=2, rowspan=2, padx=(10, 5), pady=3, sticky="nsew")

        # 一括置換実行ボタン
        self.btn_exec = tk.Button(
            fr_words, text="一括置換実行\n(自動バックアップ付)", 
            font=(MUI, 10, "bold"), bg=EXEC_BTN_BG, fg="#000000",
            width=18, height=2, command=self.on_execute_replace
        )
        self.btn_exec.grid(row=0, column=3, rowspan=2, padx=5, pady=3, sticky="nsew")

        # 検索(カウント)ボタン
        self.btn_search = tk.Button(
            fr_words, text="検索\n(カウントのみ)", 
            font=(MUI, 10, "bold"), bg="#FFEEAA", fg="#000000",
            width=14, height=2, command=self.on_search_word
        )
        self.btn_search.grid(row=0, column=4, rowspan=2, padx=(5, 20), pady=3, sticky="nsew")

        # ファイル選択ツリーエリア (中央)
        frame_mid = tk.Frame(self, bg=BG_COLOR)
        frame_mid.pack(fill="both", expand=True, padx=10, pady=5)

        fr_tools = tk.Frame(frame_mid, bg=BG_COLOR)
        fr_tools.pack(fill="x", pady=(0, 5))
        tk.Button(fr_tools, text="全選択", bg="#444444", fg=FG_COLOR, width=8, command=lambda: self.toggle_all(True)).pack(side="left", padx=(0, 5))
        tk.Button(fr_tools, text="全解除", bg="#444444", fg=FG_COLOR, width=8, command=lambda: self.toggle_all(False)).pack(side="left")
        tk.Label(fr_tools, text="※選択されたファイルは実行前に C:\\boatrace\\BACKUP へ自動保存されます", bg=BG_COLOR, fg="#888888").pack(side="left", padx=15)

        fr_canvas = tk.Frame(frame_mid, bg=ENTRY_BG, bd=1, relief="sunken")
        fr_canvas.pack(fill="both", expand=True)
        #-----------
        def _mw(e):
            self.canvas.yview_scroll(int(-1 *(e.delta / 120)), "units")
        #-----------
        def _on_conf(event=None):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        #-----------
        self.canvas = tk.Canvas(fr_canvas, bg=ENTRY_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(fr_canvas, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=ENTRY_BG)

        self.scroll_frame.bind("<Configure>", _on_conf)

        self.canvas.bind("<Enter>", lambda e:self.canvas.bind_all("<MouseWheel>", _mw))
        self.canvas.bind("<Leave>", lambda e:self.canvas.unbind_all("<MouseWheel>"))

        self.canvas.create_window((0,0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 実行結果サマリーエリア (下部拡張エリア)
        frame_bottom = tk.LabelFrame(self, text=" 実行ログ ＆ サマリー ", bg=BG_COLOR, fg=LOG_FG, font=(MUI, 10, "bold"))
        frame_bottom.pack(fill="x", padx=10, pady=(5,10))

        fr_log = tk.Frame(frame_bottom, bg=BG_COLOR)
        fr_log.pack(fill="both", expand=True, padx=5, pady=5)

        self.txt_log = tk.Text(fr_log, bg=TEXT_BG, fg=FG_COLOR, height=12, font=("Consolas", 9), relief="flat", wrap="none")
        log_scroll_y = ttk.Scrollbar(fr_log, orient="vertical", command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=log_scroll_y.set)

        log_scroll_y.pack(side="right", fill="y")
        self.txt_log.pack(side="left", fill="both", expand=True)

        self.txt_log.tag_config("SUCCESS", foreground=SUCCESS_FG)
        self.txt_log.tag_config("WARN",    foreground=WARN_FG)
        self.txt_log.tag_config("ERROR",   foreground=ERR_FG)
        self.txt_log.tag_config("INFO",    foreground=LOG_FG)

    #-------------------------------------------------------
    def log(self, text: str, tag: str = None):

        self.txt_log.insert("end", text + "\n", tag)
        self.txt_log.see("end")

    #-------------------------------------------------------
    def load_file_map(self):

        for w in self.scroll_frame.winfo_children():
            w.destroy()

        self.file_vars.clear()
        self.file_records.clear()
        self.file_map.clear()

        if not CSV_FILEMAP.exists():
            self.log(f"[エラー] {CSV_FILEMAP} が見つかりません。", "ERROR")
            return

        try:
            with open(CSV_FILEMAP, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    norm = {(k or "").strip(): (v or "").strip() for k, v in r.items()}
                    self.file_map.append(norm)
        except Exception as e:
            self.log(f"[エラー] file_map.csv の読み込み失敗: {e}", "ERROR")
            return

        grouped = {}

        for r in self.file_map:
            cat    = r.get("カテゴリ") or "未分類"
            subcat = r.get("サブカテゴリ") or "未分類"
            grouped.setdefault(cat, {}).setdefault(subcat, []).append(r)

        for cat, subcats in grouped.items():
            lbl_cat = tk.Label(self.scroll_frame, text=f"■ {cat}", font=(MUI,10,BD), bg=ENTRY_BG, fg=SELCOL, anchor="w")
            lbl_cat.pack(fill="x", padx=5, pady=(8, 2))

            for subcat, records in subcats.items():
                lbl_sub = tk.Label(self.scroll_frame, text=f"  └ {subcat}", font=(MUI,9,BD), bg=ENTRY_BG, fg="#AAAAAA", anchor="w")
                lbl_sub.pack(fill="x", padx=15, pady=(3, 1))

                for rec in records:
                    fname     = rec.get("ファイル名", "")
                    fpath_str = rec.get("実行パス", "")
                    
                    var = tk.BooleanVar(value=False)
                    self.file_vars[fpath_str]    = var
                    self.file_records[fpath_str] = rec

                    fr_item = tk.Frame(self.scroll_frame, bg=ENTRY_BG)
                    fr_item.pack(fill="x", padx=25, pady=1)

                    chk = tk.Checkbutton( fr_item, text=f"{fname}", variable=var, font=(MUI,9),
                                          bg=ENTRY_BG, fg=FG_COLOR, activebackground=ENTRY_BG,
                                                                          selectcolor=BG_COLOR )
                    chk.pack(side="left")

                    lbl_path = tk.Label(fr_item, text=f" ({fpath_str})", bg=ENTRY_BG, fg="#666666", font=(MUI, 8))
                    lbl_path.pack(side="left")

        self.log(f"[情報] {len(self.file_map)} 件のファイルマッピングを読み込みました。", "INFO")

    #-------------------------------------------------------
    def toggle_all(self, state: bool):

        for var in self.file_vars.values():
            var.set(state)

    #-------------------------------------------------------
    def backup_single_file(self, record:dict, src:Path) -> tuple[bool, str]:

        category = record.get("カテゴリ")     or "Unknown"
        subcat   = record.get("サブカテゴリ") or "Unknown" 
        today    = datetime.datetime.now().strftime("%Y%m%d")
        dst_dir  = BACKUP_ROOT / category / subcat / src.stem

        try:
            dst_dir.mkdir(parents=True, exist_ok=True)
            base_name = f"{today}_{src.name}"
            dst_file  = dst_dir / base_name
            counter   = 2

            while dst_file.exists():
                stem, ext = os.path.splitext(base_name)
                dst_file  = dst_dir / f"{stem}({counter}){ext}"
                counter  += 1

            shutil.copy2(src, dst_file)

            return True, str(dst_file)

        except Exception as e:
            return False, str(e)

    #-------------------------------------------------------
    def get_search_pattern(self, old_word: str):
        """一致条件に応じた正規表現パターンを生成して返す"""
        mode_str = self.match_mode.get()
        if mode_str == "単語":
            # (?<!\S) : 直前に非空白文字がない
            # (?!\S)  : 直後に非空白文字がない
            # （両端がスペース、タブ、改行、または行頭・行末であるワードにマッチ）
            return re.compile(r'(?<!\S)' + re.escape(old_word) + r'(?!\S)')
        else:
            return re.compile(re.escape(old_word))

    #-------------------------------------------------------
    def on_search_word(self):
        """ファイルの変更を行わず、対象ワードの出現回数のみをチェックしてサマリーに出力する"""
        old_word = self.entry_old.get()

        if not old_word:
            messagebox.showwarning("警告", "検索対象の「置換前ワード」を入力してください。")
            return

        target_paths = [path for path, var in self.file_vars.items() if var.get()]

        if not target_paths:
            messagebox.showwarning("警告", "対象ファイルが選択されていません。")
            return

        self.txt_log.delete("1.0", "end")
        mode_str = self.match_mode.get()
        self.log(f"=== 検索処理開始: '{old_word}' (条件: {mode_str}) ===", "INFO")

        pattern = self.get_search_pattern(old_word)

        total_files = len(target_paths)
        hit_files   = 0
        total_hits  = 0
        error_count = 0

        for fpath_str in target_paths:
            src = Path(fpath_str)
            rec = self.file_records.get(fpath_str, {})
            fname = rec.get("ファイル名", src.name)

            if not src.exists():
                self.log(f"× [{fname}] ファイルが存在しません: {fpath_str}", "ERROR")
                error_count += 1
                continue

            try:
                content = ""
                try:
                    with open(src, "r", encoding="utf-8") as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(src, "r", encoding="utf-8-sig") as f:
                        content = f.read()

                # 正規表現によるカウント
                matches = pattern.findall(content)
                count = len(matches)

                if count > 0:
                    hit_files += 1
                    total_hits += count
                    self.log(f"○ [{fname}] 検知: {count} 個", "SUCCESS")
                else:
                    self.log(f"- [{fname}] 対象ワードなし", "WARN")

            except Exception as e:
                self.log(f"× [{fname}] 読み込みエラー: {e}", "ERROR")
                error_count += 1

        self.log("\n================ 検索結果サマリー ================", "INFO")
        self.log(f"対象ファイル数 : {total_files} 件", "INFO")
        self.log( f"ヒットファイル : {hit_files} 件", "SUCCESS" if hit_files > 0 else "INFO" )
        self.log( f"合計検知数     : {total_hits} 箇所", "SUCCESS" if total_hits > 0 else "INFO" )
        if error_count > 0:
            self.log(f"エラー発生数   : {error_count} 件", "ERROR")
        self.log("==================================================", "INFO")

    #-------------------------------------------------------
    def on_execute_replace(self):

        old_word = self.entry_old.get()
        new_word = self.entry_new.get()

        if not old_word:
            messagebox.showwarning("警告", "置換前ワードを入力してください。")
            return

        target_paths = [path for path, var in self.file_vars.items() if var.get()]

        if not target_paths:
            messagebox.showwarning("警告", "対象ファイルが選択されていません。")
            return

        if not messagebox.askyesno("確認", f"選択された {len(target_paths)} 件のファイルを置換しますか？\n（事前にバックアップが保存されます）"):
            return

        self.txt_log.delete("1.0", "end")
        mode_str = self.match_mode.get()
        self.log(f"=== 置換処理開始: '{old_word}' -> '{new_word}' (条件: {mode_str}) ===", "INFO")

        pattern = self.get_search_pattern(old_word)

        total_files        = len(target_paths)
        updated_files      = 0
        total_replacements = 0
        error_count        = 0

        for fpath_str in target_paths:
            src = Path(fpath_str)
            rec = self.file_records.get(fpath_str, {})
            fname = rec.get("ファイル名", src.name)

            if not src.exists():
                self.log(f"× [{fname}] ファイルが存在しません: {fpath_str}", "ERROR")
                error_count += 1
                continue

            # --- バックアップ処理 ---
            bk_ok, bk_res = self.backup_single_file(rec, src)
            if not bk_ok:
                self.log(f"× [{fname}] バックアップ失敗のためスキップ: {bk_res}", "ERROR")
                error_count += 1
                continue

            try:
                content       = ""
                encoding_used = "utf-8"

                try:
                    with open(src, "r", encoding="utf-8") as f:
                        content = f.read()
                except UnicodeDecodeError:
                    encoding_used = "utf-8-sig"
                    with open(src, "r", encoding="utf-8-sig") as f:
                        content = f.read()

                # 正規表現による検索
                matches = pattern.findall(content)
                count = len(matches)

                if count > 0:
                    # lambda を使い、置換文字列にエスケープ文字等が含まれていても安全に置換する
                    new_content = pattern.sub(lambda m: new_word, content)
                    
                    with open(src, "w", encoding=encoding_used) as f:
                        f.write(new_content)

                    updated_files      += 1
                    total_replacements += count

                    self.log( f"○ [{fname}] 置換成功: {count} 件更新"
                              f" (BK: {os.path.basename(bk_res)})", "SUCCESS" )
                else:
                    self.log(f"- [{fname}] 対象ワードなし (0件変更, BK保存済)", "WARN")

            except Exception as e:
                self.log(f"× [{fname}] 置換エラー: {e}", "ERROR")
                error_count += 1

        self.log("\n================ 実行結果サマリー ================", "INFO")
        self.log(f"対象ファイル数 : {total_files} 件", "INFO")
        self.log( f"更新ファイル数 : {updated_files} 件",
                  "SUCCESS" if updated_files > 0 else "INFO" )
        self.log( f"合計置換箇所   : {total_replacements} 箇所",
                  "SUCCESS" if total_replacements > 0 else "INFO" )
        if error_count > 0:
            self.log(f"エラー発生数   : {error_count} 件", "ERROR")
        self.log("==================================================", "INFO")

        messagebox.showinfo("完了", f"処理が完了しました。\n"
                                    f"更新ファイル: {updated_files}/{total_files} 件\n"
                                    f"総置換数: {total_replacements} 箇所")

    # --------------------------------------------
    def _on_close(self):

        try:
            ctypes.windll.kernel32.FreeConsole()
            sys.exit()

        except Exception: pass
#===============================================================================
if __name__ == "__main__":
    app = WordReplacerGUI()
    app.mainloop()