# -*- coding: utf-8 -*-
# C:\boatrace\UI\Placeholder\placeholder.py

import tkinter as tk
from Helpers.Custum_func import cFr, cLbl, cBtn, cCvs
from Widgets.widgets     import framing_graph, framing_figure

GUI, MUI, HNH, CBR     = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, SK, BD = "groove", "solid", "ridge", "raised", "sunken", "bold"
ALL, CT                = "nsew", "center"

SCOL               = "#a5e6ff"
BG_COL             = "#e9f1f2"

# ==================== プレースホルダ(Main) ======================
# ----------------------------------------------------------------
def build_main_placeholder(self, parent:tk.Frame):

    for ln in range(1, 7):
        row    = (ln -1)
        Lane = cFr(parent, W=1200, H=167)
        Lane._grid(R=row, C=0); Lane.Pgate()

        # 列構成: [Lft][Ctr][Rht] ======================
        Lane.Cconf(0, W=0, minsize= 413) # L
        Lane.Cconf(1, W=1, minsize= 358) # C
        Lane.Cconf(2, W=0, minsize= 433) # R
        Lane.Rconf(0, W=1)

        # [L]: 選手基本データ ===========================
        fr_Lft = cFr(Lane,   W=409, H=167, Bd=(1,SD))
        fr_Lft.place(x=0, y=0) ;fr_Lft.Pgate()

        fr_A   = cFr(fr_Lft, W= 22, H=165, Bd=(1,GR)) ;fr_A._grid(  R=0, C=0) ;fr_A.Pgate()
        fr_B   = cFr(fr_Lft, W=112, H=165, Bd=(1,GR)) ;fr_B._grid(  R=0, C=1) ;fr_B.Pgate()
        fr_C   = cFr(fr_Lft, W=182, H=165, Bd=(1,GR)) ;fr_C._grid(  R=0, C=2) ;fr_C.Pgate()
        fr_D   = cFr(fr_Lft, W= 46, H=165           ) ;fr_D._grid(  R=0, C=3) ;fr_D.Pgate()
        fr_E   = cFr(fr_Lft, W= 45, H=165           ) ;fr_E._grid(  R=0, C=4) ;fr_E.Pgate()
        fr_C1  = cFr(fr_C,   W=182, H= 32, Bd=(1,GR)) ;fr_C1._grid( R=0, C=0) ;fr_C1.Pgate()
        fr_C2  = cFr(fr_C,   W=182, H=133, Bd=(1,GR)) ;fr_C2._grid( R=1, C=0) ;fr_C2.Pgate()
        fr_D1  = cFr(fr_D,   W= 46, H= 33, Bd=(1,GR)) ;fr_D1._grid( R=0, C=0) ;fr_D1.Pgate()
        fr_D2  = cFr(fr_D,   W= 46, H= 33, Bd=(1,GR)) ;fr_D2._grid( R=1, C=0) ;fr_D2.Pgate()
        fr_D3  = cFr(fr_D,   W= 46, H= 33, Bd=(1,GR)) ;fr_D3._grid( R=2, C=0) ;fr_D3.Pgate()
        fr_D4  = cFr(fr_D,   W= 46, H= 33, Bd=(1,GR)) ;fr_D4._grid( R=3, C=0) ;fr_D4.Pgate()
        fr_D5  = cFr(fr_D,   W= 46, H= 33, Bd=(1,GR)) ;fr_D5._grid( R=4, C=0) ;fr_D5.Pgate()
        fr_E1  = cFr(fr_E,   W= 45, H= 33, Bd=(1,GR)) ;fr_E1._grid( R=0, C=0) ;fr_E1.Pgate()
        fr_E2  = cFr(fr_E,   W= 45, H= 33, Bd=(1,GR)) ;fr_E2._grid( R=1, C=0) ;fr_E2.Pgate()
        fr_E3  = cFr(fr_E,   W= 45, H= 33, Bd=(1,GR)) ;fr_E3._grid( R=2, C=0) ;fr_E3.Pgate()
        fr_E4  = cFr(fr_E,   W= 45, H= 33, Bd=(1,GR)) ;fr_E4._grid( R=3, C=0) ;fr_E4.Pgate()
        fr_E5  = cFr(fr_E,   W= 45, H= 33, Bd=(1,GR)) ;fr_E5._grid( R=4, C=0) ;fr_E5.Pgate()

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

        lb_frno  = cLbl(fr_A,  Anc=CT, font=(GUI,13,  )            )   # 艇番
        lb_photo = cLbl(fr_B,  cursor="hand2"                      )   # 画像
        lb_name  = cLbl(fr_C2, Anc=CT, font=(GUI,13,BD), bg="white")   # 選手名
        lb_rate1 = cLbl(fr_D1, Anc=CT, font=(MUI, 8,BD), bg="white")
        lb_rate2 = cLbl(fr_D2, Anc=CT, font=(MUI, 8,BD), bg="white")
        lb_rate3 = cLbl(fr_D3, Anc=CT, font=(MUI, 8,BD), bg="white")
        lb_late  = cLbl(fr_D4, Anc=CT, font=(GUI, 7   ), bg="white")   # 出遅れ
        lb_flyg  = cLbl(fr_D4, Anc="w",font=(MUI, 7,  ), bg="white")   # ﾌﾗｲﾝｸﾞ
        lb_stav  = cLbl(fr_D5, Anc=CT, font=(MUI, 8,BD), bg="white")   # 平均ST
        lb_mo_av = cLbl(fr_E4, Anc=CT, font=(MUI, 8,BD), bg="white", cursor="hand2")
        lb_bo_av = cLbl(fr_E5, Anc=CT, font=(MUI, 8   ), bg="white")

        cv1 = tk.Canvas(fr_C1, width=182, height=30, bg="white", highlightthickness=0)
        cv2 = tk.Canvas(fr_C2, width=182, height=30, bg="white", highlightthickness=0)
        cv3 = tk.Canvas(fr_C2, width=182, height=30, bg="white", highlightthickness=0)
        cv1.place(x=0, y= -1)
        cv2.place(x=0, y= 0)
        cv3.place(x=0, y=94)

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

        # [Ctr]: 可変表示ｵﾘｼﾞﾅﾙﾃﾞｰﾀ(center_widgets) ====

        fr_Ctr = cFr(Lane, W=358, H=167, Bd=(1,SD))
        fr_Ctr.place(x=408, y=0) ;fr_Ctr.Pgate()

        # [Rgt]: 節間成績/2走ｲﾝﾃﾞｯｸｽ ===================

        R_hdr:list[tk.Frame]       = []
        R_bdy:list[list[tk.Frame]] = []
        R_idx:list[tk.Frame]       = []

        fr_Rgt = cFr(Lane, W=435, H=167, Bd=(1,SD))
        fr_Rgt.place(x=764, y=0) ;fr_Rgt.Pgate()

        for c in range(14):  fr_Rgt.Cconf(c, W=1, uniform=ln)
        for r in range(1,5): fr_Rgt.Rconf(r, W=1, uniform=ln)
        for i in range(7):
            fr_hdr = cFr(fr_Rgt, W=29, H=25, bg=BG_COL, Bd=(1,RA))
            fr_hdr._grid(R=0, C=i*2, Cspan=2, Stk=ALL) ;fr_hdr.Pgate()
            R_hdr.append(fr_hdr)

        for col in range(14):
            cells = []
            for row in range(1, 5):
                bd= (1,RA) if row <= 1 else (1,GR)
                fr_cell = cFr(fr_Rgt, W=29, H=33, bg="white", Bd=bd)
                fr_cell._grid(R=row, C=col, Stk=ALL, py=(1,0)) ;fr_cell.Pgate()
                cells.append(fr_cell)
            R_bdy.append(cells)

        fr_idx = cFr(fr_Rgt, W=27, Bd=(1,GR), bg=BG_COL)
        fr_idx._grid(R=0, C=14, Rspan=6, Stk=ALL);fr_idx.Pgate()

        for i in range(3):
            fr_idx.Rconf(i, W=1, uniform=f"IDX{ln}")
            fr_inr = cFr(fr_idx, Bd=(1, "flat"), bg=BG_COL)
            fr_inr._grid(R=i, C=0, Stk=ALL) ;fr_inr.Pgate()
            R_idx.append(fr_inr)
        fr_idx.Cconf(0, W=1)

        # ================
        self._widgets_main[ln] = {
           "frno":lb_frno,    #"regp":lb_regp,    "pid":lb_pid,    "rgns":lb_regs,
           "name":lb_name,    #"age" :lb_age,     "wkg":lb_wkg,    "heig":lb_heig,
           "stav":lb_stav,
           "late":lb_late,    "flyg":lb_flyg,  "mo_av":lb_mo_av, "bo_av":lb_bo_av,
          "rate1":lb_rate1,  "rate2":lb_rate2, "rate3":lb_rate3,
          "photo":lb_photo, "fr_Ctr":fr_Ctr,    "Lane":Lane,  
            "cv1":cv1,  "cv2":cv2,  "cv3":cv3,       }

        self._widgets_main[ln]["R_hdr"] = R_hdr
        self._widgets_main[ln]["R_bdy"] = R_bdy
        self._widgets_main[ln]["R_idx"] = R_idx

