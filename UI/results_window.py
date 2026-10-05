# -*- coding: utf-8 -*-
# C:\boatrace\UI\results_window.py

import argparse, threading, sys, sqlite3, json
import tkinter as tk

from datetime                 import date, datetime as dt
from Custum_func              import cFr, cLbl, cBtn
from Helpers.build_series_idx import build_day_lbl

#-----------------------------------------------------------
DB = r"C:\boatrace\boatrace.db"

GUI, MUI, HNH      = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy"
GR, SD, RD, RA, BD = "groove", "solid", "ridge", "raised", "bold"
ALL, CT            = "nsew", "center"

VENUES = [ "", "桐生", "戸田", "江戸川", "平和島", "多摩川", "浜名湖",  "蒲郡", "常滑",
                 "津", "三国", "びわこ", "住之江",   "尼崎",   "鳴門",  "丸亀", "児島",
               "宮島", "徳山",   "下関",   "若松",   "芦屋",   "福岡",  "唐津", "大村", ]

MAIN_HDR_BG = "#2B4A7A"
MAIN_HDR_FG = "#FFFFFF"

HDR_COLOR   = {"bg":"#2F75B5", "fg":"#FFFFFF"}
PAY_ROW_BG  = ["#FFFFFF", "#F4F8FF"]
PAY_AMT_FG  = "#D40000"
PAY_AMT_FG2 = "#000000"

FRM_BG      = {1:"#FFFFFF", 2:"#333333", 3:"#D40000", 4:"#0066CC", 5:"#FFD400", 6:"#008A2E"}
FRM_FG      = {1:"#000000", 2:"#FFFFFF", 3:"#FFFFFF", 4:"#FFFFFF", 5:"#000000", 6:"#FFFFFF"}
MAIN_BG     = "#F0F4FA"
FAULT_FG    = "#D40000"
ABSENT_BG   = "#CCCCCC"
NAME_BG     = "#FFFFFF"
PANEL_BG    = "#F0F4FA"

BAR_COLOR   = "#0069D5"
BAR_TRACK   = "#FFFFFF"

PAY_HDR_H   = 25   # 払戻一覧 ヘッダー  高さ
PAY_ROW_H   = 32   # 払戻一覧 セル      高さ
PAY_LBL_W   = 55   # 払戻一覧 レースno, 幅
PAY_3T_W    = 173  # 払戻一覧 3連単     幅
PAY_3F_W    = 173  # 払戻一覧 3連複     幅
PAY_2T_W    = 173  # 払戻一覧 2連単     幅
PAY_KK_W    = 173  # 払戻一覧 拡連複    幅

RES_ROW_H   = 45   # 結果一覧 セル高さ
RES_BOAT_W  = 160  # 結果一覧 セル幅
RES_LBL_W   = 50   # 結果一覧 レースno, 幅
RES_MOVE_W  = 60   # 結果一覧 決まり手  幅

SUM_HDR_H   = 25   # 着位分布 ヘッダー   高さ
SUM_LBL_W   = 55   # 着位分布 縦軸ラベル 幅
SUM_COL_W   = 172  # 着位分布 セル       幅
SUM_ROW_H   = 30   # 着位分布 セル       高さ
BAR_TRACK_W = 165  # 着位分布 棒グラフ   幅
BAR_H       = 10   # 着位分布 棒グラフ   高さ

# ------------------
def to_str(x:date) -> str:

   if isinstance(x,  str): return x
   if isinstance(x, date): return x.strftime("%Y-%m-%d")
# ------------------
def to_date(x:str) -> date:

    if isinstance(x, date): return x
    if isinstance(x,  str): return dt.strptime(x, "%Y-%m-%d").date()
