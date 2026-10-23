# -*- coding: utf-8 -*-
# C:\boatrace\UI\Placeholder\placeholder.py

import tkinter as tk
from Helpers.Custum_func import cFr, cLbl, cBtn, cCvs
from Widgets.widgets     import framing_graph, framing_figure

GUI, MUI, HNH, CBR     = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, SK, BD = "groove", "solid", "ridge", "raised", "sunken", "bold"
ALL, CT                = "nsew", "center"

WATER_COL = "#A5E6FF"
BLANK_COL = "#E9F1F2"
PANNEL  = "#4A6EA4"

MAIN_BG = "#F0F4FA"
HDR_BG  = "#2B4A7A"
BTN_BG  = "#4A6A9A"
WHITE   = "#FFFFFF"
YELL1   = "#FFD700"
YELL2   = "#F1EE62"
GRAY1   = "#ECECEC"
GRAY2   = "#CFCFCF"
BLACK1  = "#000000"
BLACK2  = "#222222"
BLUE    = "#ff7474"
LIT_RED = "#ff5b5b"

HDR_B   = dict(bg=HDR_BG)
BTN_B   = dict(bg=BTN_BG)
HDR_BF  = dict(bg=HDR_BG, fg=WHITE)
BTN_BF  = dict(bg=BTN_BG, fg=WHITE)
YEL2_BF = dict(bg=YELL2,  fg=BLACK2)
HDR_7   = dict(bg=HDR_BG, fg="#8bbfff", font=(MUI,8,BD))
HDR_8   = dict(bg=HDR_BG, fg=WHITE, font=(MUI,8,BD), Bd=(1,GR))
BTN_OFF = dict(bg=BTN_BG, fg=WHITE,  Bd=(1,RA))
GRY_OFF = dict(bg=GRAY1,  fg=BLACK1, Bd=(1,RA))
YEL1_ON = dict(bg=YELL1,  fg=BLACK2, Bd=(1,GR))
YEL2_ON = dict(bg=YELL2,  fg=BLACK2, Bd=(1,SK))
HDR_GR  = dict(bg=HDR_BG, Bd=(1,GR))
HL_YEL  = dict(bg="#F1EE62", fg="black")
HL_GRN  = dict(bg="#DBFBD1", fg="black")
HL_ORN  = dict(bg="#FFDCAC", fg="black")