# ==================== プレースホルダ(Sub) =======================
# ----------------------------------------------------------------
def build_sub_placeholder(self, parent:tk.Frame): #  1188  318
    #---------------
    def reset_figure():
        if hasattr(fr_figA, "reset_figure"):
            fr_figA.reset_figure()
    #---------------
    self.s_lane      = 0

    fr_Hedr  = cFr(parent, W=1200, H= 45)
    fr_body  = cFr(parent, W=1200, H=266)
    fr_Hedr._grid(R=0, C=0, pady=(0,7)) ;fr_Hedr.Pgate()
    fr_body._grid(R=2, C=0            ) ;fr_body.Pgate()

    # Frame header================================
    fr_hdrL  = cFr(fr_Hedr, W=913, H= 45, Bd=(1,SD))
    fr_hdrR  = cFr(fr_Hedr, W=280, H= 45, Bd=(1,SD))

    fr_hdrL._grid(R=0, C=0, padx=(0, 7)) ;fr_hdrL.Pgate()
    fr_hdrR._grid(R=0, C=1)              ;fr_hdrL.Pgate()

    fr_venu = cFr(fr_hdrL, W= 80, H= 43, Bd=(1,RD)) ;fr_venu._grid(R=0, C=0) ;fr_venu.Pgate()
    fr_updt = cFr(fr_hdrL, W=150, H= 43           ) ;fr_updt._grid(R=0, C=1) ;fr_updt.Pgate()
    fr_clok = cFr(fr_hdrL, W=120, H= 43           ) ;fr_clok._grid(R=0, C=2) ;fr_clok.Pgate()
    fr_last = cFr(fr_hdrL, W= 60, H= 43, Bd=(1,GR)) ;fr_last._grid(R=0, C=3) ;fr_last.Pgate()
    fr_pnel = cFr(fr_hdrL, W=501, H= 43           ) ;fr_pnel._grid(R=0, C=4) ;fr_pnel.Pgate()

    fr_btnf = cFr(fr_hdrR, W= 84, H= 43, bg=BG_COL) ;fr_btnf._grid(R=0, C=0) ;fr_btnf.Pgate()
    fr_wthr = cFr(fr_hdrR, W= 51, H= 43, bg=BG_COL) ;fr_wthr._grid(R=0, C=1) ;fr_wthr.Pgate()
    fr_para = cFr(fr_hdrR, W= 92, H= 43, bg=BG_COL) ;fr_para._grid(R=0, C=2) ;fr_para.Pgate()
    fr_wdir = cFr(fr_hdrR, W= 51, H= 43, bg=BG_COL) ;fr_wdir._grid(R=0, C=3) ;fr_wdir.Pgate()

    fr_pnlA = cFr(fr_pnel, W=501, H= 22, bg="white");fr_pnlA._grid(R=0, C=0) ;fr_pnlA.Pgate()
    fr_pnlB = cFr(fr_pnel, W=501, H= 21, bg="white");fr_pnlB._grid(R=1, C=0) ;fr_pnlB.Pgate()

    self.bt_ctw = cFr(fr_pnlA, W=341, H= 22) ;self.bt_ctw._grid(R=0, C=0)
    fr_info     = cFr(fr_pnlA, W=160, H= 22)     ;fr_info._grid(R=0, C=1) ;fr_info.Pgate()

    self.bt_rst = cBtn(fr_pnlB, W=8, font=(MUI,8), text="Reset", Bd=(1,RA), bg="#bbe0fc")
    self.bt_fly = cBtn(fr_pnlB, W=6, font=(MUI,8), text="Flying")
    self.bt_nfl = cBtn(fr_pnlB, W=7, font=(MUI,8), text="! Flying")
    self.bt_exE = cBtn(fr_pnlB, W=7, font=(MUI,8), text="江戸川除外")
    self.bt_grd = cBtn(fr_pnlB, W=7, font=(MUI,8), text="一般戦除外")
    self.bt_mrk = cBtn(fr_pnlB, W=8, font=(MUI,8), text="全 マーク")
    self.bt_ort = cBtn(fr_pnlB, W=8, font=(MUI,8), text="オ リ 展")
    self.bt_prt = cBtn(fr_pnlB, W=8, font=(MUI,8), text="交換 部品")

    self.bt_rst.config(command=reset_figure)
    self.bt_fly.config(command=lambda:_switch_btn(self, self.bt_fly, "flying"))
    self.bt_nfl.config(command=lambda:_switch_btn(self, self.bt_nfl, "not_flying"))
    self.bt_exE.config(command=lambda:_switch_btn(self, self.bt_exE, "exclude_edo"))
    self.bt_grd.config(command=lambda:_switch_btn(self, self.bt_grd, "limited_grade"))
    self.bt_mrk.config(command=lambda:_switch_btn(self, self.bt_mrk, "on_mark"))
    self.bt_ort.config(command=lambda:_toggle_btn(self, self.bt_ort, "disp_oriten")) 
    self.bt_prt.config(command=lambda:_toggle_btn(self, self.bt_prt, "disp_parts"))

    self.bt_rst._grid(R=0, C=0)
    self.bt_fly._grid(R=0, C=1, px=(5,0))
    self.bt_nfl._grid(R=0, C=2)
    self.bt_exE._grid(R=0, C=3)
    self.bt_grd._grid(R=0, C=4)
    self.bt_mrk._grid(R=0, C=5, px=(0,5))
    self.bt_ort._grid(R=0, C=6)
    self.bt_prt._grid(R=0, C=7)

    _config_btn(self, self.bt_fly, getattr(self, "flying"))
    _config_btn(self, self.bt_nfl, getattr(self, "not_flying"))
    _config_btn(self, self.bt_exE, getattr(self, "exclude_edo"))
    _config_btn(self, self.bt_grd, getattr(self, "limited_grade"))
    _config_btn(self, self.bt_mrk, getattr(self, "on_mark"))
    _config_btn(self, self.bt_ort, getattr(self, "disp_oriten"), orange=True)
    _config_btn(self, self.bt_prt, getattr(self, "disp_parts"),  orange=True)

    fr_venu.Rconf(0, minsize=22) ;fr_venu.Cconf(0, minsize=80)
    fr_venu.Rconf(1, minsize=21)
    fr_updt.Rconf(0, minsize=22) ;fr_updt.Cconf(0, minsize=80)
    fr_updt.Rconf(1, minsize=21) ;fr_updt.Cconf(1, minsize=70)
    fr_clok.Rconf(0, minsize=22) ;fr_clok.Cconf(0, minsize=55)
    fr_clok.Rconf(1, minsize=21) ;fr_clok.Cconf(1, minsize=65)
    fr_last.Rconf(0, minsize=43) ;fr_last.Cconf(0, minsize=60)

    fr_info.Rconf(0, minsize=22) ;fr_info.Cconf(0, minsize=80)
    fr_info.Cconf(1, minsize=80)

    fr_btnf.Rconf(0, minsize=43) ;fr_btnf.Cconf(0, minsize=84)
    fr_wthr.Rconf(0, minsize=43) ;fr_wthr.Cconf(0, minsize=51)
    fr_para.Rconf(0, minsize=22) ;fr_para.Cconf(0, minsize=92)
    fr_para.Rconf(1, minsize=21)
    fr_wdir.Rconf(0, minsize=43) ;fr_wdir.Cconf(0, minsize=51)

    lb_vname = cLbl(fr_venu, font=(MUI, 9,BD), bg="#c3ffcb", cursor= "hand2")
    lb_w_typ = cLbl(fr_venu, font=(MUI, 8   ), bg="#c3ffcb"           )
    lb_upd_m = cLbl(fr_updt, font=(MUI, 9   ), bg="white",   Bd=(1,SK))
    lb_upd_b = cLbl(fr_updt, font=(MUI, 9   ), bg="white",   Bd=(1,SK))
    lb_deadl = cLbl(fr_clok, font=(MUI, 9   ), bg="white",   Bd=(1,SK))
    lb_now   = cLbl(fr_clok, font=(MUI, 9   ), bg="white",   Bd=(1,SK))
    lb_last  = cLbl(fr_last, font=(GUI,10   ), bg="#f8f8f8", Bd=(1,RD))
    lb_vname.bind("<Button-1>",lambda e:self.app.open_v_analys(self.venue_id))

    lb_vname._grid(R=0, C=0, Stk=ALL)
    lb_w_typ._grid(R=1, C=0, Stk=ALL)
    lb_upd_m._grid(R=0, C=1, Stk=ALL)
    lb_upd_b._grid(R=1, C=1, Stk=ALL)
    lb_deadl._grid(R=0, C=1, Stk=ALL)
    lb_now._grid(  R=1, C=1, Stk=ALL)
    lb_last._grid( R=0, C=0, Stk=ALL)

    cLbl(fr_updt, text="モーター更新後", font=(MUI,8), bg=BG_COL, Bd=(1,RD))._grid(R=0, C=0, Stk=ALL)
    cLbl(fr_updt, text=" ボート 更新後", font=(MUI,8), bg=BG_COL, Bd=(1,RD))._grid(R=1, C=0, Stk=ALL)
    cLbl(fr_clok, text="締 切",          font=(MUI,8), bg=BG_COL, Bd=(1,RD))._grid(R=0, C=0, Stk=ALL)
    cLbl(fr_clok, text="現 在",          font=(MUI,8), bg=BG_COL, Bd=(1,RD))._grid(R=1, C=0, Stk=ALL)

    lb_stab = cLbl(fr_info, font=(MUI, 9), Bd=(1,GR)) ;lb_stab._grid(R=0, C=0, Stk=ALL)
    lb_shlp = cLbl(fr_info, font=(MUI, 9), Bd=(1,GR)) ;lb_shlp._grid(R=0, C=1, Stk=ALL)

    bt_befr = cBtn(fr_btnf, text=f"展 示", font=(MUI,8), Com=lambda:self._update_sub_entries(0))
    bt_rslt = cBtn(fr_btnf, text=f"結 果", font=(MUI,8), Com=lambda:self._update_sub_entries(1))
    lb_wspd = cLbl(fr_para, font=(MUI,10), bg=BG_COL) ;lb_wspd._grid(R=0, C=0, Stk=ALL)
    lb_wave = cLbl(fr_para, font=(MUI,10), bg=BG_COL) ;lb_wave._grid(R=1, C=0, Stk=ALL)

    bt_befr.place(x=0, y= 1, width=70, height=20)
    bt_rslt.place(x=0, y=22, width=70, height=20)

    # Frame body==================================
    fr_Lane = cFr(fr_body, W=913, H=266, Bd=(1,SD))
    fr_Rigt = cFr(fr_body, W=280, H=266, Bd=(1,SD))

    fr_Lane._grid(R=0, C=0)              ; fr_Lane.Pgate()
    fr_Rigt._grid(R=0, C=3, padx=(7, 0)) ; fr_Rigt.Pgate()

    fr_lanA = cFr(fr_Lane, W= 23, H=264)
    fr_lanB = cFr(fr_Lane, W=140, H=264)
    fr_lanC = cFr(fr_Lane, W= 20, H=264)
    fr_lanD = cFr(fr_Lane, W= 34, H=264)
    fr_lanE = cFr(fr_Lane, W=254, H=264)
    fr_botn = cFr(fr_Lane, W= 22, H=264, bg=SCOL, Bd=(1, GR))
    fr_grph = cFr(fr_Lane, W=246, H=264)
    fr_lanF = cFr(fr_Lane, W= 29, H=264)
    fr_lanG = cFr(fr_Lane, W=143, H=264)
    fr_figA = cFr(fr_lanE, W=254, H=264)
    fr_exhi = cFr(fr_lanE, W= 45, H=262)
    fr_figB = cFr(fr_Rigt, W=278, H=264)

    fr_lanA._grid(R=0, C=0)              ;fr_lanA.Pgate()
    fr_lanB._grid(R=0, C=1)              ;fr_lanB.Pgate()
    fr_lanC._grid(R=0, C=2)              ;fr_lanC.Pgate()
    fr_lanD._grid(R=0, C=3)              ;fr_lanD.Pgate()
    fr_lanE._grid(R=0, C=4)              ;fr_lanE.Pgate()
    fr_botn._grid(R=0, C=5)              ;fr_botn.Pgate()
    fr_grph._grid(R=0, C=6)              ;fr_grph.Pgate()
    fr_lanF._grid(R=0, C=7)              ;fr_lanF.Pgate()
    fr_lanG._grid(R=0, C=8)              ;fr_lanG.Pgate()
    fr_figA.place(x=0, y=0)              ;fr_figA.Pgate()
    fr_exhi.place(x=0, y=1)              ;fr_exhi.Pgate()
    fr_figB._grid(R=0, C=1)              ;fr_figB.Pgate()

    for ln in range(1, 7):
        row = ln -1

        fr_repr = cFr(fr_lanG, W=143, H=44, Bd=(1,GR))
        fr_repr._grid(R=row, C=0) ;fr_repr.Pgate()

        fr_lanA.Rconf(row, W=1) ;fr_lanA.Cconf(0, W=1)
        fr_lanB.Rconf(row, W=1) ;fr_lanB.Cconf(0, W=1)
        fr_lanC.Rconf(row, W=1) ;fr_lanC.Cconf(0, W=1)
        fr_lanD.Rconf(row, W=1) ;fr_lanD.Cconf(0, W=1)
        fr_lanF.Rconf(row, W=1) ;fr_lanF.Cconf(0, W=1)
        fr_exhi.Rconf(row, W=1) ;fr_exhi.Cconf(0, W=1)
        fr_repr.Rconf(  0, W=1) ;fr_repr.Cconf(0, W=1)
        fr_repr.Rconf(  1, W=1)
        fr_repr.Rconf(  2, W=1)

        # Label body=====
        lb_frno = cLbl(fr_lanA, Anc=CT, font=(MUI, 9   ), cursor= "hand2",      Bd=(1,RD))
        lb_name = cLbl(fr_lanB, Anc=CT, font=(GUI,11,BD), bg="white",           Bd=(1,RD))
        lb_flyg = cLbl(fr_lanC, Anc=CT, font=(MUI, 9,BD), bg="white", fg="red", Bd=(1,RD))
        lb_tilt = cLbl(fr_lanD, Anc=CT, font=(MUI, 8,BD), bg="white",           Bd=(1,RD))
        lb_exhi = cLbl(fr_exhi, Anc=CT, font=(MUI, 8,BD), bg=SCOL)
        lb_cnt  = cLbl(fr_lanF, Anc=CT, font=(GUI, 8,BD), bg="#f9f9f9",         Bd=(1,GR))
        cv_repr = cCvs(fr_repr, width=143, height=44, bg="white", highlightthickness=0)

        lb_frno._grid(          Stk=ALL)
        lb_name._grid(          Stk=ALL)
        lb_flyg._grid(          Stk=ALL)
        lb_tilt._grid(          Stk=ALL)
        lb_exhi._grid(          Stk=ALL)
        lb_cnt._grid(           Stk=ALL)
        cv_repr._grid(R=0, C=0, Stk=ALL)

        bt_sbj = cBtn( fr_botn, text= "", font=(MUI,8,BD), Rel=RA, bg="#dfdfdf",
                                  Com=lambda L=ln:_graph(self, fr_grph, L) )
        bt_sbj.place(x=4, y=(ln -1) *44 +5, width=13, height=32)
        # ----------------
        def _press(ev, ln=ln):
            w              = self._widgets_sub[ln]["frno"]
            self._drag_frn = w.cget("text")
        # ----------------
        def _release(ev, ln=ln):
            x, y = ev.x_root, ev.y_root
            for ln, wdict in self._widgets_sub.items():
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

        self._widgets_sub[ln] ={ "frno":lb_frno,   "name":lb_name, "flyg":lb_flyg,
                                 "tilt":lb_tilt,   "exhi":lb_exhi,  "cnt" :lb_cnt,
                                 "repr":cv_repr, "bt_sbj":bt_sbj,                  }

    self._widgets_sub[0]  ={ "Graph":fr_grph,   "Fig_A":fr_figA,   "Fig_B":fr_figB,
                              "wthr":fr_wthr,    "wdir":fr_wdir,    "wspd":lb_wspd,
                              "wave":lb_wave,    "stab":lb_stab,    "shlp":lb_shlp,
                             "vname":lb_vname,  "w_typ":lb_w_typ,  "upd_m":lb_upd_m,
                             "upd_b":lb_upd_b,  "deadl":lb_deadl,    "now":lb_now,
                              "last":lb_last, "bt_befr":bt_befr, "bt_rslt":bt_rslt,  }

    self.toggle_dict = {self.bt_ort:"disp_oriten", self.bt_prt:"disp_parts"}

