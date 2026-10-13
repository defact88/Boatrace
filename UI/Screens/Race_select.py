# -*- coding: utf-8 -*-
# C:\boatrace\UI\Screens\Race_select_screen.py

import tkinter  as tk
import datetime as dt
import Dal      as dal
import subprocess, sys

from tkinter             import ttk, messagebox
from typing              import Dict, Optional
from datetime            import datetime as dt, date, timedelta, timezone

from Helpers.Custum_func      import cFr, cLbl, cBtn
from Helpers.build_series_idx import build_day_lbl
from Widgets.widgets          import framing_held_type_icon  

#===============================================================================

VENUES = [ "桐生", "戸田", "江戸川","平和島","多摩川","浜名湖","蒲郡","常滑", "津",
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

GRADE_OPT = [ {"font":(MUI, 10    ), "bg":"white",   "fg":"black"   },
              {"font":(MUI, 10    ), "bg":"white",   "fg":"black"   },
              {"font":(MUI, 10, BD), "bg":"#d2ffd1", "fg":"#ff3939" },
              {"font":(MUI, 10, BD), "bg":"#d2ffd1", "fg":"#ff3939" },
              {"font":(MUI, 10, BD), "bg":"#d2ffd1", "fg":"#ff3939" },
              {"font":(MUI, 10, BD), "bg":"#72c5ff", "fg":"#ff3939" }  ]

HDR_OPT   = dict(font=(GUI,10,BD), bg="#d3dee9", Bd=(1,RD))

#===============================================================================
def today_iso() -> str:

    JST = timezone(timedelta(hours=9))
    return dt.now(JST).date().strftime("%Y-%m-%d")

# ------------------
def to_str(x) -> str:

    if isinstance(x,  str): return x
    if isinstance(x, date): return x.strftime("%Y-%m-%d")

    raise ValueError("str conv error")

# ------------------
def to_date(x) -> date:

    if isinstance(x, date): return x
    if isinstance(x,  str): return date.fromisoformat(x)

    raise ValueError("date conv error")

#-----------------------------
def days_pass(d:str, range:int):

    d = to_date(d)

    return to_str(d +timedelta(days=range))

# ======================== レース選択画面 ============================
class RaceSelectScreen(tk.Frame):

    def __init__(self, parent, app, db_path):
        super().__init__(parent)

        style = ttk.Style()
        style.configure("RSS.TButton", font=(MUI,9), anchor="center")
        style.configure("RSS.TEntry", padding=(0, 3, 3, 3))

        self.app        = app
        self.db_path    = db_path
        self.date       = today_iso()
        self.range_var  = tk.StringVar(value="270")
        self.sub_window = False
        self.cells:dict[int, dict[str,tk.Widget]] = {}

        fr_root = cFr(self,    W=740, H=700, px=30)
        fr_root._grid(R=0, C=0, py=(0,0)) ;fr_root.Pgate()

        fr_hedr = cFr(fr_root, W=660, H= 50)
        fr_ctrl = cFr(fr_root, W=660, H= 50)
        fr_wrap = cFr(fr_root, W=660, H=600)

        fr_botn = cFr(fr_hedr, W=120, H= 50)
        fr_titl = cFr(fr_hedr, W=320, H= 50)
        fr_rnge = cFr(fr_hedr, W=220, H= 50)

        fr_hedr._grid(R=0, C=0) ;fr_hedr.Pgate()
        fr_ctrl._grid(R=1, C=0) ;fr_ctrl.Pgate()
        fr_wrap._grid(R=2, C=0) ;fr_wrap.Pgate()

        fr_botn._grid(R=0, C=0) ;fr_botn.Pgate()
        fr_titl._grid(R=0, C=1) ;fr_titl.Pgate()
        fr_rnge._grid(R=0, C=2) ;fr_rnge.Pgate()

        fr_botn.Cconf(0, W=1) ;fr_botn.Rconf(0, W=1)
        fr_titl.Cconf(1, W=1) ;fr_titl.Rconf(0, W=1)
        fr_rnge.Cconf(0, W=1) ;fr_rnge.Rconf(0, W=1)
        fr_rnge.Cconf(1, W=1)
        fr_rnge.Cconf(2, W=1)
        fr_ctrl.Cconf(0, W=1) ;fr_ctrl.Rconf(0, W=1)
        fr_ctrl.Cconf(1, W=1)
        fr_ctrl.Cconf(2, W=1)
        fr_ctrl.Cconf(3, W=1)

        btn_main = ttk.Button( fr_hedr, text="メイン 画面", width=10, style="RSS.TButton",
                                               command=lambda:self.app.show_screen("Main") )
        btn_main.grid(row=0, column=0, ipady=5, sticky="w")

        cLbl( fr_hedr, W=33, Anc=CT, text="Race Window 表示レース  選 択", font=(GUI,11,BD)
             )._grid(R=0, C=1, Stk="w", padx=(20,0))

        cLbl(fr_rnge, text="データ算出期間", font=(MUI,10), width=10)._grid(R=0, C=0)
        cLbl(fr_rnge, text="日",             font=(MUI,10), width= 1)._grid(R=0, C=2)

        self.ent_range = ttk.Entry( fr_rnge, width=8, textvariable=self.range_var,
                                    style="RSS.TEntry", justify="right", font=(MUI,10) )
        self.btn_prev  = cBtn(fr_ctrl, W=5, text="＜", font=(MUI,8), bg="white",
                                                          Com=lambda:self._shift_date(-1))
        self.btn_next  = cBtn(fr_ctrl, W=5, text="＞", font=(MUI,8), bg="white",
                                                          Com=lambda:self._shift_date( 1))
        self.btn_odds  = cBtn( fr_ctrl, W=8, text="SUB OFF", font=(MUI,10), bg="white", Rel=RA,
                                                          Com=lambda:self._odds_on() )

        txt = f"{to_date(self.date).month} 月 {to_date(self.date).day} 日    開催一覧"
        self.lbl_date  = cLbl(fr_ctrl, text=txt, font=(MUI,10), bg=MAIN_BG)

        self.ent_range.grid(row=0, column=1)
        self.btn_prev.grid( row=0, column=0, padx=(140,0))
        self.lbl_date.grid( row=0, column=1)
        self.btn_next.grid( row=0, column=2)
        self.btn_odds.grid( row=0, column=3, padx=(100,0))

        self.fr_grid = cFr(fr_wrap, W=660, H=440, Bd=(1,SD))
        self.fr_grid._grid(R=0, C=0, Stk=ALL) ;self.fr_grid.Pgate()

        for r in range(4):
            self.fr_grid.Rconf(r, Min=120)
        for c in range(6):
            self.fr_grid.Cconf(c, Min=110)

        self._render_for_date()

    #---------------------------------------------
    def _odds_on(self):

        if self.sub_window:
            self.btn_odds.config(text="SUB OFF", bg="white",  relief="raised")
        else:
            self.btn_odds.config(text="SUB  ON", bg="#fbffcb", relief="ridge",)

        self.sub_window = not self.sub_window

    # ---------- public hooks ----------
    def on_show(self):

        self._render_for_date()

    # ----------------------------------
    def _shift_date(self, diff_days:int):

        self.date = days_pass(self.date, diff_days)
        self._render_for_date()

    # --------------------------------------------
    def _render_for_date(self):

        txt = f"{to_date(self.date).month} 月 {to_date(self.date).day} 日    開催一覧"
        self.lbl_date.config(text=txt)
        dayinfo = self._load_day_info(self.date)
 
        for vid, vname in enumerate(VENUES, start=1):
            info = dayinfo.get(vid, None)
            self._render_cell((vid-1)//6, (vid-1)%6, vid, vname, info)

    # --------------------------------------------
    def _render_cell(self, row:int, col:int, venue_id:int, v_name:str, info:dict|None):

        widg = self.cells.get(venue_id)

        if widg is None:
            fr_cell = cFr(self.fr_grid, W=110, H=120, Bd=(1,GR), bg=MAIN_BG)
            fr_cell._grid(R=row, C=col, Stk=ALL) ;fr_cell.Pgate()

            fr_cell.Rconf(0, Min=30) ;fr_cell.Cconf(0, Min=60)
            fr_cell.Rconf(1, Min=30) ;fr_cell.Cconf(1, Min=50)
            fr_cell.Rconf(2, Min=30)
            fr_cell.Rconf(2, Min=30)

            lb_hedr = cLbl(fr_cell, Anc=CT,  text=v_name, **HDR_OPT)
            lb_topL = cLbl(fr_cell, Anc="e", text="", font=(MUI,11), bg=MAIN_BG)
            lb_topR = cLbl(fr_cell, Anc=CT,  text="")
            lb_cntr = cLbl(fr_cell, Anc=CT,  text="", font=(MUI,6))
            lb_botm = cLbl(fr_cell, Anc=CT,  text="", font=(MUI,9))

            lb_hedr._grid(R=0, C=0, Cspan=2, Stk=ALL)
            lb_topL._grid(R=1, C=0,          Stk="we")
            lb_topR._grid(R=1, C=1,          Stk="we")
            lb_cntr._grid(R=2, C=0, Cspan=2, Stk=ALL)
            lb_botm._grid(R=3, C=0, Cspan=2, Stk=ALL)

            widg = self.cells[venue_id] = {     "frm":fr_cell, "hedr":lb_hedr, "topL":lb_topL,
                                               "cntr":lb_cntr, "topR":lb_topR, "botm":lb_botm,
                                             "clicks":(lb_topL, lb_cntr, lb_topR, lb_botm)     }

        if info is None:
            widg["frm"].configure(bg=MAIN_BG)
            widg["topL"].configure(text="", bg=MAIN_BG, fg="black")
            widg["topR"].configure(text="", bg=MAIN_BG, fg="black")
            widg["cntr"].configure(text="", bg=MAIN_BG, fg="black")
            widg["botm"].configure(text="", bg=MAIN_BG, fg="black")

            framing_held_type_icon(self, widg["topR"], 0)

            self._apply_click_binding(widg, venue_id, enabled=False)

        else:
            grade   = GRADE_IDX[info["grade"] or 0]
            day_lbl = self._calc_day_label(self.date, venue_id)
            g_opt   = GRADE_OPT[info["grade"] or 0]
            h_type  = info["held_type"]
            title   = info["title"]

            widg["frm"].config(bg="white")
            widg["topL"].configure(text=f"{grade}", **g_opt)
            widg["cntr"].configure(text=f"{title}", bg="white")
            widg["botm"].configure(text=day_lbl, bg="white")

            framing_held_type_icon(self, widg["topR"], h_type)   

            self._apply_click_binding(widg, venue_id, enabled=True)

    # --------------------------------------------
    def _apply_click_binding(self, cell:dict, v_id:int, enabled:bool):

        if enabled:
            for w in cell["clicks"]:
                w.configure(cursor="hand2")
                w.bind("<Button-1>", lambda e:self._open_race_window(v_id, self.sub_window))
        else:
            for w in cell["clicks"]:
                w.configure(cursor="")
                w.unbind("<Button-1>")

    # --------------------------------------------
    def _open_race_window(self, venue_id:int, odds_window:bool):

        try:
            range_d = int(self.range_var.get().strip())
        except Exception:
            range_d = 270

        self.app.open_race_window(self.date, venue_id, range_d, odds_window)

    # ----------------- DB access -----------------
    def _load_day_info(self, d_iso:str):

        rows = dal.fetch_all(
            """
            SELECT venue_id,
                   MIN(grade)        AS grade,
                   MIN(held_type)    AS held_type,
                   MIN(series_title) AS title
              FROM Race_programs
             WHERE date = ?
          GROUP BY venue_id
            """,
            (d_iso,) )

        return {row["venue_id"]:dict(row) for row in rows} if rows else {}

    # --------------------------------------------
    def _calc_day_label(self, d_iso:str, venue_id:int):

        labels, _ = build_day_lbl(d_iso, venue_id)

        for items in labels:
            if items["date"] == d_iso:
                if items["final_day"]:   return "最終日"
                if items["day_no"] == 1: return "初日"
                else:                    return f"{items["day_no"]}日目"

        return "ー"

    # --------------------------------------------
