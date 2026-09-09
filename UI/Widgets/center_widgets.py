# Widgets/center_widgets.py

from typing              import Union, Dict, List, Optional, Tuple, Any
from Helpers.Custum_func import cFr, cLbl, cBtn, cCvs
from tkinter             import ttk
import tkinter as tk

GUI, MUI, HNH, CBR = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, BD = "groove", "solid", "ridge", "raised", "bold"
ALL, CT            = "nsew", "center"

HDR_C              = "#e0e1f4"
HL_COL             = "#cce8ff"

BDFNT              = dict(font=(MUI,7,BD))
NMFNT              = dict(font=(MUI,7   ))

OPT                = [dict(font=(MUI,8,BD), bg="#cce8ff"),
                      dict(font=(MUI,8,  ), bg="white"),
                      dict(font=(MUI,8,  ), bg="#e9e6e6"),]
#===============================================================================
class LaneCenterManager:
    def __init__(self, lane:int=None):
 
        self.rows      = {}
        self.frame     = None
        self.subj_r    = 0
        self.subj_c    = lane
        self.disp      = 1
        self.dist_refs = {"rank_btn":{}, "course_btn":{}, "cells":{}, "move_cells":{}}
        self.move_cols = [ ("逃 げ", "逃げ"), (" 差 し ", "差し"), 
                           ("捲差し", "まくり差し"), ("まくり", "まくり") ]
    #-------------------------------------------------------
    def _build_distribute_ui(self, fr:tk.Frame):

        self.frame     = fr
        self.dist_refs = {"rank_btn":{}, "course_btn":{}, "cells":{}, "move_cells":{}}

        for w in self.frame.winfo_children(): w.destroy()         #W=356, H=165

        for r in range(8):
            if r == 0: self.frame.Rconf(r, W=1, minsize=21)
            else:      self.frame.Rconf(r, W=1, minsize=24)
        for c in range(8):
            if c <= 3: self.frame.Cconf(c, W=1, minsize=51)
            else:      self.frame.Cconf(c, W=1, minsize=38)

        self.totl = cLbl(self.frame, text="", width=5, font=(MUI,8,BD), bg=HDR_C, Bd=(1,RD))
        self.totl._grid(R=0, C=0, px=0, py=0, Stk=ALL)
        self.totl.bind("<Button-1>", lambda e: self._change_disp())

        style = ttk.Style()
        style.configure("d.TButton", font=(MUI,7), anchor="center")

        for rnk in range(1, 4):
            rbtn = cLbl(self.frame, text=f"{rnk} 着", width=6, font=(GUI,8), Bd=(1,RA), bg="#f3f5ff")
            rbtn.bind("<Button-1>",lambda e, rk=rnk: self._toggle_subject_rank(rk))
            rbtn._grid(R=0, C=rnk, Stk=ALL)
            self.dist_refs["rank_btn"][rnk] = rbtn

        for cou in range(1, 7):
            cbtn = ttk.Button(self.frame, text=f"{cou}コース", width=5, style="d.TButton",
                               command=lambda c=cou: self._on_subject_course_btn(c))
            cbtn.grid(row=cou, column=0, sticky=ALL)
            self.dist_refs["course_btn"][cou] = cbtn

            for rnk in range(1, 4):
                cell = cFr(self.frame, width=5)
                cell._grid(R=cou, C=rnk, Stk=ALL)
                cv   = cCvs(cell, W=49, H=22, relief=RD, bd=1) ;cv.place(x=-2, y=-2)
                self.dist_refs["cells"][(cou, rnk)] = cv

        for col, (label, _) in enumerate(self.move_cols):
            cLbl(self.frame, text=label, font=(GUI,8), Bd=(1,RD), bg=HDR_C, Anc=CT
                 )._grid(R=0, C=col+4, Stk=ALL)

        for row in range(1, 7):
            for col, (label, _) in enumerate(self.move_cols):
                bg = "#e9e6e6" if row >= 2 and col == 0 else "white"
                cell = cLbl(self.frame, text="", width=4, Bd=(1,RD), bg=bg, Anc=CT)
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
            b.configure(bg="#cce8ff" if self.subj_r == rk else "#f3f5ff",
                         relief=GR if self.subj_r == rk else RA)
        for c, b in self.dist_refs["course_btn"].items():
            b.state(["pressed"] if self.subj_c == c else ["!pressed"])

        total = own_cnt[self.subj_c][self.subj_r] if self.subj_r else starts[self.subj_c]
        fg = "red" if total < 10 else "black"
        self.totl.configure(text=f"{total}", fg=fg)

        for c in range(1, 7):
            vt = 0
            for rk in range(1, 4):
                cv = self.dist_refs["cells"][(c, rk)] ;cv.delete("all")

                if c  == self.subj_c and ((self.subj_r == 0) or (self.subj_r != 0 and rk == self.subj_r)):
                    v = own_cnt[self.subj_c][rk]                ;bg="#cce8ff" ;f=(MUI,8,BD)
                elif self.subj_r == 0:
                    v = oth_cnt[self.subj_c][c][rk]             ;bg="white"   ;f=(MUI,8)
                else:
                    v = oth_by[self.subj_c][self.subj_r][c][rk] ;bg="white"   ;f=(MUI,8)
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
                opt   = OPT[0] if row == self.subj_c else OPT[1]
                if col >= 4: opt = OPT[2]
                lb_wm.config(text=cnt if cnt else "", **opt)

    #-------------------------------------------------------
    def _change_disp(self):
        self.disp = 1 - self.disp
        self.totl.configure(relief=GR if self.disp else RD)
        self._render_distribute_table(self.rows)

    #-----------------------------------
    def _on_subject_course_btn(self, c:int):
        self.subj_c = c
        self._render_distribute_table(self.rows)

    #-----------------------------------
    def _toggle_subject_rank(self, rk: int):
        self.subj_r = 0 if self.subj_r == rk else rk
        self._render_distribute_table(self.rows)

#===============================================================================
def framing_center_widgets(self, fr:tk.Frame, lane:int, rows:dict, wdgt_no:int):

    if not hasattr(self, "_lane_managers"):
        self._lane_managers = {}

    if lane not in self._lane_managers:
        self._lane_managers[lane] = LaneCenterManager(lane)

    manager = self._lane_managers[lane]

    if wdgt_no == 1:
        manager._build_distribute_ui(fr)
        manager._render_distribute_table(rows)