# ==================== プレースホルダ(Main) ======================
# ----------------------------------------------------------------
def build_main_placeholder(self, parent:tk.Frame):

    for ln in range(1, 7):
        row  = (ln -1)
        Lane = cFr(parent, W=1200, H=167) ;Lane._grid(R=row, C=0) ;Lane.Pgate()

        Lane.Cconf(0, W=0, minsize= 413)
        Lane.Cconf(1, W=1, minsize= 358)
        Lane.Cconf(2, W=0, minsize= 433)
        Lane.Rconf(0, W=1)

        # left: 選手基本データ =========
        fr_left = cFr(Lane,   W=409, H=167, Bd=(1,SD)) ;fr_left.place(x=0, y=0) ;fr_left.Pgate()

        fr_A   = cFr(fr_left, W= 22, H=165, Bd=(1,GR)) ;fr_A._grid(  R=0, C=0) ;fr_A.Pgate()
        fr_B   = cFr(fr_left, W=112, H=165, Bd=(1,GR)) ;fr_B._grid(  R=0, C=1) ;fr_B.Pgate()
        fr_C   = cFr(fr_left, W=182, H=165, Bd=(1,GR)) ;fr_C._grid(  R=0, C=2) ;fr_C.Pgate()
        fr_D   = cFr(fr_left, W= 46, H=165           ) ;fr_D._grid(  R=0, C=3) ;fr_D.Pgate()
        fr_E   = cFr(fr_left, W= 45, H=165           ) ;fr_E._grid(  R=0, C=4) ;fr_E.Pgate()
        fr_C1  = cFr(fr_C,    W=182, H= 32, Bd=(1,GR)) ;fr_C1._grid( R=0, C=0) ;fr_C1.Pgate()
        fr_C2  = cFr(fr_C,    W=182, H=133, Bd=(1,GR)) ;fr_C2._grid( R=1, C=0) ;fr_C2.Pgate()
        fr_D1  = cFr(fr_D,    W= 46, H= 33, Bd=(1,GR)) ;fr_D1._grid( R=0, C=0) ;fr_D1.Pgate()
        fr_D2  = cFr(fr_D,    W= 46, H= 33, Bd=(1,GR)) ;fr_D2._grid( R=1, C=0) ;fr_D2.Pgate()
        fr_D3  = cFr(fr_D,    W= 46, H= 33, Bd=(1,GR)) ;fr_D3._grid( R=2, C=0) ;fr_D3.Pgate()
        fr_D4  = cFr(fr_D,    W= 46, H= 33, Bd=(1,GR)) ;fr_D4._grid( R=3, C=0) ;fr_D4.Pgate()
        fr_D5  = cFr(fr_D,    W= 46, H= 33, Bd=(1,GR)) ;fr_D5._grid( R=4, C=0) ;fr_D5.Pgate()
        fr_E1  = cFr(fr_E,    W= 45, H= 33, Bd=(1,GR)) ;fr_E1._grid( R=0, C=0) ;fr_E1.Pgate()
        fr_E2  = cFr(fr_E,    W= 45, H= 33, Bd=(1,GR)) ;fr_E2._grid( R=1, C=0) ;fr_E2.Pgate()
        fr_E3  = cFr(fr_E,    W= 45, H= 33, Bd=(1,GR)) ;fr_E3._grid( R=2, C=0) ;fr_E3.Pgate()
        fr_E4  = cFr(fr_E,    W= 45, H= 33, Bd=(1,GR)) ;fr_E4._grid( R=3, C=0) ;fr_E4.Pgate()
        fr_E5  = cFr(fr_E,    W= 45, H= 33, Bd=(1,GR)) ;fr_E5._grid( R=4, C=0) ;fr_E5.Pgate()

        fr_A.Rconf( 0, W=1) ;fr_A.Cconf( 0, W=1)
        fr_B.Rconf( 0, W=1) ;fr_B.Cconf( 0, W=1)  
        fr_C1.Rconf(0, W=1) ;fr_C1.Cconf(0, W=1)
        fr_C2.Rconf(0, W=1) ;fr_C2.Cconf(0, W=1)
        fr_D1.Rconf(0, W=1) ;fr_D1.Cconf(0, W=1)
        fr_D2.Rconf(0, W=1) ;fr_D2.Cconf(0, W=1)
        fr_D3.Rconf(0, W=1) ;fr_D3.Cconf(0, W=1)
        fr_D4.Rconf(0, W=1)
        fr_D4.Cconf(0, W=1) ;fr_D4.Cconf(1, W=1)
        fr_D5.Rconf(0, W=1) ;fr_D5.Cconf(0, W=1)
        fr_E1.Rconf(0, W=1) ;fr_E1.Cconf(0, W=1)
        fr_E2.Rconf(0, W=1) ;fr_E2.Cconf(0, W=1)
        fr_E3.Rconf(0, W=1) ;fr_E3.Cconf(0, W=1)
        fr_E4.Rconf(0, W=1) ;fr_E4.Cconf(0, W=1)
        fr_E5.Rconf(0, W=1) ;fr_E5.Cconf(0, W=1)

        lb_frno  = cLbl(fr_A,  Anc=CT, font=(GUI,13,  )            )
        lb_photo = cLbl(fr_B,  cursor="hand2"                      )
        lb_name  = cLbl(fr_C2, Anc=CT, font=(GUI,13,BD), bg="white")
        lb_rate1 = cLbl(fr_D1, Anc=CT, font=(MUI, 8,BD), bg="white")
        lb_rate2 = cLbl(fr_D2, Anc=CT, font=(MUI, 8,BD), bg="white")
        lb_rate3 = cLbl(fr_D3, Anc=CT, font=(MUI, 8,BD), bg="white")
        lb_late  = cLbl(fr_D4, Anc=CT, font=(GUI, 7   ), bg="white")
        lb_flyg  = cLbl(fr_D4, Anc="w",font=(MUI, 7,  ), bg="white")
        lb_stav  = cLbl(fr_D5, Anc=CT, font=(MUI, 8,BD), bg="white")
        lb_mo_av = cLbl(fr_E4, Anc=CT, font=(MUI, 8,BD), bg="white", Csr="hand2")
        lb_bo_av = cLbl(fr_E5, Anc=CT, font=(MUI, 8   ), bg="white")

        cv1 = cCvs(fr_C1, W=182, H=32, **HDR_B,    HLth=0) ;cv1.place(x=0, y= 0)
        cv2 = cCvs(fr_C2, W=182, H=30, bg="white", HLth=0) ;cv2.place(x=0, y= 0)
        cv3 = cCvs(fr_C2, W=182, H=30, bg="white", HLth=0) ;cv3.place(x=0, y=94)

        lb_frno._grid(  Stk=ALL                      )
        lb_photo._grid( Stk=ALL                      )
        lb_name._grid(  Stk=ALL                      )
        lb_rate1._grid( Stk=ALL                      )
        lb_rate2._grid( Stk=ALL                      )
        lb_rate3._grid( Stk=ALL                      )
        lb_late._grid(  Stk=ALL, R=0, C=0, pady=(1,0))
        lb_flyg._grid(  Stk=ALL, R=0, C=1, pady=(1,0))
        lb_stav._grid(  Stk=ALL,                     )
        lb_mo_av._grid( Stk=ALL, R=0, C=0            )
        lb_bo_av._grid( Stk=ALL, R=0, C=0            )

        # center: center_widgets =======

        fr_center = cFr(Lane, W=358, H=167, Bd=(1,SD))
        fr_center.place(x=408, y=0) ;fr_center.Pgate()

        self.widgets_main[ln] = { "Lane":Lane, "absent_fr":fr_C2,
           "frno":lb_frno,    "name":lb_name,  "photo":lb_photo,  "stav":lb_stav,
           "late":lb_late,    "flyg":lb_flyg,  "mo_av":lb_mo_av, "bo_av":lb_bo_av,
          "rate1":lb_rate1,  "rate2":lb_rate2, "rate3":lb_rate3,     
            "cv1":cv1,         "cv2":cv2,        "cv3":cv3,     "fr_Ctr":fr_center, }

        # right: 節間成績/2走ｲﾝﾃﾞｯｸｽ ===

        R_hdr:list[tk.Label]       = []
        R_bdy:list[list[tk.Label]] = []
        R_idx:list[tk.Label]       = []

        fr_right = cFr(Lane, W=435, H=167, Bd=(1,SD))
        fr_right.place(x=764, y=0) ;fr_right.Pgate()

        fr_right.Rconf(0, Min=29)
        fr_right.Rconf(1, Min=29)
        fr_right.Rconf(2, Min=33)
        fr_right.Rconf(3, Min=37)
        fr_right.Rconf(4, Min=37)
        for c in range(14): fr_right.Cconf(c, Min=29)
        fr_right.Cconf(14, Min=27)

        for i in range(7):
            hedr = cLbl(fr_right, text="", font=(GUI,8,BD), bg=BLANK_COL, Bd=(1,RD))
            hedr._grid(R=0, C=i*2, Cspan=2, Stk=ALL) ;hedr.Pgate()
            R_hdr.append(hedr)

        for col in range(14):
            cells = []
            for row in range(1, 5):
                pad = dict(px=(1,1), py=(3,3)) if row == 2 else dict(px=(0,0), py=(0,0))
                cell = cLbl(fr_right, text="", bg=MAIN_BG, Bd=(1,GR), Anc=CT)
                cell._grid(R=row, C=col, Stk=ALL) ;cell.Pgate()
                cells.append(cell)
            R_bdy.append(cells)

        fr_idx = cFr(fr_right, W=27, H=93, Bd=(1,RD), **HDR_B, py=30)
        fr_idx._grid(R=0, C=14, Rspan=5, Stk=ALL) ;fr_idx.Pgate()

        for r in range(3):
            fr_idx.Rconf(r, Min=31)
            inr = cLbl(fr_idx, text="", **HDR_7, py=1)
            inr._grid(R=r, C=0, Stk=ALL, px=(3,0), py=4) ;inr.Pgate()
            R_idx.append(inr)
        fr_idx.Cconf(0, Min=24)

        self.widgets_idx[ln] = {"R_hdr":R_hdr, "R_bdy":R_bdy, "R_idx":R_idx}

