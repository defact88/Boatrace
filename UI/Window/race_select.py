# -*- coding: utf-8 -*-
# C:\boatrace\UI\Screens\Race_select_screen.py

import tkinter  as tk
import datetime as dt
import Dal      as dal
import subprocess, sys

from tkinter  import messagebox
from typing   import Dict, Optional
from datetime import datetime as dt, date, timedelta, timezone

from Helpers.Custum_func      import cFr, cLbl, cBtn, cEnt
from Helpers.build_series_idx import build_day_lbl
from Widgets.widgets          import framing_held_type_icon  

#===============================================================================

VENUES = [ "桐生", "戸田", "江戸川","平和島","多摩川","浜名湖","蒲郡","常滑", "津",
           "三国","びわこ","住之江","尼崎",  "鳴門",  "丸亀",  "児島","宮島", "徳山",
           "下関","若松",  "芦屋",  "福岡",  "唐津",  "大村",                         ]
VENUE_ID = { name:i+1 for i, name in enumerate(VENUES) }

GRADE_IDX     = { 0:"一般戦", 1:"G3", 2:"G2", 3:"G1", 4:"PG1", 5:"SG" }
HELD_TYPE_IDX = { 0:"通常", 1:"ﾓｰﾆﾝｸﾞ" ,2:"ｻﾏｰﾀｲﾑ", 3:"ﾅｲﾀｰ", 4:"ﾐｯﾄﾞﾅｲﾄ" }

GUI, MUI           = "Yu Gothic UI", "Meiryo UI"
GR, SD, RD, RA, SK, BD = "groove", "solid", "ridge", "raised", "sunken", "bold"
ALL, CT            = "nsew", "center"

GRADE_OPT = [ {"font":(MUI, 10    ), "bg":"white",   "fg":"black"   },
              {"font":(MUI, 10    ), "bg":"white",   "fg":"black"   },
              {"font":(MUI, 10, BD), "bg":"#d2ffd1", "fg":"#ff3939" },
              {"font":(MUI, 10, BD), "bg":"#d2ffd1", "fg":"#ff3939" },
              {"font":(MUI, 10, BD), "bg":"#d2ffd1", "fg":"#ff3939" },
              {"font":(MUI, 10, BD), "bg":"#72c5ff", "fg":"#ff3939" }  ]

SCOL     = "#a5e6ff"#?

MAIN_BG  = "#F0F4FA"
HDR_BG   = "#2B4A7A"
BTN_BG   = "#4A6A9A"
WHITE    = "#FFFFFF"
YELLOW1  = "#FFD700"
YELLOW2  = "#F1EE62"
GRAY1    = "#ECECEC"
GRAY2    = "#CFCFCF"
BLACK1   = "#000000"
BLACK2   = "#222222"
BLUE     = "#0000FF"
LIT_RED  = "#FF6D6D"

