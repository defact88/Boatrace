# -*- coding: utf-8 -*-
# C:\boatrace\UI\results_window.py

import argparse, threading, sys, sqlite3, json
import tkinter as tk
from datetime    import datetime as dt
from Custum_func import cFr, cLbl, cBtn

DB = r"C:\boatrace\boatrace.db"

GUI, MUI, HNH      = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy"
GR, SD, RD, RA, BD = "groove", "solid", "ridge", "raised", "bold"
ALL, CT            = "nsew", "center"

VENUES = [ "", "桐生", "戸田", "江戸川", "平和島", "多摩川", "浜名湖",  "蒲郡", "常滑",
                 "津", "三国", "びわこ", "住之江",   "尼崎",   "鳴門",  "丸亀", "児島",
               "宮島", "徳山",   "下関",   "若松",   "芦屋",   "福岡",  "唐津", "大村", ]

FRM_BG = {1:"#FFFFFF", 2:"#333333", 3:"#D40000", 4:"#0066CC", 5:"#FFD400", 6:"#008A2E"}
FRM_FG = {1:"#000000", 2:"#FFFFFF", 3:"#FFFFFF", 4:"#FFFFFF", 5:"#000000", 6:"#FFFFFF"}

MAIN_BG    = "#F0F4FA"
FAULT_FG   = "#D40000"
ABSENT_BG  = "#CCCCCC"
NAME_BG    = "#FFFFFF"
PANEL_BG   = "#F0F4FA"
HDR_BG     = "#2B4A7A"
HDR_FG     = "#FFFFFF"
TBL_HDR_BG = "#2F75B5"
TBL_HDR_FG = "#FFFFFF"
BAR_COLOR  = "#0069D5"
BAR_TRACK  = "#f7f9ff" #"#ebeef5""#E4E9F5"

RESERVED_TOP_H = 330

LBL_W  = 50     # レース番号ラベル 列幅
BOAT_W = 160    # 艇番+選手名 セル幅
MOVE_W = 60     # 決まり手 列幅
ROW_H  = 50     # レース行 高さ

SUM_LBL_W   = 70    # コース別分布表 左端ラベル列幅
SUM_COL_W   = 170   # コース別分布表 データ列幅
SUM_ROW_H   = 50    # コース別分布表 行高さ
BAR_TRACK_W = 165   # 棒グラフ トラック幅
BAR_H       = 12    # 棒グラフ 高さ