# ==================== プレースホルダ(Sub) =======================
# ----------------------------------------------------------------
def build_sub_placeholder(self, parent:tk.Frame): #  1188  318
    #---------------
    def reset_figure():
        if hasattr(fr_figA, "reset_figure"):
            fr_figA.reset_figure()
    #---------------
    self.s_lane = 0

    fr_Hedr  = cFr(parent, W=1200, H= 50)
    fr_body  = cFr(parent, W=1200, H=266)
    fr_Hedr._grid(R=0, C=0, pady=(0,2)) ;fr_Hedr.Pgate()
    fr_body._grid(R=2, C=0            ) ;fr_body.Pgate()

    # Frame header================================
    fr_hdrL  = cFr(fr_Hedr, W=913, H= 50, Bd=(1,SD))
    fr_hdrR  = cFr(fr_Hedr, W=280, H= 50, Bd=(1,SD))

    fr_hdrL._grid(R=0, C=0, px=(0, 5)) ;fr_hdrL.Pgate()
    fr_hdrR._grid(R=0, C=1)            ;fr_hdrL.Pgate()

    fr_venu = cFr(fr_hdrL, W= 80, H= 48           ) ;fr_venu._grid(R=0, C=0) ;fr_venu.Pgate()
    fr_updt = cFr(fr_hdrL, W=140, H= 48, **HDR_B  ) ;fr_updt._grid(R=0, C=1) ;fr_updt.Pgate()
    fr_clok = cFr(fr_hdrL, W=115, H= 48, **HDR_B  ) ;fr_clok._grid(R=0, C=2) ;fr_clok.Pgate()
    fr_last = cFr(fr_hdrL, W= 75, H= 48, **HDR_B  ) ;fr_last._grid(R=0, C=3) ;fr_last.Pgate()
    fr_pnel = cFr(fr_hdrL, W=501, H= 48           ) ;fr_pnel._grid(R=0, C=4) ;fr_pnel.Pgate()

    fr_btnf = cFr(fr_hdrR, W= 74, H= 48, **HDR_B  ) ;fr_btnf._grid(R=0, C=0) ;fr_btnf.Pgate()
    fr_wthr = cFr(fr_hdrR, W= 69, H= 48, **HDR_B  ) ;fr_wthr._grid(R=0, C=1) ;fr_wthr.Pgate()
    fr_para = cFr(fr_hdrR, W= 80, H= 48, **HDR_B  ) ;fr_para._grid(R=0, C=2) ;fr_para.Pgate()
    fr_wdir = cFr(fr_hdrR, W= 55, H= 48, **HDR_B  ) ;fr_wdir._grid(R=0, C=3) ;fr_wdir.Pgate()

    fr_pnlA = cFr(fr_pnel, W=503, H= 24, **HDR_B   );fr_pnlA._grid(R=0, C=0) ;fr_pnlA.Pgate()
    fr_pnlB = cFr(fr_pnel, W=503, H= 24, **HDR_B   );fr_pnlB._grid(R=1, C=0) ;fr_pnlB.Pgate()

    self.bt_ctw = cFr(fr_pnlA, W=353, H= 24, **HDR_B ) ;self.bt_ctw._grid(R=0, C=0)
    fr_info     = cFr(fr_pnlA, W=150, H= 24, **HDR_B ) ;fr_info._grid(R=0, C=1) ;fr_info.Pgate()

    fr_venu.Rconf(0, Min=48) ;fr_venu.Cconf(0, Min=80)
    fr_updt.Rconf(0, Min=24) ;fr_updt.Cconf(0, Min=85)
    fr_updt.Rconf(1, Min=24) ;fr_updt.Cconf(1, Min=55)
    fr_clok.Rconf(0, Min=24) ;fr_clok.Cconf(0, Min=40)
    fr_clok.Rconf(1, Min=24) ;fr_clok.Cconf(1, Min=75)
    fr_last.Rconf(0, Min=48) ;fr_last.Cconf(0, Min=75)

    fr_info.Rconf(0, Min=24)
    fr_info.Cconf(1, Min=75) ;fr_info.Cconf(0, Min=75)

    fr_btnf.Rconf(0, Min=24) ;fr_btnf.Cconf(0, Min=74)
    fr_btnf.Rconf(1, Min=24)
    fr_wthr.Rconf(0, Min=48) ;fr_wthr.Cconf(0, Min=69)
    fr_para.Rconf(0, Min=24) ;fr_para.Cconf(0, Min=80)
    fr_para.Rconf(1, Min=24)
    fr_wdir.Rconf(0, Min=48) ;fr_wdir.Cconf(0, Min=55)

    lb_venue = cLbl(fr_venu, font=(MUI,9,BD), fg="yellow", **HDR_B, Bd=(2,RA), Csr="hand2", Wrap=70, py=2)
    lb_venue.bind("<Button-1>",lambda e:self.app.open_v_analys(self.venue_id))
    lb_venue._grid(R=0, C=0, Stk=ALL)

    cLbl(fr_updt, text="モーター更新後", **HDR_7)._grid(R=0, C=0, Stk=ALL, px=(0,0), py=(2,0))
    cLbl(fr_updt, text=" ボート 更新後", **HDR_7)._grid(R=1, C=0, Stk=ALL, px=(3,0), py=(0,3))
    lb_upd_m = cLbl(fr_updt, **HDR_8)   ;lb_upd_m._grid(R=0, C=1, Stk=ALL, px=(0,5), py=(2,0))
    lb_upd_b = cLbl(fr_updt, **HDR_8)   ;lb_upd_b._grid(R=1, C=1, Stk=ALL, px=(0,5), py=(0,2))
    cLbl(fr_clok, text="締 切",          **HDR_7)._grid(R=0, C=0, Stk=ALL, px=(8,0), py=(2,2))
    cLbl(fr_clok, text="現 在",          **HDR_7)._grid(R=1, C=0, Stk=ALL, px=(8,0), py=(0,4))
    lb_deadl = cLbl(fr_clok, **HDR_8)   ;lb_deadl._grid(R=0, C=1, Stk=ALL, px=(3,0), py=(2,0))
    lb_now   = cLbl(fr_clok, **HDR_8)   ;lb_now._grid(  R=1, C=1, Stk=ALL, px=(3,0), py=(0,2))

    lb_last  = cLbl(fr_last, Anc=CT, font=(GUI,10), bg="#142e43", fg=WHITE, Bd=(2,SK))
    lb_last._grid( R=0, C=0, Stk=ALL, px=5, py=8)

    lb_stab = cLbl(fr_info, font=(MUI,8), Bd=(2,SK)) ;lb_stab._grid(R=0, C=0, Stk=ALL, py=1)
    lb_shlp = cLbl(fr_info, font=(MUI,8), Bd=(2,SK)) ;lb_shlp._grid(R=0, C=1, Stk=ALL, px=2, py=1)

    self.bt_befr = cBtn(fr_btnf, W=5, text=f"展 示", font=(MUI,8,BD), Csr="hand2")
    self.bt_rslt = cBtn(fr_btnf, W=5, text=f"結 果", font=(MUI,8,BD), Csr="hand2") 
    self.bt_befr._config(Com=lambda:_toggle_btn(self, "figB_result", False))
    self.bt_rslt._config(Com=lambda:_toggle_btn(self, "figB_result", True ))
    self.bt_befr._grid(R=0, C=0, Stk=ALL, px=(1,5), py=(1,1))
    self.bt_rslt._grid(R=1, C=0, Stk=ALL, px=(1,5), py=(1,1))
    lb_wspd = cLbl(fr_para, font=(MUI,8,BD), **HDR_BF) ;lb_wspd._grid(R=0, C=0, Stk=ALL)
    lb_wave = cLbl(fr_para, font=(MUI,8,BD), **HDR_BF) ;lb_wave._grid(R=1, C=0, Stk=ALL, py=(0,3))

    self.bt_rst = cBtn(fr_pnlB, W= 7, font=(MUI,8,BD), Csr="hand2", text="Reset", Bd=(1,RA), bg="#bbe0fc")
    self.bt_fly = cBtn(fr_pnlB, W= 6, font=(MUI,8,BD), Csr="hand2", text="Flying")
    self.bt_nfl = cBtn(fr_pnlB, W= 7, font=(MUI,8,BD), Csr="hand2", text="! Flying")
    self.bt_exE = cBtn(fr_pnlB, W= 9, font=(GUI,8,BD), Csr="hand2", text="江戸川除外", py=3)
    self.bt_grd = cBtn(fr_pnlB, W= 8, font=(MUI,8,BD), Csr="hand2", text="一般戦除外")
    self.bt_mrk = cBtn(fr_pnlB, W= 7, font=(MUI,8,BD), Csr="hand2", text="全 マーク")
    self.bt_ort = cBtn(fr_pnlB, W= 9, font=(GUI,8,BD), Csr="hand2", text="オ リ 展")
    self.bt_prt = cBtn(fr_pnlB, W= 9, font=(GUI,8,BD), Csr="hand2", text="交換 部品")

    self.bt_rst.config(command=reset_figure)
    self.bt_fly.config(command=lambda:_switch_btn(self, self.bt_fly, "flying"))
    self.bt_nfl.config(command=lambda:_switch_btn(self, self.bt_nfl, "not_flying"))
    self.bt_exE.config(command=lambda:_switch_btn(self, self.bt_exE, "exclude_edo"))
    self.bt_grd.config(command=lambda:_switch_btn(self, self.bt_grd, "limited_grade"))
    self.bt_mrk.config(command=lambda:_switch_btn(self, self.bt_mrk, "on_mark"))
    self.bt_ort.config(command=lambda:_toggle_btn(self, "disp_oriten", True )) 
    self.bt_prt.config(command=lambda:_toggle_btn(self, "disp_oriten", False))

    self.bt_rst._grid(R=0, C=0, Stk=ALL, py=(0,2))
    self.bt_fly._grid(R=0, C=1, Stk=ALL, py=(0,2), px=(5,0))
    self.bt_nfl._grid(R=0, C=2, Stk=ALL, py=(0,2))
    self.bt_exE._grid(R=0, C=3, Stk=ALL, py=(0,2))
    self.bt_grd._grid(R=0, C=4, Stk=ALL, py=(0,2))
    self.bt_mrk._grid(R=0, C=5, Stk=ALL, py=(0,2), px=(0,10))
    self.bt_ort._grid(R=0, C=6, Stk=ALL, py=(0,2))
    self.bt_prt._grid(R=0, C=7, Stk=ALL, py=(0,2))

    _config_btn(self, self.flying,        self.bt_fly, None, (1,GR), HL_GRN)
    _config_btn(self, self.not_flying,    self.bt_nfl, None, (1,GR), HL_GRN)
    _config_btn(self, self.exclude_edo,   self.bt_exE, None, (1,GR), HL_GRN)
    _config_btn(self, self.limited_grade, self.bt_grd, None, (1,GR), HL_GRN)
    _config_btn(self, self.on_mark,       self.bt_mrk, None, (1,GR), HL_GRN)
    _config_btn(self, self.disp_oriten, self.bt_ort,  self.bt_prt,  (1,SK), HL_ORN)
    _config_btn(self, self.figB_result, self.bt_rslt, self.bt_befr, (1,SK), YEL2_BF)

    # Frame body==================================
    fr_Lane = cFr(fr_body, W=913, H=266, Bd=(1,SD)) ;fr_Lane._grid(R=0, C=0)           ;fr_Lane.Pgate()
    fr_Rigt = cFr(fr_body, W=280, H=266, Bd=(1,SD)) ;fr_Rigt._grid(R=0, C=3, px=(6,0)) ;fr_Rigt.Pgate()

    fr_lanA = cFr(fr_Lane, W= 23, H=264)           ; fr_lanA._grid(R=0, C=0) ;fr_lanA.Pgate()
    fr_lanB = cFr(fr_Lane, W=140, H=264)           ; fr_lanB._grid(R=0, C=1) ;fr_lanB.Pgate()
    fr_lanC = cFr(fr_Lane, W= 20, H=264)           ; fr_lanC._grid(R=0, C=2) ;fr_lanC.Pgate()
    fr_lanD = cFr(fr_Lane, W= 34, H=264)           ; fr_lanD._grid(R=0, C=3) ;fr_lanD.Pgate()
    fr_lanE = cFr(fr_Lane, W=254, H=264)           ; fr_lanE._grid(R=0, C=4) ;fr_lanE.Pgate()
    fr_botn = cFr(fr_Lane, W= 21, H=264, **HDR_B)  ; fr_botn._grid(R=0, C=5) ;fr_botn.Pgate()
    fr_grph = cFr(fr_Lane, W=246, H=264)           ; fr_grph._grid(R=0, C=6) ;fr_grph.Pgate()
    fr_lanF = cFr(fr_Lane, W= 29, H=264)           ; fr_lanF._grid(R=0, C=7) ;fr_lanF.Pgate()
    fr_lanG = cFr(fr_Lane, W=143, H=264)           ; fr_lanG._grid(R=0, C=8) ;fr_lanG.Pgate()
    fr_figA = cFr(fr_lanE, W=254, H=264)           ; fr_figA.place(x=0, y=0) ;fr_figA.Pgate()
    fr_exhi = cFr(fr_lanE, W= 45, H=262)           ; fr_exhi.place(x=0, y=1) ;fr_exhi.Pgate()
    fr_figB = cFr(fr_Rigt, W=278, H=264)           ; fr_figB._grid(R=0, C=1) ;fr_figB.Pgate()

    for ln in range(1, 7):
        r = ln -1
        fr_repr = cFr(fr_lanG, W=143, H=44, Bd=(1,GR)) ;fr_repr._grid(R=r, C=0) ;fr_repr.Pgate()

        fr_lanA.Rconf(r, W=1) ;fr_lanA.Cconf(0, W=1)
        fr_lanB.Rconf(r, W=1) ;fr_lanB.Cconf(0, W=1)
        fr_lanC.Rconf(r, W=1) ;fr_lanC.Cconf(0, W=1)
        fr_lanD.Rconf(r, W=1) ;fr_lanD.Cconf(0, W=1)
        fr_lanF.Rconf(r, W=1) ;fr_lanF.Cconf(0, W=1)
        fr_exhi.Rconf(r, W=1) ;fr_exhi.Cconf(0, W=1)
        fr_repr.Rconf(0, W=1) ;fr_repr.Cconf(0, W=1)
        fr_repr.Rconf(1, W=1)
        fr_repr.Rconf(2, W=1)

        # Label body=====
        lb_frno = cLbl(fr_lanA, Anc=CT,  font=(MUI, 9   ), Csr="hand2",          Bd=(1,RD))
        lb_name = cLbl(fr_lanB, Anc=CT,  font=(GUI,11,BD), bg="white",           Bd=(1,RD))
        lb_flyg = cLbl(fr_lanC, Anc=CT,  font=(MUI, 9,BD), bg="white", fg="red", Bd=(1,RD))
        lb_tilt = cLbl(fr_lanD, Anc=CT,  font=(MUI, 7,BD), **HDR_BF,             Bd=(1,RD))
        lb_exhi = cLbl(fr_exhi, Anc=CT,  font=(MUI, 8,BD), bg=WATER_COL                   )
        lb_cnt  = cLbl(fr_lanF, Anc="w", font=(MUI, 7,BD), **HDR_BF,             Bd=(1,RD))
        canvas = cCvs(fr_repr, W=143, H=44, bg="white", HLth=0)

        lb_frno._grid(Stk=ALL)
        lb_name._grid(Stk=ALL)
        lb_flyg._grid(Stk=ALL)
        lb_tilt._grid(Stk=ALL)
        lb_exhi._grid(Stk=ALL)
        lb_cnt._grid( Stk=ALL)
        canvas._grid( Stk=ALL)

        bt_sbj = cBtn( fr_botn, text= "", font=(MUI,8,BD), Rel=RA, bg="#4870b0", Csr= "hand2",
                                             Com=lambda ln=ln:_on_graph_btn(self, fr_grph, ln) )
        bt_sbj.place(x=4, y=(ln -1) *44 +5, width=13, height=32)
        # ----------------
        def _press(ev, ln=ln):
            w              = self.widgets_sub[ln]["frno"]
            self._drag_frn = w.cget("text")
        # ----------------
        def _release(ev, ln=ln):
            x, y = ev.x_root, ev.y_root
            for ln, wdict in self.widgets_sub.items():
                if ln != 0:
                    w  = wdict["frno"]
                    wx = w.winfo_rootx()
                    wy = w.winfo_rooty()
                    ww = w.winfo_width()
                    wh = w.winfo_height()
                    if wx <= x <= wx+ww and wy <= y <= wy+wh:
                        drop_lane = ln
                        break

            frno = int(self._drag_frn)
            self._frame_at_lane(drop_lane, frno)
            self._drag_frn = None
        # ----------------
        lb_frno.bind("<ButtonPress-1>",   _press  )
        lb_frno.bind("<ButtonRelease-1>", _release)

        self.widgets_sub[ln] ={ "frno":lb_frno,  "name":lb_name, "flyg":lb_flyg,
                                 "tilt":lb_tilt,  "exhi":lb_exhi,  "cnt" :lb_cnt,
                                 "cnvs":canvas, "bt_sbj":bt_sbj,                  }

    self.widgets_sub[0]  ={ "Graph":fr_grph,   "Fig_A":fr_figA,   "Fig_B":fr_figB,
                              "wthr":fr_wthr,    "wdir":fr_wdir,    "wspd":lb_wspd,
                              "wave":lb_wave,    "stab":lb_stab,    "shlp":lb_shlp,
                             "venue":lb_venue,  "upd_m":lb_upd_m,  "upd_b":lb_upd_b,
                             "deadl":lb_deadl,    "now":lb_now,     "last":lb_last,  }

