# -*- coding: utf-8 -*-
# C:\boatrace\UI\Widgets\center_widgets.py

from typing              import Union, Dict, List, Optional, Tuple, Any
from Helpers.Custum_func import cFr, cLbl, cBtn, cCvs
from tkinter             import ttk
import tkinter as tk

GUI, MUI, HNH, CBR     = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, SK, BD = "groove", "solid", "ridge", "raised", "sunken", "bold"
ALL, CT                = "nsew", "center"

BLANK_C  = "#E9E6E6"
CNT_CEL  = "#E0E1F4"

HL_BLU   = "#CCE8FF"
BLUE2    = "#0D7DDA"
WHITE    = "#FFFFFF"
BLACK    = "#000000"
HDR_BG   = "#2B4A7A"
BTN_BG   = "#4A6A9A"

HDR_B    = dict(bg=HDR_BG)
HDR_BF   = dict(bg=HDR_BG, fg=WHITE)
BTN_BF   = dict(bg=BTN_BG, fg=WHITE)
HDR_OFF  = dict(bg=HDR_BG, fg=WHITE, Bd=(1,RA))
BTN_OFF  = dict(bg=BTN_BG, fg=WHITE, Bd=(1,RA))
BLUE1_ON = dict(bg=HL_BLU, fg=BLACK, Bd=(1,SK))
BLUE2_ON = dict(bg=BLUE2,  fg=WHITE, Bd=(1,SK))

WM_OPTS  = [ dict(font=(MUI,8,BD), bg=HL_BLU),
             dict(font=(MUI,8,  ), bg="white"),
             dict(font=(MUI,8,  ), bg=BLANK_C), ]