# ----------------------------------------------------------------
def _graph(self, f, s_lane):

    if self.s_lane == s_lane:
        self._widgets_sub[s_lane]["bt_sbj"].config(bg="#dfdfdf", relief=RA) # 非選択
        self.s_lane = 0 
    else: 
        self._widgets_sub[s_lane]["bt_sbj"].config(bg="#F1EE62", relief=RD) # 選択中
        if self.s_lane:
            self._widgets_sub[self.s_lane]["bt_sbj"].config(bg="#E1E1E1", relief=RA) # 非選択
        self.s_lane = s_lane

    framing_graph(self, f, self.frame_order, self.data_rows, rows2=self.overall, s_lane=self.s_lane)

# ----------------------------------------------------------------
def _switch_btn(self, btn:tk.Button, flag_name:str):

    setattr(self, flag_name, not getattr(self, flag_name))

    _config_btn(self, btn, getattr(self, flag_name))

    self._reload_for(self.date, self.venue_id, self.race_no)

# ----------------------------------------------------------------
def _config_btn(self, btn:tk.Button, flg:bool, orange:bool=False):

    if orange:
        btn.config(bg="#ffdcac", relief=SK) if flg else btn.config(bg="#DFDFDF", relief=RA)
    else:
        btn.config(bg="#dbfbd1", relief=SK) if flg else btn.config(bg="#DFDFDF", relief=RA)

# ----------------------------------------------------------------
def _toggle_btn(self, btn:tk.Button, flag_name:str):

    setattr(self, flag_name, True)

    for bt, flg in self.toggle_dict.items(): 
        if bt == btn: bt.config(bg="#ffdcac", relief=SK)
        else:
             bt.config(bg="#DFDFDF", relief=RA)
             setattr(self, flg, False)

    self._reload_for(self.date, self.venue_id, self.race_no)

# ----------------------------------------------------------------