HDR_B    = dict(bg=HDR_BG)
HDR_BF   = dict(bg=HDR_BG,  fg=WHITE)
BTN_BF   = dict(bg=BTN_BG,  fg=WHITE)
BTN_OFF  = dict(bg=BTN_BG,  fg=WHITE,  Bd=(1,RA))
GRAY_OFF = dict(bg=GRAY1,   fg=BLACK1, Bd=(1,RA))
YELL1_ON = dict(bg=YELLOW1, fg=BLACK2, Bd=(1,GR))
YELL2_ON = dict(bg=YELLOW2, fg=BLACK2, Bd=(1,SK))

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
class RaceSelectWindow(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.app        = app
        self.date       = today_iso()
        self.range_var  = tk.StringVar(value="270")
        self.sub_window = False
        self.cells:dict[int, dict[str,tk.Widget]] = {}

        fr_root = cFr(self,    W=800, H=630, px=21)
        fr_root._grid(R=0, C=0, py=(0,28)) ;fr_root.Pgate()

        fr_hedr      = cFr(fr_root, W=758, H= 50)
        fr_ctrl      = cFr(fr_root, W=758, H= 50)
        self.fr_grid = cFr(fr_root, W=758, H=522, Bd=(1,SD))

        fr_hedr._grid(     R=0, C=0)      ;fr_hedr.Pgate()
        fr_ctrl._grid(     R=1, C=0)      ;fr_ctrl.Pgate()
        self.fr_grid._grid(R=2, C=0) ;self.fr_grid.Pgate()

        fr_hedr.Cconf(0, Min=130) ;fr_hedr.Rconf(0, Min=50)
        fr_hedr.Cconf(1, Min=418)
        fr_hedr.Cconf(2, Min= 85)
        fr_hedr.Cconf(3, Min= 75)
        fr_hedr.Cconf(4, Min= 50)
        fr_ctrl.Cconf(0, Min=240) ;fr_ctrl.Rconf(0, Min=50)
        fr_ctrl.Cconf(1, Min=210)
        fr_ctrl.Cconf(2, Min=188)
        fr_ctrl.Cconf(3, Min=120)

        cBtn( fr_hedr, W=9, text="メイン 画面", font=(MUI,9), bg="white",
               Com=lambda:self.app.show_screen("Main") )._grid(R=0, C=0, Stk="w")

        cLbl( fr_hedr, W=30, Anc=CT, text="Race Window 表示レース  選 択", font=(GUI,11,BD)
             )._grid(R=0, C=1, Stk=ALL)

        cLbl(fr_hedr, W=11, text="データ算出期間", font=(MUI,10))._grid(R=0, C=2, Stk="w")
        self.ent_range = cEnt(fr_hedr, W=8, Txtv=self.range_var, font=(MUI,10), Jst="right")
        self.ent_range._grid(R=0, C=3, Stk="we")
        cLbl(fr_hedr, W= 3, text="日",             font=(MUI,10))._grid(R=0, C=4, Stk="w")

        self.btn_prev = cBtn( fr_ctrl, W=5, text="＜", font=(MUI,8,BD), Bd=(1,RA), **BTN_BF,
                                                                  Com=lambda:self._shift_date(-1) )
        self.btn_next = cBtn( fr_ctrl, W=5, text="＞", font=(MUI,8,BD), Bd=(1,RA), **BTN_BF,
                                                                  Com=lambda:self._shift_date( 1) )
        self.btn_sub  = cBtn( fr_ctrl, W=8, text="SUB OFF", font=(MUI,9), bg="white", Rel=RA,
                                                                  Com=lambda:self._odds_on() )

        txt = f"{to_date(self.date).month} 月 {to_date(self.date).day} 日    開催一覧"
        self.lbl_date  = cLbl(fr_ctrl, text=txt, font=(MUI,10), bg=MAIN_BG)

        self.btn_prev._grid( R=0, C=0, Stk="e")
        self.lbl_date._grid( R=0, C=1, Stk=ALL)
        self.btn_next._grid( R=0, C=2, Stk="w")
        self.btn_sub._grid(  R=0, C=3, Stk="e")

        for r in range(4):
            self.fr_grid.Rconf(r, Min=130)
        for c in range(6):
            self.fr_grid.Cconf(c, Min=126)

        self._render_for_date()

    #---------------------------------------------
    def _odds_on(self):

        if self.sub_window:
            self.btn_sub._config(text="SUB OFF", **GRAY_OFF)
        else:
            self.btn_sub._config(text="SUB  ON", **YELL2_ON)

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
            fr_cell = cFr(self.fr_grid, W=126, H=130, Bd=(1,GR), bg=MAIN_BG)
            fr_cell._grid(R=row, C=col, Stk=ALL) ;fr_cell.Pgate()

            fr_cell.Rconf(0, Min=25) ;fr_cell.Cconf(0, Min=78)
            fr_cell.Rconf(1, Min=21) ;fr_cell.Cconf(1, Min=48)
            fr_cell.Rconf(2, Min=50)
            fr_cell.Rconf(3, Min=30)

            lb_hedr = cLbl(fr_cell, Anc=CT,  text=v_name, font=(GUI,10,BD), Bd=(1,RD), **HDR_BF)
            lb_topL = cLbl(fr_cell, Anc="e", text="",     font=(MUI,9), bg=MAIN_BG)
            lb_topR = cLbl(fr_cell, Anc=CT,  text="")
            lb_cntr = cLbl(fr_cell, Anc=CT,  text="",     font=(MUI,8), Wrap=122)
            lb_botm = cLbl(fr_cell, Anc=CT,  text="",     font=(MUI,9))

            lb_hedr._grid(R=0, C=0, Cspan=2, Stk=ALL)
            lb_topL._grid(R=1, C=0,          Stk="we", py=(3.0), px=(5,0))
            lb_topR._grid(R=1, C=1,          Stk="we", py=(3.0), px=(0,5))
            lb_cntr._grid(R=2, C=0, Cspan=2, Stk=ALL)
            lb_botm._grid(R=3, C=0, Cspan=2, Stk=ALL)

            widg = self.cells[venue_id] = {     "frm":fr_cell, "hedr":lb_hedr, "topL":lb_topL,
                                               "cntr":lb_cntr, "topR":lb_topR, "botm":lb_botm,
                                             "clicks":(lb_topL, lb_cntr, lb_topR, lb_botm)     }

        if info is None:
            widg["frm" ].configure(bg=MAIN_BG)
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
            widg["topR"].configure(text=f"",        **g_opt)
            widg["cntr"].configure(text=f"{title}", bg="white")
            widg["botm"].configure(text=day_lbl,    bg="white")

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