#===============================================================================
class LaneCenterManager:
    def __init__(self, lane:int):
 
        self.rows      = {}
        self.subj_r    = 0
        self.subj_c    = lane
        self.disp      = 1
        self.dist_refs = {"rank_btn":{}, "course_btn":{}, "cells":{}, "move_cells":{}}
        self.move_cols = [ ("逃 げ", "逃げ"), (" 差 し ", "差し"), 
                           ("捲差し", "まくり差し"), ("まくり", "まくり") ]

    #-------------------------------------------------------
    def _build_distribute_ui(self, fr:tk.Frame):

        for child in fr.winfo_children(): child.destroy()

        for r in range(8):
            if r == 0: fr.Rconf(r, W=1, minsize=21)
            else:      fr.Rconf(r, W=1, minsize=24)
        for c in range(8):
            if c <= 3: fr.Cconf(c, W=1, minsize=51)
            else:      fr.Cconf(c, W=1, minsize=38)

        self.totl = cLbl(fr, W=5, text="", font=(GUI,9,BD), **BTN_BF, Bd=(1,RD), Csr="hand2")
        self.totl._grid(R=0, C=0, Stk=ALL, px=0, py=0)
        self.totl.bind("<Button-1>", lambda e: self._change_disp())

        for rnk in range(1, 4):
            rbtn = cLbl(fr, W=6, text=f"{rnk} 着", font=(GUI,8,BD), **HDR_OFF, Csr="hand2")
            rbtn.bind("<Button-1>",lambda e, r=rnk: self._toggle_subject_rank(r))
            rbtn._grid(R=0, C=rnk, Stk=ALL)
            self.dist_refs["rank_btn"][rnk] = rbtn

        for cou in range(1, 7):
            cbtn = cBtn(fr, W=1, text=f"{cou} コース", font=(MUI,7,BD), **HDR_OFF, Csr="hand2",
                                  Com=lambda c=cou: self._on_subject_course_btn(c) )
            cbtn._grid(R=cou, C=0, Stk=ALL)
            self.dist_refs["course_btn"][cou] = cbtn

            for rnk in range(1, 4):
                cell = cFr(fr, W=5)
                cell._grid(R=cou, C=rnk, Stk=ALL)
                cv   = cCvs(cell, W=49, H=22, Bd=(1,RD)) ;cv.place(x=-2, y=-2)
                self.dist_refs["cells"][(cou, rnk)] = cv

        for col, (label, _) in enumerate(self.move_cols):
            cLbl(fr, text=label, font=(GUI,7,BD), Bd=(1,RD), **HDR_BF)._grid(R=0, C=col+4, Stk=ALL)

        for row in range(1, 7):
            for col, (label, _) in enumerate(self.move_cols):
                bg   = BLANK_C if row >= 2 and col == 0 else "white"
                cell = cLbl(fr, W=4, text="", bg=bg, Anc=CT, Bd=(1,RD))
                cell._grid(R=row, C=col+4, Stk=ALL)
                self.dist_refs["move_cells"][(row, label)] = cell

    #-------------------------------------------------------
    def _render_distribute_table(self, rows:dict):

        if not self.dist_refs: return

        self.rows = rows
        own_cnt   = self.rows["own_cnt"]
        oth_cnt   = self.rows["oth_cnt"]
        oth_by    = self.rows["oth_by_r"]
        mv_all    = self.rows["win_move"]
        starts    = self.rows["starts"]

        for rk, b in self.dist_refs["rank_btn"].items():
            b._config(**BLUE2_ON if self.subj_r == rk else HDR_OFF)
        for c, b in self.dist_refs["course_btn"].items():
            b._config(**BLUE2_ON if self.subj_c == c  else HDR_OFF)

        total = own_cnt[self.subj_c][self.subj_r] if self.subj_r else starts[self.subj_c]
        fg    = "red" if total < 10 else "white"
        self.totl.config(text=f"{total}", fg=fg)

        for c in range(1, 7):
            vt = 0
            for rk in range(1, 4):
                cv = self.dist_refs["cells"][(c, rk)] ;cv.delete("all")

                if c  == self.subj_c and ((self.subj_r == 0) or (self.subj_r != 0 and rk == self.subj_r)):
                    v = own_cnt[self.subj_c][rk]                ;bg=HL_BLU  ;f=(MUI,8,BD)
                elif self.subj_r == 0:
                    v = oth_cnt[self.subj_c][c][rk]             ;bg="white" ;f=(MUI,8)
                else:
                    v = oth_by[self.subj_c][self.subj_r][c][rk] ;bg="white" ;f=(MUI,8)
                vt += v
                if v: text = f"{v}" if self.disp else f"{int(vt / total *100)}"
                else: text = ""

                cv.create_text(27, 14, text=text, font=f) ;cv.config(bg=bg)
                if v and not self.disp: cv.create_text(41, 17, text="%", font=(MUI,6))

        if self.subj_r:
            win_move = self.rows["subj_wm"][self.subj_c][self.subj_r] or None
        else:
            win_move = mv_all.get(self.subj_c, None)

        if win_move is None: win_move = {c:{} for c in range(1, 7)}

        for row in range(1, 7):
            wmvs = win_move.get(row, {})
            for col, (label, key) in enumerate(self.move_cols):
                if row >= 2 and col == 0: continue
                lb_wm = self.dist_refs["move_cells"][(row, label)]
                cnt   = wmvs.get(key, 0)
                opt   = WM_OPTS[0] if row == self.subj_c else WM_OPTS[1]
                if col >= 4: opt = WM_OPTS[2]
                lb_wm.config(text=cnt if cnt else "", **opt)

    #-------------------------------------------------------
    def _change_disp(self):
        self.disp = 1 - self.disp
        self.totl.config(relief=RD if self.disp else GR)
        self._render_distribute_table(self.rows)

    #-----------------------------------
    def _on_subject_course_btn(self, c:int):
        self.subj_c = c
        self._render_distribute_table(self.rows)

    #-----------------------------------
    def _toggle_subject_rank(self, rk: int):
        self.subj_r = 0 if self.subj_r == rk else rk
        self._render_distribute_table(self.rows)

    #-----------------------------------
    def reset_state(self, lane):
        self.subj_r = 0
        self.subj_c = lane
        self.disp   = 1

#===============================================================================
def framing_center_widgets(self, fr:tk.Frame, lane:int, rows:dict, wdgt_no:int):

    if wdgt_no == 1:
        if lane not in self.lane_managers:
            manager = LaneCenterManager(lane)
            manager._build_distribute_ui(fr)
        else:
            manager = self.lane_managers[lane]

        manager._render_distribute_table(rows)
        self.lane_managers[lane] = manager

