# -*- coding: utf-8 -*-
# C:\boatrace\UI\Screens\Race_select_screen.py

import tkinter  as tk
import datetime as dt
import sqlite3, subprocess, sys
from tkinter             import ttk, messagebox
from typing              import Dict, Optional
from datetime            import datetime as dt, date, timedelta, timezone

from Helpers.Custum_func import cFr, cLbl, cBtn
from Helpers.series_idx  import build_day_lbl
from Widgets.widgets     import framing_held_type_icon  

VENUES = [ "桐生","戸田",  "江戸川","平和島","多摩川","浜名湖","蒲郡","常滑", "津",
           "三国","びわこ","住之江","尼崎",  "鳴門",  "丸亀",  "児島","宮島", "徳山",
           "下関","若松",  "芦屋",  "福岡",  "唐津",  "大村",                         ]
VENUE_ID = { name:i+1 for i, name in enumerate(VENUES) }

GRADE_IDX     = { 0:"一般", 1:"G3", 2:"G2", 3:"G1", 4:"PG1", 5:"SG" }
HELD_TYPE_IDX = { 0:"通常", 1:"ﾓｰﾆﾝｸﾞ" ,2:"ｻﾏｰﾀｲﾑ", 3:"ﾅｲﾀｰ", 4:"ﾐｯﾄﾞﾅｲﾄ" }

GUI, MUI           = "Yu Gothic UI", "Meiryo UI"
GR, SD, RD, RA, BD = "groove", "solid", "ridge", "raised", "bold"
ALL, CT            = "nsew", "center"
SCOL               = "#a5e6ff"
MAIN_BG            = "#F0F4FA"
#MAIN_BG            = "SystemButtonFace"

GRADE_OPT    = [ {"font":(MUI, 10    ), "bg":"white", "fg":"black" },
                 {"font":(MUI, 10    ), "bg":"white", "fg":"black" },
                 {"font":(MUI, 10, BD), "bg":"#d2ffd1", "fg":"#ff3939" },
                 {"font":(MUI, 10, BD), "bg":"#d2ffd1", "fg":"#ff3939" },
                 {"font":(MUI, 10, BD), "bg":"#d2ffd1", "fg":"#ff3939" },
                 {"font":(MUI, 10, BD), "bg":"#72c5ff", "fg":"#ff3939" }         ]

# --------
def jst_today() -> date:
    JST = timezone(timedelta(hours=9))
    return dt.now(JST).date()
# --------
def today_iso() -> str:
    return jst_today().strftime("%Y-%m-%d")

