# -*- coding: utf-8 -*-
# C:\boatrace\UI\Screens\Analysis_player.py

from tkinter                import ttk, messagebox
from PIL                    import Image, ImageTk
from typing                 import Dict, Optional
from itertools              import product
from dateutil.relativedelta import relativedelta
from collections            import defaultdict
from datetime               import datetime as dt, date, time, timedelta
import os, tkinter as tk, Dal as dal

from Helpers.Custum_func    import cFr, cLbl, cBtn
from Helpers.queries        import Query
from Widgets.widgets        import set_player_image, framing_graph
from Screens.same_period_player import PlayerSamePeriodScreen


GUI, MUI       = "Yu Gothic UI", "Meiryo UI"
BD             = "bold"
GR, SD, RA, RD = "groove", "solid", "raised", "ridge"
ALL, CT        = "nsew", "center"

COL_KEYS  = ["全", "SG", "G1", "G2", "一 般"]

ROW_KEYS  = [ ("starts",      "出走 数"),
              ("series_cnt",  "出場 節"),
              ("score_ave",   "勝率"   ),
              ("st_ave",      "平均 ST"),
              ("to_final",    "優 出"  ),
              ("victory",     "優 勝"  ),
              ("r1",          "1 着"   ),
              ("r2",          "2 着"   ),
              ("r3",          "3 着"   ),
              ("r4",          "4 着"   ),
              ("r5",          "5 着"   ),
              ("r6",          "6 着"   ),
              ("F_L",         "F / L"  ),
              ("S_K",         "S / K"  ), ]

MONTH     = { "1M": 1, "2M": 2, "3M": 3, "4M": 4, "5M": 5, "6M": 6, "7M": 7, "8M": 8, "9M": 9,
              "1Y":12, "2Y":24, "3Y":36, "4Y":48, "5Y":60,"10Y":120 }

ADJUST    = {"pre_y":-12, "pre_m":-1, "next_y":12, "next_m":1}

FINAL_RNK = { 1:"①", 2:"②", 3:"③", 4:"④", 5:"⑤", 6:"⑥",
              "F":"(F)", "L":"(L)", "S":"(S)", "K":"(K)"       }

GOPT      = { 0: dict(text="一般",            font=(MUI,8   )),
              1: dict(text="G3",              font=(MUI,8   )), 
              2: dict(text="G2",  fg="green", font=(MUI,9,BD)),
              3: dict(text="G1",  fg="blue",  font=(MUI,9,BD)),
              4: dict(text="PG1", fg="blue",  font=(MUI,9,BD)),
              5: dict(text="SG",  fg="red",   font=(MUI,9,BD))  }

FRM_COLOR = { 0: dict(bg="SystemButtonFace", fg=  "black"),
              1: dict(bg="#FFFFFF",          fg="#000000"),
              2: dict(bg="#000000",          fg="#FFFFFF"),
              3: dict(bg="#D40000",          fg="#FFFFFF"),
              4: dict(bg="#0066CC",          fg="#FFFFFF"),
              5: dict(bg="#FFD400",          fg="#000000"),
              6: dict(bg="#008A2E",          fg="#FFFFFF"), }

CLS_COLOR = { "A1": dict(fg="blue",    bg="white", font=(GUI,10,BD)),
              "A2": dict(fg="#008000", bg="white", font=(GUI,10,BD)),
              "B1": dict(fg="black",   bg="white", font=(GUI,10   )),
              "B2": dict(fg="red",     bg="white", font=(GUI,10,BD))  }

BDFNT          = dict(font=(MUI,9,BD))
NMFNT          = dict(font=(MUI,9   ))

COL1, COL2, COL3 = "#FFF4AA", "#33EE33", "#2A62FF"
SRC_COL, SRS_COL = "#a463ff", "#505050"
STC_COL, STR_COL = "#2A62FF", "#2a9a01"
G_COL            = {0:"#616161", 1:"#616161", 2:"#05eb00", 3:"#3f76ff", 4:"#3f76ff", 5:"red"}
NOR_COL          = {"bg":"white", "fg":"black"}
HDR_COL          = "#e0e1f4"
HL_COL           = "#cce8ff"

CEL_W  = 65
CEL_H  = 27
TBL_W  = CEL_W  *6 -1
TBL_H  = CEL_H *15 -1

C_W    = 72
CLW    = (C_W *5)+2

# --------
def wid_txt(s: str) -> str:
    hair = "\u200A" 
    return hair.join(list(s))
