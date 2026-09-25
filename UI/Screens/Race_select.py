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

GRADE_OPT    = [ {"font":(MUI, 10    ), "bg":"white",   "fg":"black"   },
                 {"font":(MUI, 10    ), "bg":"white",   "fg":"black"   },
                 {"font":(MUI, 10, BD), "bg":"#d2ffd1", "fg":"#ff3939" },
                 {"font":(MUI, 10, BD), "bg":"#d2ffd1", "fg":"#ff3939" },
                 {"font":(MUI, 10, BD), "bg":"#d2ffd1", "fg":"#ff3939" },
                 {"font":(MUI, 10, BD), "bg":"#72c5ff", "fg":"#ff3939" }  ]

HDR_OPT = dict(font=(GUI,10,BD), bg="#d3dee9", Bd=(1,RD))
#===============================================================================
def date_today() -> date:

    JST = timezone(timedelta(hours=9))

    return dt.now(JST).date()
# ------------------
def _str(d:date) -> str:

    return d.strftime("%Y-%m-%d")

# ======================== レース選択画面 ============================
class RaceSelectScreen(tk.Frame):

    def __init__(self, parent, app, db_path):
        super().__init__(parent)

        style = ttk.Style()
        style.configure("RSS.TButton", font=(MUI,9), anchor="center")
        style.configure("RSS.TEntry", padding=(0, 3, 3, 3))

        self.app       = app
        self.db_path   = db_path
        self.date      = date_today()
        self.range_var = tk.StringVar(value="270")
        self.ow        = False
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

        btn_main = ttk.Button( fr_hedr, text="メイン 画面", width=10, style="RSS.TButton",
                                               command=lambda:self.app.show_screen("Main") )
        btn_main.grid(row=0, column=0, ipady=5, sticky="w")

        cLbl( fr_hedr, W=33, Anc=CT, text="Race Window 表示レース  選 択", font=(GUI,11,BD)
             )._grid(R=0, C=1, Stk="w", padx=(20,0))

        cLbl(fr_rnge, text="データ算出期間", font=(MUI,10), width=10)._grid(R=0, C=0)
        cLbl(fr_rnge, text="日",             font=(MUI,10), width= 1)._grid(R=0, C=2)

        self.ent_range = ttk.Entry( fr_rnge, width=8, textvariable=self.range_var,
                                    style="RSS.TEntry", justify="right", font=(MUI,10) )
        self.btn_prev  = ttk.Button(fr_ctrl, text="＜", width=3, command=lambda:self._shift_date(-1))
        self.btn_next  = ttk.Button(fr_ctrl, text="＞", width=3, command=lambda:self._shift_date( 1))
        self.btn_odds  = cBtn( fr_ctrl, text="オッズ OFF", width=10, bg="white", relief="raised",
                                        font=(MUI,10), command=lambda:self._odds_on()             )
        self.lbl_date  = cLbl( fr_ctrl, text=f"{self.date.month} 月 {self.date.day} 日    開催一覧",
                                                                          font=(MUI,10), bg=MAIN_BG  )

        self.ent_range.grid(row=0, column=1)
        self.btn_prev.grid( row=0, column=0, padx=(140,0))
        self.lbl_date.grid( row=0, column=1)
        self.btn_next.grid( row=0, column=2)
        self.btn_odds.grid( row=0, column=3, padx=(100,0))

        self.fr_grid = cFr(fr_wrap, W=660, H=440, Bd=(1,SD))
        self.fr_grid._grid(R=0, C=0, Stk=ALL) ;self.fr_grid.Pgate()

        for r in range(4):
            self.fr_grid.Rconf(r, weight=1)
        for c in range(6):
            self.fr_grid.Cconf(c, weight=1)

        self._render_for_date()

    #---------------------------------------------
    def _odds_on(self):

        if self.ow:
            self.btn_odds.config(text="オッズ OFF", bg="white", relief="raised")
        else:
            self.btn_odds.config(text="オッズ ON", bg="#fbffcb", relief="ridge",)

        self.ow = not self.ow

    # ---------- public hooks ----------
    def on_show(self):

        self._render_for_date()

    # ----------------------------------
    def _shift_date(self, diff_days:int):

        try:
            self.date = self.date +timedelta(days=diff_days)
        except Exception:
            self.date = date_today()

        self._render_for_date()

    # --------------------------------------------
    def _render_for_date(self):
 
        self.lbl_date.config(text=f"{self.date.month} 月 {self.date.day} 日     開催一覧")
        dayinfo = self._load_day_info(self.date)
 
        for vid, vname in enumerate(VENUES, start=1):
            info = dayinfo.get(vid, None)
            self._render_cell((vid-1)//6, (vid-1)%6, vid, vname, info)

    # --------------------------------------------
    def _render_cell(self, row:int, col:int, venue_id:int, v_name:str, info:dict|None):

        widg  = self._cells.get(venue_id)

        if widg is None:
            fr_cell = cFr(self.fr_grid, W=110, H=110, Bd=(1,GR), bg=MAIN_BG)
            fr_cell._grid(R=row, C=col, Stk=ALL) ;fr_cell.Pgate()

            fr_cell.Rconf(0, Min=30) ;fr_cell.Cconf(0, Min=60)
            fr_cell.Rconf(1, Min=40) ;fr_cell.Cconf(1, Min=50)
            fr_cell.Rconf(2, Min=40)

            lb_hedr = cLbl(fr_cell, Anc=CT,  text=v_name, **HDR_OPT)
            lb_topL = cLbl(fr_cell, Anc="e", text="", font=(MUI,11), bg=MAIN_BG)
            lb_topR = cLbl(fr_cell, Anc=CT,  text="")
            lb_botm = cLbl(fr_cell, Anc=CT,  text="", font=(MUI,10))

            lb_hedr._grid(R=0, C=0, Cspan=2, Stk=ALL)
            lb_topL._grid(R=1, C=0,          Stk="we")
            lb_topR._grid(R=1, C=1,          Stk="we")
            lb_botm._grid(R=2, C=0, Cspan=2, Stk=ALL)

            widg = self._cells[venue_id] = { "frm":fr_cell, "hedr":lb_hedr, "topL":lb_topL,
                                                            "topR":lb_topR, "botm":lb_botm,
                                             "clicks":(lb_topL, lb_topR, lb_botm)           }

        if info is None:
            widg["frm"].configure(bg=MAIN_BG)
            widg["topL"].configure(text="", bg=MAIN_BG, fg="black")
            widg["topR"].configure(text="", bg=MAIN_BG, fg="black")
            widg["botm"].configure(text="", bg=MAIN_BG, fg="black")

            framing_held_type_icon(self, widg["topR"], 0)

            self._apply_click_binding(widg, venue_id, enabled=False)

        else:
            grade   = GRADE_IDX.get(info.get("grade") or 0, "一般")
            day_lbl = self._calc_day_label(self.date, venue_id)
            g_opt   = GRADE_OPT[info.get("grade") or 0]
            h_type  = info.get("held_type", 0)

            widg["frm"].config(bg="white")
            widg["topL"].configure(text=f"{grade}", **g_opt)
            widg["topR"].configure(text=f"",        **g_opt)
            widg["botm"].configure(text=day_lbl, bg="white")

            framing_held_type_icon(self, widg["topR"], h_type)   
      
            self._apply_click_binding(widg, venue_id, enabled=True)

    # --------------------------------------------
    def _apply_click_binding(self, cell:dict, venue_id:int, enabled:bool):

        widgets = cell["clicks"]

        if enabled:
            for w in widgets:
                w.configure(cursor="hand2")
                w.bind("<Button-1>", lambda e, v=venue_id:self._open_race_window(v, self.ow))
        else:
            for w in widgets:
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
    def _load_day_info(self, _date:date):

        out:dict[int, dict] = {}

        rows = dal.fetch_all(
            """
            SELECT venue_id,
                   MIN(grade)     AS grade,
                   MIN(held_type) AS held_type
              FROM Race_programs
             WHERE date = ?
          GROUP BY venue_id
            """,
            (_str(_date),))

        for row in rows:
            vid      = int(row["venue_id"])
            out[vid] = dict(grade=row["grade"], held_type=row["held_type"])

        return out

    # --------------------------------------------
    def _calc_day_label(self, _date:date, venue_id:int):

        labels, _ = build_day_lbl(_date, venue_id)

        for items in labels:
            if items["date"] == _str(_date):
                if items.get("is_final"):      return "最終日"
                if items.get("label_no") == 1: return "初日"
                else:                          return f"{items["label_no"]}日目"

        return "ー"