# ======================== レース選択画面 ============================
# --------------------------------------------------------------------
class RaceSelectScreen(tk.Frame):

    def __init__(self, parent, app, db_path):
        super().__init__(parent)

        self.app       = app
        self.db_path   = db_path
        self.date      = today_iso()
        self.range_var = tk.StringVar(value="270")
        self.ow        = True
        self._cells:dict[int, dict[str, tk.Widget]] = {}

        fr_root = cFr(self,    W=740, H=600, px=40, py=30)

        fr_hedr = cFr(fr_root, W=660, H= 50)
        fr_ctrl = cFr(fr_root, W=660, H= 50)
        fr_wrap = cFr(fr_root, W=660, H=440)
        fr_botn = cFr(fr_hedr, W=120, H= 50)
        fr_titl = cFr(fr_hedr, W=320, H= 50)
        fr_rnge = cFr(fr_hedr, W=220, H= 50)

        fr_root._grid(R=0, C=0) ; fr_root.Pgate()

        fr_hedr._grid(R=0, C=0) ; fr_hedr.Pgate()
        fr_ctrl._grid(R=1, C=0) ; fr_ctrl.Pgate()
        fr_wrap._grid(R=2, C=0) ; fr_wrap.Pgate()
        fr_botn._grid(R=0, C=0) ; fr_botn.Pgate()
        fr_titl._grid(R=0, C=1) ; fr_titl.Pgate()
        fr_rnge._grid(R=0, C=2) ; fr_rnge.Pgate()

        fr_botn.Cconf(0, W=1) ; fr_botn.Rconf(0, W=1)
        fr_titl.Cconf(1, W=1) ; fr_titl.Rconf(0, W=1)
        fr_rnge.Cconf(0, W=1) ; fr_rnge.Rconf(0, W=1)
        fr_rnge.Cconf(1, W=1)
        fr_rnge.Cconf(2, W=1)
        fr_ctrl.Cconf(0, W=1) ; fr_ctrl.Rconf(0, W=1)
        fr_ctrl.Cconf(1, W=1)
        fr_ctrl.Cconf(2, W=1)
        fr_ctrl.Cconf(3, W=1)

        btn_main = ttk.Button( fr_hedr, text="メイン 画面", width=10, style="r.TButton",
                                               command=lambda: self.app.show_screen("Main") )
        btn_main.grid(row=0, column=0, ipady=5, sticky="w")

        cLbl( fr_hedr, W=33, anc=CT, text="表示レース  選 択", font=(GUI,11,BD)
             )._grid(R=0, C=1, Stk="w", padx=(20,0))

        # Controls row
        cLbl(fr_rnge, text="データ算出期間", font=(MUI,10), width=10)._grid(R=0, C=0)
        cLbl(fr_rnge, text="日",             font=(MUI,10), width= 1)._grid(R=0, C=2)

        self.ent_range = ttk.Entry(fr_rnge, width=8, textvariable=self.range_var, justify="right")
        self.btn_prev = ttk.Button(fr_ctrl, text="＜", width=3, command=lambda:self._shift_date(-1))
        self.btn_next = ttk.Button(fr_ctrl, text="＞", width=3, command=lambda:self._shift_date( 1))
        self.btn_odds = cBtn( fr_ctrl, text="オッズ ON", width=10, bg="#fbffcb", relief="ridge",
                                                                 command=lambda:self._odds_on() )
        self.lbl_date = cLbl(fr_ctrl, text=self._date_title(), font=(MUI,11), bg=MAIN_BG)

        self.ent_range.grid(row=0, column=1)
        self.btn_prev.grid( row=0, column=0, padx=(140,0))
        self.lbl_date.grid( row=0, column=1)
        self.btn_next.grid( row=0, column=2)
        self.btn_odds.grid( row=0, column=3, padx=(100,0))

        # Grid area
        self.fr_grid = cFr(fr_wrap, W=660, H=440)
        self.fr_grid._grid(R=0, C=0, Stk=ALL)
        self.fr_grid.Pgate()

        for r in range(4):
            self.fr_grid.Rconf(r, weight=1)
        for c in range(6):
            self.fr_grid.Cconf(c, weight=1)

        self._render_for_date()

    #---------------------------------------------
    def _odds_on(self):

        if self.ow == True:
            self.ow = False
            self.btn_odds.config(text="オッズ OFF", bg="white", relief="raised")
        else:
            self.ow = True
            self.btn_odds.config(text="オッズ ON", bg="#fbffcb", relief="ridge",)

    # ---------- public hooks ----------
    def on_show(self):
        self._render_for_date()
    # ----------------------------------
    def reload_today(self):
        self.date = today_iso()
        self._render_for_date()
    # ------- internal helpers ---------
    def _date_title(self) -> str:
        d = dt.strptime(self.date, "%Y-%m-%d").date()
        return f"{d.month} 月 {d.day} 日     開催一覧"
    # ----------------------------------
    def _shift_date(self, diff_days:int):
        try:
            d = dt.strptime(self.date, "%Y-%m-%d").date()
            d = d + timedelta(days=diff_days)
            self.date = d.strftime("%Y-%m-%d")
        except Exception:
            self.date = today_iso()
        self._render_for_date()
    # --------------------------------------------
    def _render_for_date(self):
 
        self.lbl_date.configure(text=self._date_title())
        dayinfo = self._load_day_info(self.date)
 
        for idx, vname in enumerate(VENUES):
            vid = idx + 1
            info = dayinfo.get(vid, None)
            self._render_cell(idx//6, idx%6, vid, vname, info)

    # --------------------------------------------
    def _render_cell(self, row:int, col:int, venue_id:int, venue_name:str, info:dict|None):

        v_opt = {"text":venue_name, "font":(GUI,10,BD), "bg":"#d3dee9"}
        widg  = self._cells.get(venue_id)

        if widg is None:
            self.fr_cel = cFr(self.fr_grid, W=110, H=110, bd=1, Rel=SD, bg=MAIN_BG)
            self.fr_cel._grid(R=row, C=col, Stk=ALL) ;self.fr_cel.Pgate()
            self.fr_cel.Rconf(0, W=1) ; self.fr_cel.Cconf(0, W=1)
            self.fr_cel.Rconf(1, W=1) ; self.fr_cel.Cconf(1, W=1)
            self.fr_cel.Rconf(2, W=1)

            lb_ven = cLbl(self.fr_cel, anc=CT, **v_opt, bd=1, Rel=RD)
            lb_upL = cLbl(self.fr_cel, anc="e", text="", font=(MUI,11), bg=MAIN_BG)
            lb_upR = cLbl(self.fr_cel, anc=CT,  text="")
            lb_dwn = cLbl(self.fr_cel, anc=CT,  text="")

            lb_ven._grid(R=0, C=0, Cspan=2, Stk=ALL)
            lb_upL._grid(R=1, C=0,          Stk="we")
            lb_upR._grid(R=1, C=1,          Stk="we")
            lb_dwn._grid(R=2, C=0, Cspan=2, Stk=ALL)

            widg = self._cells[venue_id] = dict( cel=self.fr_cel, ven=lb_ven, upL=lb_upL,
                                                 upR=lb_upR, dwn=lb_dwn,
                                                 clicks=( self.fr_cel, lb_ven, lb_upL,
                                                                  lb_upR, lb_dwn )   )
        else:
            (cel, lb_ven, lb_upL, lb_upR, lbl_dwn) = ( widg["cel"], widg["ven"],
                                                       widg["upL"], widg["upL"], widg["dwn"] )
            cel._grid(R=row, C=col, Stk=ALL)

        if info is None:
            widg["upL"].configure(text="", bg=MAIN_BG, fg="black")
            widg["upR"].configure(text="", bg=MAIN_BG, fg="black")
            widg["dwn"].configure(text="", bg=MAIN_BG, fg="black")
            self._apply_click_binding(widg, venue_id, enabled=False)
            framing_held_type_icon(self, widg["upR"], 0)
        else:
            self.fr_cel.config(bg="white")
            grade   = GRADE_IDX.get(info.get("grade") or 0, "一般")
            day_lbl = self._calc_day_label(self.date, venue_id)
            g_opt   = GRADE_OPT[info.get("grade") or 0]
            h_type  = info.get("held_type", 0)

            widg["upL"].configure(text=f"{grade}", **g_opt)
            widg["upR"].configure(text=f"", **g_opt)
            widg["dwn"].configure(text=day_lbl or "ー", bg="white")
            framing_held_type_icon(self, widg["upR"], h_type)         
            self._apply_click_binding(widg, venue_id, enabled=True)

    # --------------------------------------------
    def _apply_click_binding(self, cell:dict, venue_id:int, enabled:bool):

        widgets = cell["clicks"]

        if enabled:
            for w in widgets:
                w.configure(cursor="hand2")
                w.bind("<Button-1>", lambda e, v=venue_id: self._open_race_window(v, self.ow))
        else:
            for w in widgets:
                w.configure(cursor="")
                w.unbind("<Button-1>")
    # --------------------------------------------
    def _open_race_window(self, venue_id:int, odds_window:bool):

        try:
            range_d = int(self.range_var.get().strip())
        except Exception:
            range_d = 200
        self.app.open_race_window(self.date, venue_id, range_d, odds_window)

    # ----------------- DB access -----------------
    def _load_day_info(self, d_iso:str):

        out:dict[int, dict] = {}
        conn                = sqlite3.connect(self.db_path, timeout=30)

        try:
            conn.row_factory = sqlite3.Row
            cur              = conn.cursor()
            rows = cur.execute(
                """
                SELECT venue_id,
                       MIN(grade)     AS grade,
                       MIN(held_type) AS held_type
                  FROM Race_programs
                 WHERE date = ?
              GROUP BY venue_id
                """,
                      (d_iso,)).fetchall()

            for r in rows:
                vid      = int(r["venue_id"])
                out[vid] = dict(grade=r["grade"], held_type=r["held_type"])

            return out
        finally: conn.close()

    # --------------------------------------------
    def _calc_day_label(self, d_iso:str, venue_id:int):

        labels, _ = build_day_lbl(d_iso, venue_id)

        for items in labels:
            if items["date"] == d_iso:
                if   items.get("is_final"): return "最終日"
                day_no = items.get("label_no")
                if day_no == 1:             return "初日"
                return f"{day_no}日目"

        return "ー"