# ----------------------------
def wid_txt(s:str) -> str:

    hair = "\u200A" 
    return hair.join(list(s))
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
        self.payout_rows      = {}

        self._build_ui()
        self._load_data()
        self._render()

        th = threading.Thread(target=self._read_stdin_loop, daemon=True)
        th.start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # --------------- ウィンドウ終了処理 -------------------
    def _on_close(self):

        try: self.destroy()
        except Exception: pass

    # ------------- 標準入力待受スレッドループ -------------
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

    # ----------------- 受信コマンド処理 -------------------
    def _handle_command(self, d:dict):

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
        changed   = (new_date != self.date or int(new_venue) != self.venue_id)

        if changed:
            self.date     = new_date
            self.venue_id = int(new_venue)
            self._on_refresh()

    # --------------------- UI 構築 ------------------------
    def _build_ui(self):

        hdr = cFr(self, bg=MAIN_HDR_BG, H=35) ;hdr._pack(fill="x", side="top")

        self.lbl_title = cLbl(hdr, text="", bg=MAIN_HDR_BG, fg=MAIN_HDR_FG, font=(MUI,9,BD))
        self.lbl_title._pack(side="left", px=10, py=2)

        cBtn( hdr, text=" 更   新 ", Com=self._on_refresh, bg="#4A7ACC", fg="white",
                  font=(GUI,9,BD), Rel=RA, px=8 )._pack(side="right", px=10, py=4)

        self.btn_fr = cFr(hdr, bg=MAIN_HDR_BG, H=35) ;self.btn_fr._pack(side="left", px=30)
        self._mk_day_buttons(self.btn_fr)

        body = cFr(self, bg=PANEL_BG) ;body._pack(fill="both", expand=True)

        self.payout_frame = cFr(body, bg=PANEL_BG)
        self.top_frame    = cFr(body, bg=PANEL_BG)
        self.bottom_frame = cFr(body, bg=PANEL_BG)

        self.payout_frame._pack(fill="x",              side="top", px=10, py=(8,5))
        self.top_frame._pack(   fill="x",              side="top",        py=(0,0))
        self.bottom_frame._pack(fill="both", Exp=True, side="top",        py=(5,8))

    # ------------------------------------------------------
    def _on_refresh(self):

        self._load_data()
        self._render()

    # ------------------ DB 読み込み -----------------------
    def _load_data(self):

        c = sqlite3.connect(DB)
        c.row_factory = sqlite3.Row

        sql = """
            SELECT re.race_no,
                   re.frame_no,
                   re.course,
                   re.finish_rank AS f_rank,
                   re.fault_code,
                   re.win_move,
                   p.name         AS player_name
              FROM Race_entries re JOIN Players p 
                ON p.player_id = re.player_id
             WHERE re.date     = ?
               AND re.venue_id = ?
          ORDER BY re.race_no, (re.finish_rank IS NULL), re.finish_rank, re.frame_no
             """

        rows = c.execute(sql, (self.date, self.venue_id)).fetchall()

        psql = """
            SELECT r.race_no,
                   py.combo_3T,  py.combo_3F,  py.combo_2T,
                   py.combo_KK1, py.combo_KK2, py.combo_KK3,
                   py.payout_3T, py.payout_3F, py.payout_2T,
                   py.payout_KK1,py.payout_KK2,py.payout_KK3
              FROM Payouts py JOIN Races r
                ON r.race_id = py.race_id
             WHERE py.date     = ?
               AND py.venue_id = ?
               AND py.status   = 'normal'
          ORDER BY r.race_no
             """

        prows = c.execute(psql, (self.date, self.venue_id)).fetchall()
        c.close()

        race_rows       = {}
        course_rank_cnt = {}
        finished        = set()
        payout_rows     = {}

        for r in rows:
            race_rows.setdefault(r["race_no"], []).append(dict(r))
            finished.add(r["race_no"])

            if r["fault_code"] == "N" and r["f_rank"] is not None and r["course"]:
                key = (r["course"], r["f_rank"])
                course_rank_cnt[key] = course_rank_cnt.get(key, 0) + 1

        for p in prows:
            payout_rows[p["race_no"]] = dict(p)

        self.race_rows       = race_rows
        self.course_rank_cnt = course_rank_cnt
        self.finished_races  = len(finished)
        self.payout_rows     = payout_rows

    # ---------------------- 描画 --------------------------
    def _render(self):

        d     = to_date(self.date).strftime("%Y 年 %#m 月 %#d 日")
        venue = VENUES[self.venue_id] if 0 <= self.venue_id < len(VENUES) else ""

        self.lbl_title.config(text=f" {d}    {venue}   レース結果一覧 ")

        for w in self.payout_frame.winfo_children():  w.destroy()
        for w in self.top_frame.winfo_children():     w.destroy()
        for w in self.bottom_frame.winfo_children():  w.destroy()

        self._update_day_btn_style()
        self._render_payout_table(self.payout_frame)
        self._render_race_table(self.top_frame)
        self._render_course_summary(self.bottom_frame)

    # ---------------- 払い戻し一覧テーブル ----------------
    def _render_payout_table(self, parent):

        bet_cols = [ ("3 連単",  "combo_3T",  "payout_3T",  PAY_3T_W),
                     ("3 連複",  "combo_3F",  "payout_3F",  PAY_3F_W),
                     ("2 連単",  "combo_2T",  "payout_2T",  PAY_2T_W),
                     ("拡 連複", "combo_KK1", "payout_KK1", PAY_KK_W),
                     ("",        "combo_KK2", "payout_KK2", PAY_KK_W),
                     ("",        "combo_KK3", "payout_KK3", PAY_KK_W), ]

        tbl = cFr(parent, bg=PANEL_BG, Bd=(1,SD)) ;tbl._pack(side="top")

        tbl.Rconf(0, minsize=PAY_HDR_H)
        tbl.Cconf(0, minsize=PAY_LBL_W)

        for col, (_, _, _, w) in enumerate(bet_cols):
            tbl.Cconf(col + 1, minsize=w)

        cLbl(tbl, text="", **HDR_COLOR, Bd=(1,RD))._grid(R=0, C=0, Stk=ALL)

        span = {}

        for col, (label, _, _, w) in enumerate(bet_cols):
            if col  > 3:  break
            if col == 3: span = dict(Cspan=3)

            cLbl( tbl, text=label, font=(MUI,9), Anc=CT, Bd=(1,RD), **HDR_COLOR,
                 )._grid(R=0, C=col +1, **span, Stk=ALL)

        for row in range(1, 13):

            tbl.Rconf(row, minsize=PAY_ROW_H)

            row_bg = PAY_ROW_BG[(row) % 2]
            pd     = self.payout_rows.get(row)

            cLbl( tbl, text=f"{row} R    ", font=(MUI,8,BD) , Anc="e", Bd=(1,RD), **HDR_COLOR
                 )._grid(R=row, C=0, Stk=ALL)

            for col, (_, ck, pk, _) in enumerate(bet_cols):

                combo      = pd[ck] if pd and pd.get(ck) not in (None, 0, 9) else None
                payout     = pd[pk] if pd and pd.get(pk) is not  None        else None
                combo_txt  = self._fmt_combo(ck, combo) if combo  else ""
                payout_txt = f"{payout:,} 円"           if payout else ""
                amt_fg     = PAY_AMT_FG if payout and payout >= 10000 else PAY_AMT_FG2
                px1        = 15 if col <= 1 else 30
                px2        = 10 if col <= 2 else 23

                cell = cFr(tbl, bg=row_bg, Bd=(1,GR)) ;cell._grid(R=row, C=col +1, Stk=ALL)

                cLbl(cell, text=combo_txt,  bg=row_bg, font=(GUI,10,BD), Anc="w"
                     )._pack(side="left",  px=(px1,0))
                cLbl(cell, text=payout_txt, bg=row_bg, font=(MUI,9,BD), Anc="e", fg=amt_fg
                     )._pack(side="right", px=(0,px2))

    #-------------------------------------------------------
    @staticmethod
    def _fmt_combo(combo_key:str, combo:int) -> str:

        s = str(combo)
        if combo_key.startswith("combo_3"):
            return f"{s[0]} - {s[1]} - {s[2]}" if len(s) >= 3 else s
        elif combo_key.startswith("combo_2") or combo_key.startswith("combo_KK"):
            return f"{s[0]} - {s[1]}" if len(s) >= 2 else s

        return s

    # -------------------- 着順テーブル --------------------
    def _render_race_table(self, parent):

        tbl = cFr(parent, bg=PANEL_BG) ;tbl._pack(side="top")

        tbl.Cconf(0, minsize=RES_LBL_W)
        tbl.Cconf(7, minsize=RES_MOVE_W)
        for col in range(1, 7):
            tbl.Cconf(col, minsize=RES_BOAT_W)
        for row in range(12):
            tbl.Rconf(row, minsize=RES_ROW_H)
            self._render_race_row(tbl, row, row+1, self.race_rows.get(row+1, []))

    # ------------------------------------------------------
    def _render_race_row(self, tbl, row, r_no, data):

        cLbl( tbl, text=f"{r_no:2} R", font=(MUI,9,BD), bg=PANEL_BG, Anc="e"
             )._grid(R=row, C=0, px=(0,20), Stk=ALL)

        for i in range(6):
            entry = data[i] if i < len(data) else None
            self._render_boat_cell(tbl, row, i +1, entry)

        w_m = next((e["win_move"] for e in data if e.get("f_rank") == 1 and e.get("win_move")), "" )

        cLbl( tbl, text=wid_txt(w_m), font=(MUI,9), bg=PANEL_BG, Anc=CT
             )._grid(R=row, C=7, px=(10,0), Stk=ALL)

    # ------------------------------------------------------
    def _render_boat_cell(self, tbl, row, col, entry):

        cell = cFr(tbl, bg=PANEL_BG) ;cell._grid(R=row, C=col, Stk=ALL, px=0, py=7)

        if entry is None:
            return

        frame_no = entry["frame_no"]
        course   = entry["course"]
        bg       = FRM_BG.get(frame_no, "#CCCCCC")
        fg       = FRM_FG.get(frame_no, "#000000")

        cLbl( cell, text=str(course), bg=bg, fg=fg, font=(MUI,10,BD), W=3, Anc=CT, Bd=(1,RA)
             )._pack(side="left", fill="y")

        is_fault = entry["fault_code"] != "N"
        name_bg  = ABSENT_BG if is_fault else MAIN_BG

        fr = cFr(cell, bg=name_bg) ;fr._pack(side="left", fill="both", px=(5,5), Exp=True)

        cLbl( fr, text=entry["player_name"], bg=name_bg, font=(MUI,8), Anc="w"
             )._pack(side="left", Exp=True, fill="both", px=(20,0))

        if is_fault:
            cLbl( fr, text=entry["fault_code"], bg=name_bg, fg=FAULT_FG, font=(MUI,10,BD)
                 )._pack(side="right", px=(0,4))

    # ----------------- コース別着順分布 -------------------
    def _render_course_summary(self, parent):

        fr1 = cFr(parent, bg=PANEL_BG, Bd=(1,SD)) ;fr1._pack(side="top", pady=(0,0))
        fr2 = cFr(parent, bg=PANEL_BG, Bd=(1,SD)) ;fr2._pack(side="top", pady=(0,0))

        fr1.Cconf(0, Min=SUM_LBL_W) ;fr1.Rconf(0, Min=SUM_HDR_H)
        fr2.Cconf(0, Min=SUM_LBL_W)
        for col in range(1, 7):
            fr1.Cconf(col, Min=SUM_COL_W)
            fr2.Cconf(col, Min=SUM_COL_W)

        n_races = self.finished_races
        rate3 = {1:0.0, 2:0.0, 3:0.0, 4:0.0, 5:0.0, 6:0.0}

        for rank in range(1, 7):
            if rank <= 3: fr1.Rconf(rank,   Min=SUM_ROW_H)
            else:         fr2.Rconf(rank-4, Min=SUM_ROW_H)
            frame = fr1  if rank <= 3 else fr2
            row   = rank if rank <= 3 else rank-4

            cLbl( frame, text=f"{rank} 着", **HDR_COLOR, font=(MUI,9), Anc=CT, Bd=(1,RD)
                 )._grid(R=row, C=0, Stk=ALL)

            for course in range(1, 7):
                cnt = self.course_rank_cnt.get((course, rank), 0)
                pct = (cnt / n_races * 100.0) if n_races else 0.0
                self._render_pct_cell(frame, row, course, pct)

                if rank <= 3: rate3[course] += pct

        cLbl(fr1, text="", **HDR_COLOR, Bd=(1,RA))._grid(R=0, C=0, Stk=ALL)
        for course in range(1, 7):
            r = rate3[course]
            cLbl( fr1, text=f"{course} コース     {r:.0f} % ", **HDR_COLOR, font=(MUI,9,BD), Anc=CT, Bd=(1,RD)
                 )._grid(R=0, C=course, Stk=ALL)

    # ------------------------------------------------------
    def _render_pct_cell(self, parent, row, col, pct):

        cell = cFr(parent, bg="#FFFFFF", Bd=(1,GR)) ;cell._grid(R=row, C=col, Stk=ALL)

        bar_track = cFr(cell, bg=BAR_TRACK, W=BAR_TRACK_W, H=BAR_H)
        bar_track._pack(py=(14,4)) ;bar_track.pack_propagate(False)

        bar_w = int(BAR_TRACK_W * max(0.0, min(100.0, pct)) / 100.0)
        if bar_w > 0:
            cFr(bar_track, bg=BAR_COLOR, W=bar_w, H=BAR_H)._pack(side="left", fill="y")

            txt = f"{pct:.0f} %" if pct else "" 
            cLbl(cell, text=txt , bg="#FFFFFF", font=(MUI,9))._pack(py=(0,6))

    #------------------- 日程切替 ボタン -------------------
    def _mk_day_buttons(self, parent:tk.Frame):

        for child in parent.winfo_children(): child.destroy()

        self._day_btns = {}
        labels, _ = build_day_lbl(to_date(self.date), self.venue_id)

        for col, info in enumerate(labels):
            if not info["visible"]: continue

            dn   = info["label_no"]
            d    = to_date(info["date"])
            txt  = "初 日"  if dn == 1           else f"{dn}日目"
            txt  = "最終日" if info["final_day"] else txt

            btn  = cBtn(parent, text=txt, width=7, Com=lambda d=d:self._switch_day(d) )
            btn._grid(R=0, C=col, px=2)

            self._day_btns[d] = btn

            if col >= 9: break

        self._update_day_btn_style()

    #-------------------------------------------------------
    def _switch_day(self, d):

        self.date = d
        self._update_day_btn_style()
        self._on_refresh()

    #-------------------------------------------------------
    def _update_day_btn_style(self):

        for d, btn in self._day_btns.items():
            if d == to_date(self.date):
                btn.config(bg="#FFD700", fg="#222222", font=(MUI,8,BD), relief=GR)
            else:
                btn.config(bg="#4A6A9A", fg="#FFFFFF", font=(MUI,8,BD), relief=RA)

#=================== エントリポイント ======================
def main():

    parser = argparse.ArgumentParser(description="ボートレース 結果ウィンドウ")
    parser.add_argument("--date",   required=True,           help="YYYY-MM-DD")
    parser.add_argument("--venue",  required=True, type=int, help="会場ID 1-24")
    args = parser.parse_args()

    app = ResultsWindow(date=args.date, venue_id=args.venue)
    app.mainloop()

#===========================================================
if __name__ == "__main__":
    main()