# ----------------------------------------------------------------
def _on_graph_btn(self, frame, s_lane):

    if self.s_lane == s_lane:
        self.widgets_sub[s_lane]["bt_sbj"]._config(Bd=(1,RA), **BTN_BF)
        self.s_lane = 0 
    else: 
        self.widgets_sub[s_lane]["bt_sbj"]._config(Bd=(1,RD), **YEL2_BF)
        if self.s_lane:
            self.widgets_sub[self.s_lane]["bt_sbj"]._config(Bd=(1,RA), **BTN_BF)
        self.s_lane = s_lane

    framing_graph(self, frame, self.frame_order, self.data_rows, s_lane=self.s_lane)

# ----------------------------------------------------------------
def _switch_btn(self, btn:tk.Button, flag_name:str):

    setattr(self, flag_name, not getattr(self, flag_name))

    _config_btn(self, getattr(self,flag_name), btn, None, (1,RD), HL_GRN)

    self._update_main_entries()
    self._update_sub_entries()

# ----------------------------------------------------------------
def _toggle_btn(self, flag_name:str, flag:bool):

    setattr(self, flag_name, flag)

    btnA   = self.bt_ort if flag_name == "disp_oriten" else self.bt_rslt
    btnB   = self.bt_prt if flag_name == "disp_oriten" else self.bt_befr
    hl_col = HL_ORN      if flag_name == "disp_oriten" else YEL2_BF
    figB   = False       if flag_name == "disp_oriten" else True

    _config_btn(self, flag, btnA, btnB, (1,SK), hl_col)

    self._update_sub_entries(figA=False, graph=False, figB=figB)

# ----------------------------------------------------------------
def _config_btn(self, flag:bool, btnA:tk.Button, btnB:tk.Button, on_rel:tuple, hl_col:dict):

    if flag:
        btnA._config(Bd=on_rel, **hl_col)
        if btnB:
            btnB._config(Bd=(1,RA), **BTN_BF)
    else:
        btnA._config(Bd=(1,RA), **BTN_BF)
        if btnB:
            btnB._config(Bd=on_rel, **hl_col)

# ----------------------------------------------------------------