#===============================================================================
class ResultsWindow(tk.Tk):

    def __init__(self, date:str, venue_id:int):
        super().__init__()

        self.title("")
        self.geometry("1150x1400+1295+0")
        self.resizable(False, False)
        self.configure(bg=PANEL_BG)

        self.date             = date
        self.venue_id         = venue_id
        self.race_rows        = {}
        self.course_rank_cnt  = {}
        self.finished_races   = 0

        self._build_ui()
        self._load_data()
        self._render()

        th = threading.Thread(target=self._read_stdin_loop, daemon=True)
        th.start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -------- 標準入力待受スレッドループ --------
    def _read_stdin_loop(self):

        try:
            for line in iter(sys.stdin.readline, ''):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                self.after(0, lambda d=data: self._handle_command(d))
        except Exception:
            pass

    # ----------- 受信コマンド処理 ---------------
    def _handle_command(self, d: dict):

        state = d.get("state")
        if state == "stop":
            self._on_close()
            return

        if state == "withdraw":
            self.withdraw()
        elif state in ("deiconify", "normal"):
            self.deiconify()

        new_date  = d.get("date",  self.date)
        new_venue = d.get("venue", self.venue_id)

        changed = (new_date != self.date or int(new_venue) != self.venue_id)

        if changed:
            self.date     = new_date
            self.venue_id = int(new_venue)
            self._load_data()
            self._render()

    # ----------- ウィンドウ終了処理 -------------
    def _on_close(self):

        try: self.destroy()
        except Exception: pass

    #====================== UI 構築 ========================
    def _build_ui(self):

        # ヘッダー
        hdr = cFr(self, bg=HDR_BG, H=36) ;hdr._pack(fill="x", side="top")

        # 将来の追加用の余白(上部)
        cFr(self, bg=PANEL_BG, H=RESERVED_TOP_H)._pack(fill="x", side="top")

        self.lbl_title = cLbl(hdr, text="", bg=HDR_BG, fg=HDR_FG, font=(MUI,9,BD))
        self.lbl_title._pack(side="left", px=10, py=5)

        cBtn( hdr, text=" 更   新 ", Com=self._on_refresh, bg="#4A7ACC", fg="white",
                  font=(GUI,9,BD), Rel=RA, px=8 )._pack(side="right", px=10, py=4)

        body = cFr(self, bg=PANEL_BG) ;body._pack(fill="both", expand=True)

        self.top_frame    = cFr(body, bg=PANEL_BG)
        self.top_frame._pack(fill="x", side="top", py=(10,10))

        self.bottom_frame = cFr(body, bg=PANEL_BG)
        self.bottom_frame._pack(fill="both", Exp=True, side="top", py=(10,10))

    # ------------ 更新ボタン ------------
    def _on_refresh(self):

        self._load_data()
        self._render()

    #====================== DB 読み込み ========================
    def _load_data(self):

        c = sqlite3.connect(DB)
        c.row_factory = sqlite3.Row

        sql = """
            SELECT re.race_no, re.frame_no, re.course, re.finish_rank,
                   re.fault_code, re.win_move, p.name AS player_name
              FROM Race_entries re
              JOIN Players     p ON p.player_id = re.player_id
             WHERE re.date     = ?
               AND re.venue_id = ?
             ORDER BY re.race_no, (re.finish_rank IS NULL), re.finish_rank, re.frame_no
             """
        rows = c.execute(sql, (self.date, self.venue_id)).fetchall()
        c.close()

        race_rows       = {}
        course_rank_cnt = {}
        finished        = set()

        for r in rows:
            race_rows.setdefault(r["race_no"], []).append(dict(r))
            finished.add(r["race_no"])

            if r["fault_code"] == "N" and r["finish_rank"] is not None and r["course"]:
                key = (r["course"], r["finish_rank"])
                course_rank_cnt[key] = course_rank_cnt.get(key, 0) + 1

        self.race_rows       = race_rows
        self.course_rank_cnt = course_rank_cnt
        self.finished_races  = len(finished)

    #====================== 描画 ========================
    def _render(self):

        d     = dt.fromisoformat(self.date).strftime("%Y 年 %#m 月 %#d 日")
        venue = VENUES[self.venue_id] if 0 <= self.venue_id < len(VENUES) else ""
        self.lbl_title.config(text=f" {d}    {venue}   レース結果 ")

        for w in self.top_frame.winfo_children():    w.destroy()
        for w in self.bottom_frame.winfo_children(): w.destroy()

        self._render_race_table(self.top_frame)
        self._render_course_summary(self.bottom_frame)

    # ---------------- 上部: 着順テーブル ----------------
    def _render_race_table(self, parent):

        tbl = cFr(parent, bg=PANEL_BG) ;tbl._pack(side="top")

        tbl.grid_columnconfigure(0, minsize=LBL_W)
        for c in range(1, 7):
            tbl.grid_columnconfigure(c, minsize=BOAT_W)
        tbl.grid_columnconfigure(7, minsize=MOVE_W)

        for rno in range(1, 13):
            grow = rno - 1
            tbl.grid_rowconfigure(grow, minsize=ROW_H)
            self._render_race_row(tbl, grow, rno, self.race_rows.get(rno, []))

    # ---------------------------------
    def _render_race_row(self, tbl, grid_row, race_no, row):

        cLbl( tbl, text=f"{race_no:2} R", font=(MUI,9,BD), bg=PANEL_BG, Anc="e"
             )._grid(R=grid_row, C=0, px=(0, 20), Stk=ALL)

        for i in range(6):
            entry = row[i] if i < len(row) else None
            self._render_boat_cell(tbl, grid_row, i + 1, entry)

        win_move = next( (e["win_move"] for e in row
                          if e.get("finish_rank") == 1 and e.get("win_move")), "" )

        cLbl( tbl, text=win_move, font=(MUI,9), bg=PANEL_BG, Anc=CT
             )._grid(R=grid_row, C=7, px=(10,0), Stk=ALL)

    # ---------------------------------
    def _render_boat_cell(self, tbl, grid_row, grid_col, entry):

        cell = cFr(tbl, bg=PANEL_BG)
        cell._grid(R=grid_row, C=grid_col, Stk=ALL, px=0, py=10)

        if entry is None:
            return

        frame_no = entry["frame_no"]
        course   = entry["course"]
        bg       = FRM_BG.get(frame_no, "#CCCCCC")
        fg       = FRM_FG.get(frame_no, "#000000")

        cLbl( cell, text=str(course), bg=bg, fg=fg, font=(MUI,10,BD), W=3, Anc=CT, Bd=(1,RA)
             )._pack(side="left", fill="y")

        is_fault = entry["fault_code"] != "N"
        name_bg  = ABSENT_BG if is_fault else NAME_BG

        name_fr = cFr(cell, bg=name_bg)
        name_fr._pack(side="left", fill="both", px=(5,5), Exp=True)

        cLbl( name_fr, text=entry["player_name"], bg=name_bg, font=(MUI,8), Anc="w"
             )._pack(side="left", Exp=True, fill="both", px=(20,0))

        if is_fault:
            cLbl( name_fr, text=entry["fault_code"], bg=name_bg, fg=FAULT_FG, font=(MUI,10,BD)
                 )._pack(side="right", px=(0,4))

    # ---------------- 下部: コース別着順分布 ----------------
    def _render_course_summary(self, parent):

        grid_fr = cFr(parent, bg=PANEL_BG, Bd=(1,SD)) ;grid_fr._pack(side="top")

        grid_fr.Cconf(0, Min=SUM_LBL_W)

        for c in range(1, 7):
            grid_fr.Cconf(c, Min=SUM_COL_W)

        grid_fr.Rconf(0, Min=30)

        cLbl(grid_fr, text="", bg=TBL_HDR_BG, Bd=(1,RA))._grid(R=0, C=0, Stk=ALL)
        for course in range(1, 7):
            cLbl( grid_fr, text=f"{course} コース", bg=TBL_HDR_BG, fg=TBL_HDR_FG,
                       font=(MUI,9,BD), Anc=CT, Bd=(1,RD) )._grid(R=0, C=course, Stk=ALL)

        n_races = self.finished_races

        for rank in range(1, 7):
            grid_fr.Rconf(rank, Min=SUM_ROW_H)

            cLbl( grid_fr, text=f"{rank} 着", bg=TBL_HDR_BG, fg=TBL_HDR_FG, font=(MUI,9),
                            Anc=CT, Bd=(1,RD) )._grid(R=rank, C=0, Stk=ALL)

            for course in range(1, 7):
                cnt = self.course_rank_cnt.get((course, rank), 0)
                pct = (cnt / n_races * 100.0) if n_races else 0.0
                self._render_pct_cell(grid_fr, rank, course, pct)

    # ---------------------------------
    def _render_pct_cell(self, parent, grid_row, grid_col, pct):

        cell = cFr(parent, bg="#FFFFFF", Bd=(1,GR))
        cell._grid(R=grid_row, C=grid_col, Stk=ALL)

        bar_track = cFr(cell, bg=BAR_TRACK, W=BAR_TRACK_W, H=BAR_H)
        bar_track._pack(py=(14,4))
        bar_track.pack_propagate(False)

        bar_w = int(BAR_TRACK_W * max(0.0, min(100.0, pct)) / 100.0)
        if bar_w > 0:
            cFr(bar_track, bg=BAR_COLOR, W=bar_w, H=BAR_H)._pack(side="left", fill="y")

        txt = f"{pct:.0f} %" if pct else "" 
        cLbl(cell, text=txt , bg="#FFFFFF", font=(MUI,9))._pack(py=(0,6))

#=================== エントリポイント ======================
def main():

    parser = argparse.ArgumentParser(description="ボートレース 結果ウィンドウ")
    parser.add_argument("--date",  required=True,           help="YYYY-MM-DD")
    parser.add_argument("--venue", required=True, type=int, help="会場ID 1-24")
    args = parser.parse_args()

    app = ResultsWindow(date=args.date, venue_id=args.venue)
    app.mainloop()

#===========================================================
if __name__ == "__main__":
    main()