#===============================================================================
class PlayerAnalysisScreen(tk.Toplevel):
    def __init__( self, master, p_id:int, v_id:Optional[int]= None,
                                         d_iso:Optional[str]= None,
                                           cou:Optional[int]= None  ):
        super().__init__(master)

        self.title("")
        self.geometry("1201x970+750+200")
        self.resizable(False, False)

        self.date_from  = date.today()
        self.date_to    = date.today()

        self.query       = None
        self.data_rows   = None
        self.series_rows = None
        self.s_years     = []
        self.year_idx    = 0
        self.adjustment  = False

        self.course      = cou
        self.rank        = 0
        self.dist_refs   = {}
        self.disp        = 0
        self.player_id   = p_id
        self.venue_id    = v_id
        self.period      = 9
        self.grade_key   = [0, 1, 2, 3, 4, 5]

        self.grade_state  = { (0, 1):True, (2,):True, (3, 4):True, (5,):True }

        self.trend_state  = { "sr_single":True,  "sr_cumltv":False,
                              "st_single":False, "st_cumltv":False  }

        self.filter_state = {   "str_wind":False,      "local":False,
                              "all_ladies":False, "not_ladies":False,
                                    "rain":False,  "sea_water":False,
                             "fresh_water":False,      "river":False,
                                "brackish":False, "has_flying":False, }

        self.filter_dict  = {   "str_wind":("wind_spd",        5),
                                   "local":("venue_id", self.venue_id),
                              "all_ladies":("all_ladies",      1),
                              "not_ladies":("all_ladies",      0),
                                    "rain":("weather",      "雨"),
                               "sea_water":("water_type", "海水"),
                             "fresh_water":("water_type", "淡水"),
                                   "river":("water_type", "河川"),
                                "brackish":("brackish",   "汽水"),
                              "has_flying":("flying", "__DYN_FLYING__"), }

        self._build_ui()
        self._load_player_basic(self.player_id)
        self._refresh_classes()
        self._apply_period("9M")

        self._update_rows()

        self._refresh_players_data()
        self._refresh_bar_graph()
        self._refresh_trend_graph()
        self._refresh_series_panel()

    # ====================== UI ============================
    def _build_ui(self):

        fr_root  = cFr(   self, W=1181, H=960)
        fr_main  = cFr(fr_root, W= 800, H=710)
        fr_side  = cFr(fr_root, W= 381, H=702, Bd=(1,SD))
        fr_botm  = cFr(fr_root, W=1181, H=250)

        fr_body  = cFr(fr_main, W= 800, H=420)
        fr_grph  = cFr(fr_main, W= 800, H=300)

        fr_left  = cFr(fr_body, W= 390, H=420)
        fr_right = cFr(fr_body, W= 390, H=420)

        fr_plyr  = cFr(fr_left, W= 390, H=210)
        fr_clss  = cFr(fr_left, W= CLW, H= 66)
        fr_btnA  = cFr(fr_left, W= 390, H= 30)
        fr_btnB  = cFr(fr_left, W= 390, H= 30)
        fr_btnC  = cFr(fr_left, W= 390, H= 30)
        fr_btnD  = cFr(fr_left, W= 390, H= 30)

        fr_imag  = cFr(fr_plyr, W= 140, H=198)
        fr_prof  = cFr(fr_plyr, W= 218, H=205, Bd=(1,SD))

        self.bar = cFr(fr_grph, W= 320, H=253)
        fr_Gbtn  = cFr(fr_grph, W= 320, H= 35)
        fr_trnd  = cFr(fr_grph, W= 480, H=260)
        fr_Tbtn  = cFr(fr_grph, W= 480, H= 35)

        fr_info  = cFr(self.bar,W= 320, H= 25)
        self.win = cFr(fr_botm, W= 910, H=250)

        fr_root._grid( R=0, C=0, px=10,     py=( 0,10))  ; fr_root.Pgate()
        fr_main._grid( R=0, C=0                       )  ; fr_main.Pgate()
        fr_side._grid( R=0, C=1,            py=( 0, 8))  ; fr_side.Pgate()
        fr_botm._grid( R=1, C=0, Cspan=2              )  ; fr_botm.Pgate()
        fr_body._grid( R=0, C=0                       )  ; fr_body.Pgate()
        fr_grph._grid( R=1, C=0                       )  ; fr_grph.Pgate()
        fr_left._grid( R=0, C=0                       )  ; fr_left.Pgate()
        fr_right._grid(R=0, C=1                       )  ;fr_right.Pgate()
        fr_plyr._grid( R=0, C=0                       )  ; fr_plyr.Pgate()
        fr_imag._grid( R=0, C=0                       )  ; fr_imag.Pgate()
        fr_prof._grid( R=0, C=1, px=(15,10),py=( 3, 0))  ; fr_prof.Pgate()
        fr_clss._grid( R=1, C=0,            py=(10,10))  ; fr_clss.Pgate()
        fr_btnA._grid( R=2, C=0,            py=( 0, 2))  ; fr_btnA.Pgate()
        fr_btnB._grid( R=3, C=0,            py=( 0, 2))  ; fr_btnB.Pgate()
        fr_btnC._grid( R=4, C=0,            py=( 0, 2))  ; fr_btnC.Pgate()
        fr_btnD._grid( R=5, C=0,            py=( 0, 2))  ; fr_btnD.Pgate()
        fr_trnd._grid( R=0, C=1                       )  ; fr_grph.Pgate()
        fr_Gbtn._grid( R=1, C=0                       )  ; fr_Gbtn.Pgate()
        fr_Tbtn._grid( R=1, C=1                       )  ; fr_Tbtn.Pgate()
        self.win._grid(R=0, C=0)                         ; self.win.Pgate()
        self.bar._grid(R=0, C=0)
        # グラフ -------------
        self.cv_trend_graph  = tk.Canvas(fr_trnd, width=480, height=260)
        self.cv_trend_graph.place( x=0, y=0)

        # 選手ﾌﾟﾛﾌｨｰﾙ --------
        lb_img = cLbl(fr_imag)
        lb_img._grid(R=0, C=0)
        set_player_image(lb_img, self.player_id, (140, 198))

        self.basic_vars = {          "name": tk.StringVar(value=""),
                                "player_id": tk.StringVar(value=""),
                            "regist_period": tk.StringVar(value=""),
                                  "regions": tk.StringVar(value=""),
                                      "age": tk.StringVar(value=""),
                               "birthplace": tk.StringVar(value=""),
                                   "career": tk.StringVar(value=""),  }

        rows = [ ("選手名",  "name"   ), ("登録番号", "player_id"    ),
                 ("年齢",    "age"    ), ("登録期",   "regist_period"),
                 ("所属支部","regions"), ("出身地",   "birthplace"   ),  
                 ("選手歴", "career")                                   ]

        opt = dict(Anc=CT, Bd=(1,GR), font=(MUI,10))

        for r,(cap,key) in enumerate(rows):
            cLbl(fr_prof, text=cap, W=8, bg=HDR_COL, py=5, **opt)._grid(R=r, C=0, Stk="e")
            lbl = cLbl(fr_prof, textvariable=self.basic_vars[key], bg="white", width=18, py=5, **opt)
            lbl._grid(R=r, C=1, Stk="w")
            if r == 3:
                lbl.bind("<Button-1>",lambda e:self._same_period())
                lbl.config(cursor="hand2")

        # 直近5期適用級 ------
        self._class  = {}
        self.season  = {}
        self.sc_ave  = {}

        y_s = self._5seasons()

        for c in range(5):
            frA = cFr(fr_clss, W=C_W, H=20) ;frA._grid(R=0, C=c) ;frA.Pgate()
            frB = cFr(fr_clss, W=C_W, H=22) ;frB._grid(R=1, C=c) ;frB.Pgate()
            frC = cFr(fr_clss, W=C_W, H=22) ;frC._grid(R=2, C=c) ;frC.Pgate()
            frA.Cconf(0, W=1); frA.Rconf(0, W=1)
            frB.Cconf(0, W=1); frB.Rconf(0, W=1)
            frC.Cconf(0, W=1); frC.Rconf(0, W=1)
            l_a = cLbl(frA, text="", font=(MUI, 9), Bd=(1,RA), bg=HDR_COL) ;l_a._grid(R=0, C=0, Stk=ALL)
            l_b = cLbl(frB, text="", font=(GUI,10), Bd=(1,GR)          ) ;l_b._grid(R=0, C=0, Stk=ALL)
            l_c = cLbl(frC, text="", font=(MUI, 9), Bd=(1,GR)          ) ;l_c._grid(R=0, C=0, Stk=ALL)

            key = y_s[4-c]
            l_a.config(cursor= "hand2")
            l_a.bind( "<Button-1>",lambda e, k=key: self._on_switch(k, 0))

            self.season[key] = l_a ;self._class[key] = l_b ;self.sc_ave[key] = l_c

        # 成績データテーブル--
        self.fr_tbl = cFr(fr_right, W=TBL_W, H=TBL_H, Bd=(1,RD))
        self.fr_tbl._grid(R=0, C=0); self.fr_tbl.Pgate()

        self.fr_tbl.Cconf(0, minsize=CEL_W -3) ;self.fr_tbl.Rconf(0, minsize=CEL_H -3)

        for c in range(1, len(COL_KEYS) +1): self.fr_tbl.Cconf(c, minsize=CEL_W)
        for r in range(1, len(ROW_KEYS) +1): self.fr_tbl.Rconf(r, minsize=CEL_H)

        self.cells = {}
        # ----------
        def make_cell(r:int, c:int, text:str, f:str):
            opt = {"bg":HDR_COL, "Bd":(1,RD)} if r==0 else {"bg":"white", "Bd":(1,GR)}
            lbl = cLbl(self.fr_tbl, text=text, font=f, Anc=CT, **opt)
            lbl._grid(R=r, C=c, Stk=ALL)
            self.cells[(r,c)] = lbl
        #-----------
        make_cell(0, 0, text="", f=(MUI,10))
        for c, cap in enumerate(COL_KEYS, start=1):
            make_cell(0, c, text=cap, f=(MUI,10))
        for r, (_, cap) in enumerate(ROW_KEYS, start=1):
            make_cell(r, 0, text=cap, f=(GUI,10))
        for r in range(1, len(ROW_KEYS) +1):
            for c in range(1, len(COL_KEYS) +1):
                make_cell(r, c, text="-", f=(MUI,10))

        # ボタン -------------
        self.btns  = [{}, {}, {}, {}, {}]
        # ----------
        def mk_btn(frm, text, key, idx, w, px):
            b = ttk.Button( frm, text=text, width=w, style="r.TButton",
                                command=lambda k=key: self._on_switch(k, idx) )
            b.pack(side=tk.LEFT, padx=px)
            self.btns[idx][key] = b
            return b
        # ----------
        mk_btn(fr_btnA, "全期間",  "ALL", 0,7,0)
        mk_btn(fr_btnA, "今期",   "THIS", 0,7,(1,6))
        mk_btn(fr_btnA, "1 年",     "1Y", 0,7,1)
        for m in [9,6,3]: mk_btn(fr_btnA, f"{m}ヶ月", f"{m}M", 0,7,1)
        mk_btn(fr_btnB, "指定期間","adjust", 0,7,(0,10))
        mk_btn(fr_btnB, "<<", "pre_y", 4,3,0) ;mk_btn(fr_btnB, "<",   "pre_m", 4,3,0)
        self.lb_period = cLbl(fr_btnB, text=" 1 年  0 ヶ月", font=(MUI,9), Bd=(1,GR), bg="white")
        self.lb_period._pack(side=tk.LEFT, px=3)
        mk_btn(fr_btnB, ">", "next_m", 4,3,0) ;mk_btn(fr_btnB, ">>", "next_y", 4,3,0)

        mk_btn(fr_btnC, "当 地",           "local", 3,  6, 2)
        mk_btn(fr_btnC, "海水",        "sea_water", 3,  6, 2)
        mk_btn(fr_btnC, "淡水",      "fresh_water", 3,  6, 2)
        mk_btn(fr_btnC, "河川",            "river", 3,  6, 2)
        mk_btn(fr_btnC, "混合戦",     "not_ladies", 3,  6, 2)
        mk_btn(fr_btnC, "女子戦",     "all_ladies", 3,  6, 2)

        mk_btn(fr_btnD, "強 風",        "str_wind", 3,  6, 2)
        mk_btn(fr_btnD, "雨",               "rain", 3,  6, 2)
        mk_btn(fr_btnD, "ﾌﾗｲﾝｸﾞ",     "has_flying", 3,  6, 2)

        mk_btn(fr_Gbtn, "SG",                 (5,), 1,  6, 2)
        mk_btn(fr_Gbtn, "G1",               (3, 4), 1,  6, 2)
        mk_btn(fr_Gbtn, "G2",                 (2,), 1,  6, 2)
        mk_btn(fr_Gbtn, "一般/G3",          (0, 1), 1,  7, 2)

        mk_btn(fr_Tbtn, "勝率 (単)",   "sr_single", 2, 11, 4)
        mk_btn(fr_Tbtn, "勝率 (累積)", "sr_cumltv", 2, 11, 4)
        mk_btn(fr_Tbtn, "ＳＴ (単)",   "st_single", 2, 11, 4)
        mk_btn(fr_Tbtn, "ＳＴ (累積)", "st_cumltv", 2, 11, 4)

        # サイド =======================
        frm   = cFr(fr_side, W=379, H=35, bg=HDR_COL, Bd=(1,RD))       #379  700
        frm._grid(R=0, C=0,Cspan=2, Stk=ALL) ; frm.Pgate()

        # 節間成績------------
        self.btn_y_prev = cBtn(frm, text="＜", W=5, font=(MUI,6,BD), Com=lambda:self._on_series_btn(+1))
        self.btn_y_next = cBtn(frm, text="＞", W=5, font=(MUI,6,BD), Com=lambda:self._on_series_btn(-1))

        self.lbl_y_disp = cLbl(frm, text="---- 年", font=(MUI,9,BD), bg=HDR_COL, Anc=CT)

        self.btn_y_prev._pack(side=tk.LEFT, px=(70, 0), py=0, expand=False)
        self.lbl_y_disp._pack(side=tk.LEFT, px=( 0, 0), py=2, expand=True)
        self.btn_y_next._pack(side=tk.LEFT, px=( 0,70), py=0, expand=False)

        self.btn_y_prev.config(state="disable", bg="SystemButtonFace")
        self.btn_y_next.config(state="disable", bg="SystemButtonFace")

        self.canvs   = tk.Canvas(fr_side, width=352, height=665)
        self.scr_bar = ttk.Scrollbar(fr_side, orient="vertical", command=self.canvs.yview)
        self.body    = tk.Frame(self.canvs, width=352, height=665)

        self.canvs.configure(yscrollcommand=self.scr_bar.set)

        self.canvs.grid(  row=1, column=0, sticky=ALL)  ;self.canvs.grid_propagate(False)
        self.scr_bar.grid(row=1, column=1, sticky="ns") ;self.scr_bar.grid_propagate(False)

        self.window = self.canvs.create_window((0, 0), window=self.body, anchor="nw")
        #-----------
        def _mw(e):
            self.canvs.yview_scroll(int(-1 *(e.delta / 120)), "units")
        #-----------
        def _on_close():
           self.unbind_all("<MouseWheel>")
           self._mw_handler = None
           self.destroy()
        #-----------
        def _on_conf(event=None):
            self.canvs.configure(scrollregion=self.canvs.bbox("all"))
            self.canvs.itemconfigure(self.window, width=self.canvs.winfo_width())
        #-----------
        self.body.bind( "<Configure>", _on_conf)
        self.canvs.bind("<Configure>", _on_conf)
        self.canvs.bind_all("<MouseWheel>", _mw)
        self.protocol("WM_DELETE_WINDOW", _on_close)

        self._update_radio_btn_state( 0, "9M")
        self._update_toggle_btn_state(1, self.grade_state)
        self._update_toggle_btn_state(2, self.trend_state)

        self._build_distribute_ui()

    # ======================================================
    def _update_toggle_btn_state(self, idx:int, filter_dict:dict):

        for k, b in self.btns[idx].items():
            if filter_dict.get(k): b.state(['pressed'])
            else:                  b.state(['!pressed'])
    # --------------------------------------------
    def _update_radio_btn_state(self, idx:int, key:str|tuple):

        for k, b in self.btns[idx].items():
            if k == key: b.state(["pressed"])
            else:        b.state(["!pressed"])
        for k, lbl in self.season.items():
            if k == key: lbl.config(bg=HL_COL, relief=GR, bd=1)
            else:        lbl.config(bg=HDR_COL,  relief=RA, bd=1)
    # --------------------------------------------
    def _on_switch(self, key:str ,idx:int):

        if idx == 0:
            if key == "adjust": self.adjustment = True
            else:               self.adjustment = False
            self._apply_period(key)
            self._update_radio_btn_state(0, key)
        if idx == 1:
            self.grade_state[key] = not self.grade_state.get(key, False)
            if self.grade_state[key]:
                self.grade_key.extend(key)
            else: self.grade_key = [k for k in self.grade_key if k not in key]
            self._update_toggle_btn_state(idx, self.grade_state)
        if idx == 2:
            self.trend_state[key] = not self.trend_state.get(key, False)
            self._update_toggle_btn_state(idx, self.trend_state)
            self._refresh_trend_graph() ;return
        if idx == 3:   
            self.filter_state[key] = not self.filter_state.get(key, False)
            self._update_toggle_btn_state(idx, self.filter_state)
        if idx == 4:   
            self.period += ADJUST[key]
            if self.period < 0: self.period = 0
            self._apply_period("adjust")
            if  not self.adjustment: return

        self._update_rows()
        self._refresh_bar_graph()
        self._refresh_trend_graph() 
        self._refresh_players_data()
        self._refresh_series_panel()

    # --------------------------------------------
    def _on_series_btn(self, step:int):

        self.year_idx += step
        self._refresh_series_panel(read_only=True)

    # --------------- rows 更新 ------------------
    def _update_rows(self):

        opts   = {}
        for key, state in self.filter_state.items():
            if state:
                (opt, param) = self.filter_dict[key]
                opts[opt]    = param

        self.query = Query( self.date_from.isoformat(), self.date_to.isoformat(),
                                query1= True,
                                query2= True,
                             player_id= self.player_id,
                                 grade= self.grade_key,
                        exclude_rookie= [False,True],  
                                                                            **opts )
        self.data_rows  = self.query._pack(for_distribute=True)

        self._render_distribute_table()
    # ---------------------------------------------------------------
    def _apply_period(self, key:str|tuple):

        today        = date.today()
        self.date_to = today

        if isinstance(key, tuple):
            self.date_from, self.date_to = self._period_for_calc(key[0], key[1])

        elif key == "ALL":
            row = dal.fetch_one("""
                SELECT MIN(r.date)
                  FROM Races r 
                  JOIN Race_entries e 
                    ON r.race_id = e.race_id
                 WHERE e.player_id=?
                 """,
                (self.player_id,)            )

            dmin           = row[0] if row and row[0] else today
            self.date_from = self._to_date(dmin)

        elif key == "THIS":
            self.date_from = self._this_term_start(today)

        elif key == "adjust":
            m = f"{(self.period %12):2}"
            self.lb_period.config(text=f" {self.period // 12} 年 {m} ヶ月 ")
            if self.adjustment:
                self.date_from = today -relativedelta(months=self.period)
            else: return

        else: self.date_from = today -relativedelta(months=MONTH[key])

    #---------------------- 選手ﾌﾟﾛﾌｨｰﾙ 取得・更新 -------------------
    def _load_player_basic(self, player_id:int):
        # ----------
        def _date_to_career(regip:int):
            path_months   = (regip - 1) * 6
            debut_date    = date(1957, 11, 1) + relativedelta(months=path_months)
            return relativedelta(date.today(), debut_date)
        # ----------
        sql = """
            SELECT player_id, name, regist_period,
                   regions,   age,  birthplace
              FROM Players 
             WHERE player_id=?
              """
        row = dal.fetch_one(sql, (player_id,))
        if not row: return

        pid, name, regip, reg, age, birth = row
        diff   = _date_to_career(regip)
        career = f"{diff.years} 年  {diff.months} ヶ月"
        self.regist_period = regip

        self.basic_vars["name"         ].set(name.split() or "")
        self.basic_vars["player_id"    ].set(str(pid))
        self.basic_vars["regist_period"].set("" if regip is None else f"{str(regip)} 期")
        self.basic_vars["regions"      ].set(f"{reg} 支部" or "")
        self.basic_vars["age"          ].set(f"{age} 歳" if age else "")
        self.basic_vars["birthplace"   ].set(birth.split() if birth else "")
        self.basic_vars["career"       ].set(f"{career}")

    #-------------------- 直近5期適用級 取得・更新 -------------------
    def _refresh_classes(self):

        y_s = self._5seasons()

        for idx, (y, s) in enumerate(y_s):
            key = (y, s)

            row = dal.fetch_one("""
                SELECT class_in, score_ave
                  FROM Season_result
                 WHERE player_id =?
                   AND year      =?
                   AND season    =?
                """ ,
                (self.player_id, y, s))

            if row:
                txt = f"'{y % 100:02d} {'前 期' if s == 1 else '後 期'}"
                self.season[key].configure(text=txt)
                self._class[key].configure(text=row["class_in"], **CLS_COLOR[row["class_in"]])
                self.sc_ave[key].configure(text=f"{float(row["score_ave"])/100:.2f}", **NOR_COL)

    #----------------------- 選手成績ﾃﾞｰﾀ 更新 -----------------------
    def _refresh_players_data(self):
        # --------------
        def _fmt(value):
            if value == 0: return "ー"
            return f"{value:.2f}"
        # --------------
        data = self.query._pack(by_grade=True)

        for c, grade in enumerate(["ALL","SG","G1","G2","G0"], start=1):
            s = data[grade]

            if s["starts"] == 0: cells = ["-"] * len(ROW_KEYS)
            else:                cells = [      s["starts"],        s["series"],
                                           _fmt(s["sc_ave"]),  _fmt(s["st_ave"]),
                                                s["to_final"],      s["victory"],
                                                s["r1"],  s["r2"], s["r3"],
                                                s["r4"],  s["r5"], s["r6"],
                                                s["F_L"], s["S_K"],               ]

            for r, val in enumerate(cells, start=1):
                if (c in [2,3,4]) and (r == 6) and (s["victory"] >= 1):
                    self.cells[(r, c)].config(text=str(val), fg="blue", bg="white", font=(MUI,10,BD))
                else: self.cells[(r, c)].config(text=str(val), fg="black", bg="white")

    #------------------------ ｺｰｽ別ｸﾞﾗﾌ描画 --------------------------
    def _refresh_bar_graph(self):

        row = self.query._pack(by_course=True)
        lb1 = cFr(self.bar, W= 50, H=252) ;lb1._grid(R=0, C=0)
        fr  = cFr(self.bar, W=240, H=252) ;fr._grid( R=0, C=1)
        lb2 = cFr(self.bar, W= 30, H=252) ;lb2._grid(R=0, C=2)

        framing_graph(self, fr, [1,2,3,4,5,6], rows1=row, W=240, H=246)

        for ln in range(6):
            cnt     = row[ln+1]["cnt"]
            v       = row[ln+1]["st_ave"]
            label_A = f"{ln+1} コース"
            label_B = f"   / {cnt} "
            label_C = "ー" if v is None else v

            cLbl(lb1, text=label_A, anchor="w", font=(MUI,8)).place(x=0, y=ln*41)
            cLbl(lb1, text=label_B, anchor="w", font=(MUI,8,BD)).place(x=0, y=ln*41+15)
            cLbl(lb2, text=label_C, anchor="w", font=(MUI,8)).place(x=0, y=ln*41+5)

    #------------------------ 折れ線グラフ描画 -----------------------
    def _refresh_trend_graph(self):
        # ----------
        def _fixed(v:float) -> int:
            vv = 0.0 if v is None else max(0.0, min(0.5, float(v)))
            return T + YH -int((vv / 0.5) *YH)
        # ----------
        cv         = self.cv_trend_graph;  cv.delete("all")

        W, H       = 465, 260
        L, R, T, B = 23, 20, 5, 26
        XW, YH     = W -(L+R), H -(T+B)

        data    = self.query._pack(by_series=True, for_trend=True)
        n       = len(data)
        step    = XW / max(1, (n-1))
        xs      = [L + int(round(i * step)) for i in range(n)]
        ys_sr_c = [T + YH -int((min(max(d["sr_cumltv"], 0.0), 10.0)/ 10.0) * YH) for d in data]
        ys_sr_s = [T + YH -int((min(max(d["sr_single"], 0.0), 10.0)/ 10.0) * YH) for d in data]
        ys_st_c = [_fixed(d["st_cumltv"]) if d["st_cumltv"] is not None else None for d in data]
        ys_st_s = [_fixed(d["st_single"]) if d["st_single"] is not None else None for d in data]
        show_st = (self.trend_state.get("st_cumltv") or self.trend_state.get("st_single"))
        show_sr = (self.trend_state.get("sr_cumltv") or self.trend_state.get("sr_single"))
        grade   = [d["grade"] for d in data]

        cv.create_rectangle(L, T, L+XW, T+YH, outline="#a4b7cb", width=1, fill="white")

        if show_sr:                 # 右軸ﾗﾍﾞﾙ
            for yv in [0, 3.0, 5.0, 6.0, 10]:
                y = T + YH - int( (yv / 10.0) * YH )
                cv.create_text(W-R +5, y, text=f"{yv}", anchor="w", font=(GUI, 9))
                if yv == 6.0:
                    cv.create_line(L, y, XW+L, y, fill="#c1c1c1", width=1)
                if yv in [3.0, 5.0]:
                    cv.create_line(L, y, XW+L, y, fill="#dedede", width=1)
            if not data:
                cv.create_text(L+XW / 2, YH+T / 2, text="データなし", font=(MUI, 10))
                return

        if show_st:                  # 左軸ﾗﾍﾞﾙ
            for tv in [0, 0.10, 0.15, 0.20, 0.50]:
                lbl = f"{tv:.2f}"[1:] if tv != 0 else tv
                y   = _fixed(tv)
                cv.create_text(20, y, text=lbl, anchor="e", font=(GUI, 9, BD), fill=STC_COL)
                if tv not in [0, 0.5]:
                    cv.create_line(L, y, L+XW, y, fill="#b3d4ff", width=1)

        for i, d in enumerate(data):  # ﾌﾗｲﾝｸﾞ線
            if d["has_F"]:
                x = xs[i]
                cv.create_line(x, T, x, T+YH, fill="#FF2A2A", width=1)
        #-----------
        def draw_line(xs, ys, color):
            pts = [(xs[i], ys[i]) for i in range(n) if ys[i] is not None]
            for i in range(1, len(pts)):
                x1,y1 = pts[i-1] ;x2,y2 = pts[i]
                cv.create_line(x1, y1, x2, y2, fill=color, width=1)
            for i,(x,y) in enumerate(pts):
                g = grade[i]
                cv.create_oval(x-1.5, y-1.5, x+1.5, y+1.5, fill=G_COL[g], outline="")
        #-----------
        if self.trend_state.get("sr_cumltv"): draw_line(xs, ys_sr_c, SRC_COL)
        if self.trend_state.get("sr_single"): draw_line(xs, ys_sr_s, SRS_COL)
        if self.trend_state.get("st_cumltv") and any(v is not None for v in ys_st_c):
            draw_line(xs, ys_st_c, STR_COL)
        if self.trend_state.get("st_single") and any(v is not None for v in ys_st_s):
            draw_line(xs, ys_st_s, STC_COL)

        # X目盛(節番号)
        for i, x in enumerate(xs, 1):
            cv.create_text(x, T+YH+5, text=str(i), anchor="n", font=(GUI, 8))

    #------------------------- series_panel --------------------------
    def _apply_series_year_state(self):

        if self.s_years: self.lbl_y_disp.config(text=f"{self.s_years[self.year_idx]} 年")
        else:            self.lbl_y_disp.config(text="----")

        if self.year_idx < len(self.s_years) -1: self.btn_y_prev.config(state="normal",  bg="white")
        else:                                    self.btn_y_prev.config(state="disable", bg="SystemButtonFace")
        if self.year_idx >= 1:                   self.btn_y_next.config(state="normal",  bg="white")
        else:                                    self.btn_y_next.config(state="disable", bg="SystemButtonFace")

    #-----------------------  節間成績 更新 --------------------------
    def _refresh_series_panel(self, read_only:bool= False):

        for w in self.body.winfo_children(): w.destroy()

        if not read_only:
            self.s_years     = []
            self.year_idx    = 0
            self.series_rows = self.query._pack(by_series=True, for_index=True)
            if not self.series_rows:
                self.canvs.configure(scrollregion=self.canvs.bbox("all")) ; return

            for year in reversed(self.series_rows.keys()): self.s_years.append(year)

            active_year = self.s_years[0]
        else: active_year = self.s_years[self.year_idx]

        self._apply_series_year_state()

        for year in self.series_rows.keys():
            if year == active_year: row = self.series_rows[year]

        for r, seri in enumerate(reversed(row.values())):
            d_min, d_max, title, grade, _, slots = seri.values()

            fr_grid  = cFr(self.body, W=352, H= 145, Bd=(1,SD))
            fr_term  = cFr(fr_grid,   W=350, H=  37, bg="white")
            fr_grde  = cFr(fr_grid,   W= 50, H=  22, Bd=(1,RD))
            fr_titl  = cFr(fr_grid,   W=300, H=  22, bg="white")

            fr_grid._grid(R=r, C=0,           Stk=ALL) ; fr_grid.Pgate()
            fr_term._grid(R=0, C=0, Cspan=14, Stk=ALL) ; fr_term.Pgate()
            fr_grde._grid(R=1, C=0, Cspan= 2, Stk=ALL) ; fr_grde.Pgate()
            fr_titl._grid(R=1, C=2, Cspan=12, Stk=ALL) ; fr_titl.Pgate()

            fr_grde.Rconf(0, W=1) ; fr_grde.Cconf(0, W=1)
            fr_term.Rconf(0, W=1) ; fr_term.Cconf(0, W=1)
            fr_titl.Rconf(0, W=1) ; fr_titl.Cconf(0, W=1)

            term  = f"{self._jp_date(d_min, md=True)}  ～  {self._jp_date(d_max, md=True)}"

            cLbl(fr_grde, **GOPT[grade], Anc= CT)._grid(R=0, C=0, Stk=ALL)
            cLbl( fr_term, text=term,  Anc="w", bg="white", font=(MUI,9)
                 )._grid(R=0, C=0, px=(10,0), py=(12,3), Stk=ALL)
            cLbl( fr_titl, text=title, Anc="w", bg="white", font=(GUI,9)
                 )._grid(R=0, C=0, px=(20,0), Stk=ALL)

            for col, item in enumerate(slots):
                frn   = item["fr_no"]
                cour  = item["cour"]
                slit  = f"{item['s_adj']:.2f}"[1:] if item['s_adj'] else ""
                rank  = item["finish"] if not item["is_fnl"] else FINAL_RNK[item["finish"]]
                fcolr = ("red" if rank in ("F","L","S","K","(F)","(L)","(S)","(K)") else "black")
                bg    = HL_COL if cour == self.course else "white"
                opt   = { 0: dict(text=cour, **FRM_COLOR[frn],     font=(GUI, 9,BD) ),
                          1: dict(text=slit, fg=fcolr, bg="white", font=(MUI, 8   ) ),
                          2: dict(text=rank, fg=fcolr, bg=bg,      font=(GUI,10,BD) ), }

                if item["is_fnl"]: opt[2]["font"] = (GUI,11,BD)

                for row in range(3):
                    fr_cell = cFr(fr_grid, bg=bg if row == 2 else "white", W=25, H=28, Bd=(1,GR))
                    fr_cell._grid(R=row+2, C=col, Stk=ALL) ;fr_cell.Pgate()
                    fr_cell.Rconf(row, W=1) ;fr_cell.Cconf(0, W=1)

                    cLbl(fr_cell, **opt[row], anc=CT)._grid(R=0, C=0, Stk=ALL)

        self.canvs.configure(scrollregion= self.canvs.bbox("all"))

    #------------------------- 分布図 描画 ---------------------------
    def _build_distribute_ui(self):

        for w in self.win.winfo_children(): w.destroy()

        fr_left  = cFr(self.win, W=530, H=250)
        fr_right = cFr(self.win, W=380, H=250)

        fr_left._grid( R=0, C=0, py=(20,0))  ;fr_left.Pgate()
        fr_right._grid(R=0, C=1, py=(22,0)) ;fr_right.Pgate()

        self.dist_refs = {   "fr_left": fr_left, "fr_right": fr_right,
                            "rank_btn": {}, "cells": {}, "move_cells": {},
                          "course_btn": {},
                           "move_cols": [ ("逃げ",       "逃げ"),
                                          ("差し",       "差し"),
                                          ("まくり差し", "まくり差し"),
                                          ("まくり",     "まくり"),
                                          ("抜き",       "抜き"),
                                          ("恵まれ",     "恵まれ"),    ],  }

        self.totl = cLbl(fr_left, text="", width=8, font=(MUI,9,BD), bg="#cce8ff", Bd=(1,GR))
        self.totl._grid(R=0, C=0, px=1, py=1, Stk=ALL)
        self.totl.bind("<Button-1>",lambda e:self._change_disp())

        for rk in range(1, 7):
            rbtn = ttk.Button( fr_left, text=f"{rk} 着", width=9, style="r.TButton",
                               command=lambda _rk=rk: self._toggle_subject_rank(_rk) )
            rbtn.grid(row=0, column=rk, padx=1, pady=1, sticky=tk.NSEW)
            self.dist_refs["rank_btn"][rk] = rbtn

        for c in range(1, 7):
            cbtn = ttk.Button( fr_left, text=f"{c}コース", width=7, style="r.TButton",
                               command=lambda _c=c:self._on_subject_course_btn(_c)   )
            cbtn.grid(row=c, column=0, padx=(0, 1), pady=0, sticky=tk.NSEW)
            self.dist_refs["course_btn"][c] = cbtn

            for rk in range(1, 7):
                cell = cLbl(fr_left, text="", width=9, Bd=(1,RD), Anc="e", py=6)
                cell._grid(R=c, C=rk, Stk=ALL)
                self.dist_refs["cells"][(c, rk)] = cell

        for j, (label, keys) in enumerate(self.dist_refs["move_cols"]):
            cLbl(fr_right, text=label, py=4, font=(MUI,8), Bd=(1,RD), bg=HDR_COL, Anc=CT
                 )._grid(R=0, C=j, py=(0,2), Stk=ALL)

        for r in range(1, 7):
            for c, (label, keys) in enumerate(self.dist_refs["move_cols"]):
                bg ="#e9e6e6" if r >=2 and c == 0 else "white"
                cell = cLbl(fr_right, text="", W=6, py=2, Bd=(1,RD), Anc=CT, bg=bg)
                cell._grid(R=r, C=c, Stk=ALL)
                self.dist_refs["move_cells"][(r, label)] = cell

        self._render_distribute_table()

    #-----------------------------------------------------------------
    def _render_distribute_table(self):

        if not getattr(self, "dist_refs", None): return
        if not getattr(self, "data_rows", None): return

        subj_c  = self.course
        subj_r  = self.rank
        own_cnt = self.data_rows["own_cnt"]
        oth_cnt = self.data_rows["oth_cnt"]
        oth_by  = self.data_rows["oth_by_r"]
        mv_all  = self.data_rows["win_move"]
        starts  = self.data_rows["starts"]

        for c, b in self.dist_refs["course_btn"].items():
            if subj_c == c: b.state(["pressed"])
            else:           b.state(["!pressed"])

        for rk, b in self.dist_refs["rank_btn"].items():
            if subj_r == rk: b.state(["pressed"])
            else:            b.state(["!pressed"])

        total = own_cnt[subj_c][subj_r] if subj_r else starts[subj_c]
        self.totl.configure(text=f"{total}")

        for c in range(1, 7):
            vt = 0
            for rk in range(1, 7):
                cell = self.dist_refs["cells"][(c, rk)]

                if   rk == 1: bg="white"   ;f=(MUI,8,BD)
                elif rk <= 3: bg="white"   ;f=(MUI,8)
                else:         bg="#e9e6e6" ;f=(MUI,8)

                if c  == subj_c and ((subj_r == 0) or (subj_r != 0 and rk == subj_r)):
                    bg = "#cce8ff"
                    v  = own_cnt[subj_c][rk]
                else:
                    if subj_r == 0: v = oth_cnt[subj_c][c][rk]
                    else:           v = oth_by[subj_c][subj_r][c][rk]
                vt += v
                if v: text = f"{v}  " if self.disp else f"{(vt / total *100):.1f} % "
                else: text = ""
                cell.configure(text=text, bg=bg, font=f)

        if subj_r in range(1, 7): win_move = self.data_rows["subj_wm"][subj_c][subj_r] or None
        else:                     win_move = mv_all.get(subj_c, None)

        if win_move is None: win_move = {c:{} for c in range(1, 7)}

        for c in range(1, 7):
            wmvs = win_move.get(c, {})
            for col, (label, key) in enumerate(self.dist_refs["move_cols"]):
                if c >= 2 and col == 0: continue
                lb_wm = self.dist_refs["move_cells"][(c, label)]
                cnt   = wmvs.get(key, 0)

                lb_wm.config(text=cnt if cnt else "", bg="white", **NMFNT)
                if col >= 4:      lb_wm.config(bg="#e9e6e6"         )
                if c   == subj_c: lb_wm.config(bg="#cce8ff", **BDFNT)

    #-----------------------------------
    def _change_disp(self):
        if self.disp == 1: self.disp = 0
        else: self.disp = 1
        self._render_distribute_table()
    #-----------------------------------
    def _on_subject_course_btn(self, c:int):
        self.course = c
        self._render_distribute_table()
    #-----------------------------------
    def _toggle_subject_rank(self, rk: int):
        if self.rank == rk: self.rank = 0
        else:               self.rank = rk
        self._render_distribute_table()
    #-----------------------------------
    @staticmethod
    def _this_term_start(today:date) -> date:

        if 5 <= today.month <= 10: return date(today.year,  5, 1)
        if      today.month >= 11: return date(today.year, 11, 1)

        return date(today.year-1, 11, 1)
    #-----------------------------------
    @staticmethod
    def _add_months(d:date, n:int) -> date:

        y    = d.year + (d.month-1 + n)//12
        m    =          (d.month-1 + n) %12 +1
        last = (date(y + (m==12), (m%12) +1, 1) - timedelta(days=1)).day

        return date(y, m, min(d.day, last))
    #-----------------------------------
    @staticmethod
    def _to_date(x) -> date:

        if isinstance(x, date): return x
        if isinstance(x,  str): return date.fromisoformat(x)

        raise ValueError("date conv error")
    #-----------------------------------
    def _jp_date(self, d:date, md:bool=False) -> str:

        d = self._to_date(d)
        if md: return wid_txt(f"{d.month}月 {d.day}日")
        else:  return wid_txt(f"{d.year}年  {d.month}月 {d.day}日")
    #-----------------------------------
    @staticmethod
    def _period_for_calc(year:str, season:int):

        if season == 1: d_frm = f"{year -1}-05-01" ; d_to = f"{year -1}-10-31"
        if season == 2: d_frm = f"{year -1}-11-01" ; d_to = f"{year   }-04-30"

        return date.fromisoformat(d_frm), date.fromisoformat(d_to)
    # ----------------------------------
    def _5seasons(self):

        today = date.today()
        y = int(today.year)
        s = (1 if 1 <= today.month <= 6 else 2)
        if s == 1: y_s = [ (y, 1), (y-1, 2), (y-1, 1), (y-2, 2), (y-2, 1) ]
        else:      y_s = [ (y, 2), (y,   1), (y-1, 2), (y-1, 1), (y-2, 2) ]

        return y_s
    # ----------------------------------
    def _same_period(self):
        PlayerSamePeriodScreen(self, self.regist_period)

    # 外部から選手切替--------------------------------------
    def set_player(self, player_id:int, venue_id:int= None):

        self.player_id = player_id
        self.venue_id  = venue_id


