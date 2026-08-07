
from tkinter import ttk, messagebox
from PIL     import Image, ImageTk
from typing  import Dict, Optional
from dateutil.relativedelta import relativedelta
from Helpers.Custum_func    import cFr, cLbl, cBtn
from Helpers.queries        import Query
from datetime               import datetime as dt, date, timedelta
from Widgets.widgets        import framing_graph
import tkinter as tk
import Dal     as dal
import os

GUI, MUI   = "Yu Gothic UI", "Meiryo UI"
GR, SD, BD = "groove", "solid", "bold"
ALL, CT    = "nsew", "center"

COL_KEYS  = [ "1 コース", "2 コース", "3 コース", "4 コース", "5 コース", "6 コース" ]
ROW_KEYS  = [ ("starts",      "出走 数"),
              ("st_ave",      "平均 ST"),
              ("r1",          "1 着"),
              ("r2",          "2 着"),
              ("r3",          "3 着"),
              ("r4",          "4 着"),
              ("r5",          "5 着"),
              ("r6",          "6 着"),
              ("F_L",         "F / L"), ]

MONTH    = { "1M": 1, "2M": 2, "3M": 3, "4M": 4, "5M": 5, "6M": 6, "7M": 7, "8M": 8, "9M": 9,
             "1Y":12, "2Y":24, "3Y":36, "4Y":48, "5Y":60,"10Y":120 }

SEASON   = {"spring":(3,5), "summer":(6,8), "autumn":(9,11), "winter":(12,2)}

ADJUST   = {"pre_y":-12, "pre_m":-1, "next_y":12, "next_m":1}

GMAP     = { "ALL":None, "SG":[5], "G1G2":[4,3,2], "GENE":[1,0] }

COL1, COL2, COL3 = "#FFF4AA", "#33EE33", "#2A62FF"
EDGE             = "#000010"
SRC_COL, SRS_COL = "#a463ff", "#505050"
STC_COL, STR_COL = "#2A62FF", "#2a9a01"
HDR_COL          = "#e0e1f4"

CEL_W  = 72
CEL_H  = 40
TBL_W  = CEL_W  * 7 +2 -5
TBL_H  = CEL_H  *10 +2 -5

#---------------------------------------
def _to_date(x) -> date:

    if isinstance(x, date): return x
    if isinstance(x,  str): return date.fromisoformat(x)

    raise ValueError("date conv error")

# ======== Venues Analysis (per venue) =======================================
class VenuesAnalysisScreen(tk.Toplevel):
    def __init__(self, master, venue_id):
        super().__init__(master)

        self.title("")
        self.geometry("920x720+1100+200")
        self.resizable(False, False)

        self.venue_id     = venue_id
        self.rows1        = None
        self.rows2        = None
        self.period       = 12
        self.adjustment   = False
        self.grade_key    = [0, 1, 2, 3, 4, 5]

        self.date_from    = date.today()
        self.date_to      = date.today()

        self.grade_state  = {(0,1):True, (2,):True, (3,4):True, (5,):True}

        self.filter_state = {     "wind_2":False,
                                  "wind_3":False,
                                  "wind_4":False,
                                  "wind_5":False,
                              "all_ladies":False, "not_ladies":False,
                                    "rain":False,
                             "follow_wind":False,
                            "against_wind":False,          }

        self.filter_dict  = {     "wind_2":("wind_spd", 2),
                                  "wind_3":("wind_spd", 3),
                                  "wind_4":("wind_spd", 4),
                                  "wind_5":("wind_spd", 5),
                              "all_ladies":("all_ladies", 1),
                              "not_ladies":("all_ladies", 0),
                                    "rain":("weather", "雨"),
                             "follow_wind":("wind_dir", (2,3,4,5,6)),
                            "against_wind":("wind_dir", (10,11,12,13,14)), }

        self._build_ui()
        self._apply_period("6M")
        self._set_venue_profile()
        self._update_rows()
        self._refresh_right_table()
        self._refresh_course_graph()

    # ====================== UI ============================
    def _build_ui(self):

        fr_root  = cFr(   self, W=900, H=720)
        fr_body  = cFr(fr_root, W=900, H=420)
        fr_botm  = cFr(fr_root, W=900, H=290)

        fr_left  = cFr(fr_body, W=380, H=420)
        fr_right = cFr(fr_body, W=520, H=420)

        fr_venu  = cFr(fr_left, W=380, H=255)
        fr_vtop  = cFr(fr_venu, W=380, H= 25)
        fr_imag  = cFr(fr_venu, W=380, H=180)
        fr_prof  = cFr(fr_venu, W=380, H= 50)

        fr_btnA  = cFr(fr_left, W=380, H= 30)
        fr_btnB  = cFr(fr_left, W=380, H= 30)
        fr_btnC  = cFr(fr_left, W=340, H= 30)
        fr_btnD  = cFr(fr_left, W=380, H= 30)

        fr_info  = cFr(fr_left, W=380, H= 30)

        fr_grph  = cFr( fr_botm, W=360, H=250)
        fr_Gbtn  = cFr( fr_botm, W=360, H= 30)
        fr_Tbtn  = cFr( fr_botm, W=420, H= 30)

        fr_root._grid( R=0, C=0, padx=10, pady=( 0, 10)) ;  fr_root.Pgate()
        fr_body._grid( R=0, C=0                        ) ;  fr_body.Pgate()
        fr_botm._grid( R=1, C=0                        ) ;  fr_botm.Pgate()
        fr_left._grid( R=0, C=0, padx=(0, 10)          ) ;  fr_left.Pgate()
        fr_right._grid(R=0, C=1                        ) ; fr_right.Pgate()
        fr_venu._grid( R=0, C=0,                       ) ;  fr_venu.Pgate()
        fr_vtop._grid( R=0, C=0,                       ) ;  fr_vtop.Pgate()
        fr_imag._grid( R=1, C=0                        ) ;  fr_imag.Pgate()
        fr_prof._grid( R=2, C=0,          pady=( 5, 0) ) ;  fr_prof.Pgate()
        fr_btnA._grid( R=1, C=0,          pady=( 5, 2) ) ;  fr_btnA.Pgate()
        fr_btnB._grid( R=2, C=0,          pady=( 0, 2) ) ;  fr_btnB.Pgate()
        fr_btnC._grid( R=3, C=0,          pady=( 0, 2) ) ;  fr_btnC.Pgate()
        fr_btnD._grid( R=4, C=0,          pady=( 0, 2) ) ;  fr_btnD.Pgate()
        fr_info._grid( R=5, C=0,          pady=( 0, 2) ) ;  fr_info.Pgate()
        fr_grph._grid( R=0, C=0                        ) ;  fr_grph.Pgate()
        fr_Gbtn._grid( R=1, C=0                        ) ;  fr_Gbtn.Pgate()
        fr_Tbtn._grid( R=0, C=1                        ) ;  fr_Tbtn.Pgate()

        fr_vtop.Cconf(0, W=1) ; fr_vtop.Rconf(0, W=1)

        self.lb_img = cLbl(fr_imag, text=""); self.lb_img._grid(R=0, C=0, Stk=ALL)
        self._set_venue_image()

        self.lb_vname = cLbl(fr_vtop, font=(GUI,11,BD))
        self.lb_vname._grid(R=0, C=0, Stk="nswe")

        self.lb_wtyp  = cLbl(fr_prof, font=(MUI,10))
        self.lb_home  = cLbl(fr_prof, font=(MUI,10))
        self.lb_mupd  = cLbl(fr_prof, font=(MUI,10))
        self.lb_bupd  = cLbl(fr_prof, font=(MUI,10))

        self.lb_wtyp._grid(R=1, C=0, padx=30, Stk="w")
        self.lb_home._grid(R=2, C=0, padx=30, Stk="w")
        self.lb_mupd._grid(R=1, C=1, padx=30, Stk="e")
        self.lb_bupd._grid(R=2, C=1, padx=30, Stk="e")
        self.lbl_range = cLbl(fr_info, text="", font=(MUI,10))
        self.lbl_range._grid(R=0, C=0, padx=(50,0), pady=(5,0), Stk="w")

        # 成績データ ---------
        def _make_cell(row:int, col:int, text:str="", f:str=None, anc:str=CT, bg:str=None):
            lbl = cLbl(self.fr_tbl, text=text, Bd=(1,GR), font=f, Anc=anc, bg=bg)
            lbl._grid(R=row, C=col, Stk=ALL)
            self._cells[(row, col)] = lbl
        #-----------
        self.fr_tbl = cFr(fr_right, W=TBL_W, H=TBL_H, Bd=(1,SD))
        self.fr_tbl._grid(R=0, C=0); self.fr_tbl.Pgate()

        self.fr_tbl.Cconf(0, minsize=CEL_W-5)
        self.fr_tbl.Rconf(0, minsize=CEL_H-5)

        for c in range(1, len(COL_KEYS)+1): self.fr_tbl.Cconf(c, minsize=CEL_W)
        for r in range(1, len(ROW_KEYS)+1): self.fr_tbl.Rconf(r, minsize=CEL_H)

        self._cells = {}
        _make_cell(0, 0, text="", bg=HDR_COL)

        for c, cap in enumerate(COL_KEYS, start=1):
            _make_cell(0, c, text=cap, f=(MUI,10), anc=CT, bg=HDR_COL)
        for r, (_, cap) in enumerate(ROW_KEYS, start=1):
            _make_cell(r, 0, text=cap, f=(MUI,10), anc=CT)
        for r in range(1, len(ROW_KEYS)+1):
            for c in range(1, len(COL_KEYS)+1):
                _make_cell(r, c, text="-", f=(GUI,10), anc="e", bg="white")

        # グラフ -------------
        self.fr_course = cFr(fr_grph, W= 40, H=240)
        self.fr_graph  = cFr(fr_grph, W=250, H=240, Bd=(1,SD))
        self.fr_label  = cFr(fr_grph, W= 60, H=240)
        self.fr_course._grid(R=0, C=0)
        self.fr_graph._grid( R=0, C=1)
        self.fr_label._grid( R=0, C=2)

        # ボタン作成 ---------
        self._btns  = [{}, {}, {}, {}, {}, {}]
        # ----------
        def mk_btn(frm, text, key, idx, w, px):
            b = ttk.Button( frm, text=text, width=w, style="r.TButton",
                              command=lambda k=key: self._on_switch(k, idx) )
            b.pack(side=tk.LEFT, padx=px)
            self._btns[idx][key] = b
            return b
        # ----------
        mk_btn(fr_btnA, "全期間",  "ALL", 0,7,0)
        mk_btn(fr_btnA, "今期",   "THIS", 0,7,(1,6))
        mk_btn(fr_btnA, "1 年",     "1Y", 0,7,1)
        for m in [9,6,3]: mk_btn(fr_btnA, f"{m}ヶ月", f"{m}M", 0,7,1)
        mk_btn(fr_btnB, "指定期間","adjust", 0,7,(0,10))
        mk_btn(fr_btnB, "<<", "pre_y", 4,3,0) ;mk_btn(fr_btnB, "<",   "pre_m", 4,3,0)
        self.lb_period = cLbl(fr_btnB, text=" 1 年  0 ヶ月", font=(MUI,9), Bd=(1,GR), bg="white")
        self.lb_period._pack(side=tk.LEFT, padx=3)
        mk_btn(fr_btnB, ">", "next_m", 4,3,0) ;mk_btn(fr_btnB, ">>", "next_y", 4,3,0)

        mk_btn(fr_btnC, "春期",           "spring", 5,  6, 2)
        mk_btn(fr_btnC, "夏期",           "summer", 5,  6, 2)
        mk_btn(fr_btnC, "秋期",           "autumn", 5,  6, 2)
        mk_btn(fr_btnC, "冬期",           "winter", 5,  6, 2)

        mk_btn(fr_btnD, "追い風",    "follow_wind", 3,  6, 2)
        mk_btn(fr_btnD, "向い風",   "against_wind", 3,  6, 2)
        cLbl(fr_btnD, text="風速", font=(MUI,9), Anc=CT).pack(side=tk.LEFT)
        mk_btn(fr_btnD, "2m以上",         "wind_2", 3,  6, 2)
        mk_btn(fr_btnD, "3m以上",         "wind_3", 3,  6, 2)
        mk_btn(fr_btnD, "4m以上",         "wind_4", 3,  6, 2)
        mk_btn(fr_btnD, "5m以上",         "wind_5", 3,  6, 2)

        mk_btn(fr_Gbtn, "SG",                 (5,), 1,  6, 2)
        mk_btn(fr_Gbtn, "G1",               (3, 4), 1,  6, 2)
        mk_btn(fr_Gbtn, "G2",                 (2,), 1,  6, 2)
        mk_btn(fr_Gbtn, "一般/G3",          (0, 1), 1,  7, 2)

        self._update_radio_btn_state( 0, "6M")
        self._update_toggle_btn_state(1, self.grade_state)

    # --------------------------------------------
    def _update_toggle_btn_state(self, idx:int, filter_dict:dict):

        for k, b in self._btns[idx].items():
            if filter_dict.get(k): b.state(['pressed'])
            else:                  b.state(['!pressed'])
    # --------------------------------------------
    def _update_radio_btn_state(self, idx:int, key:str|tuple):

        for k, b in self._btns[idx].items():
            if k == key: b.state(["pressed"])
            else:        b.state(["!pressed"])
    # --------------------------------------------
    def _on_switch(self, key:str ,idx:int):

        if idx == 0:
            if key == "adjust": self.adjustment = True
            else:               self.adjustment = False
            self._apply_period(key)
            self._update_radio_btn_state(0, key)
            self._update_radio_btn_state(5, key)
        if idx == 1:
            self.grade_state[key] = not self.grade_state.get(key, False)
            if self.grade_state[key]:
                self.grade_key.extend(key)
            else: self.grade_key = [k for k in self.grade_key if k not in key]
            self._update_toggle_btn_state(idx, self.grade_state)
        if idx == 3:   
            self.filter_state[key] = not self.filter_state.get(key, False)
            self._update_toggle_btn_state(idx, self.filter_state)
        if idx == 4:   
            self.period += ADJUST[key]
            if self.period < 0: self.period = 0
            self._apply_period("adjust")
            if  not self.adjustment: return
        if idx == 5:
            self._apply_period(SEASON[key])
            self._update_radio_btn_state(0, key)
            self._update_radio_btn_state(5, key)

        self._update_rows()
        self._refresh_course_graph()
        self._refresh_right_table()
    # --------------------------------------------
    def _apply_period(self, key:str|tuple):

        today        = date.today()
        self.date_to = today

        if isinstance(key, tuple):
            self.date_from, self.date_to = self._season_to_date(key[0], key[1])

        elif key == "ALL":
            self.date_from = date(2000,1,1)
            self.date_to   = date.today()

        elif key == "THIS":
            self.date_from = self._this_term_start(today)

        elif key == "adjust":
            m = f"{(self.period %12):2}"
            self.lb_period.config(text=f" {self.period // 12} 年 {m} ヶ月 ")
            if self.adjustment:
                self.date_from = today -relativedelta(months=self.period)
            else: return

        else: self.date_from = today -relativedelta(months=MONTH[key])

        self.lbl_range.config(
              text=f"{self._jp_date(self.date_from)}  ～  {self._jp_date(self.date_to)}" )

    # --------------- データ 取得 ----------------
    def _update_rows(self):

        opt_dict = {}

        for key, stat in self.filter_state.items():
            if stat:
                (opt, param)  = self.filter_dict[key]
                opt_dict[opt] = param

        query1 = Query( self.date_from, self.date_to, query1=True, grade=self.grade_key,
                          venue_id=self.venue_id, exclude_rookie=[True,False], **opt_dict )
        query2 = Query( self.date_from, self.date_to, query1=True, grade=self.grade_key,
                                     exclude_rookie=[True,False], **opt_dict )

        self.rows1 = query1._pack(by_course=True)
        self.rows2 = query2._pack(by_course=True)

    # ------------------- 画像 -------------------
    def _set_venue_image(self):

        try:
            path  = os.path.join(r"C:\boatrace\tmp\venues_img", f"{self.venue_id}.png")
            im    = Image.open(path).resize((380, 180))
            photo = ImageTk.PhotoImage(im)
            self.lb_img.configure(image=photo, text="")
            self.lb_img._venue_photo_ref = photo
        except Exception:
            self.lb_img.configure(text="(No Image)")

    # --------------- プロフィール ---------------
    def _set_venue_profile(self):

        row = dal.fetch_one("""
            SELECT venue_name, upd_motor, upd_boat, home_region, water_type
              FROM Venues
             WHERE venue_id=?
            """, (self.venue_id,)) or {}

        row = {k:row[k] for k in row.keys()} if row else {}
        vn  = row.get("venue_name","")
        um  = row.get("upd_motor","")
        ub  = row.get("upd_boat","")
        hr  = row.get("home_region","")
        wt  = row.get("water_type","")

        self.lb_vname.configure(text=f"ボートレース  {vn}")
        self.lb_wtyp.configure( text=f" 水 質：{wt}")
        self.lb_home.configure( text=f"ホーム：{hr}支部")
        self.lb_mupd.configure( text=f"ﾓｰﾀｰ更新月：{um} 月")
        self.lb_bupd.configure( text=f"ﾎﾞｰﾄ更新月：{ub} 月")

    # ------------- 右側テーブル更新 -------------
    def _refresh_right_table(self):

        rows1 = self.rows1
        rows2 = self.rows2

        for col, c in enumerate(range(1,7), start=1):
            row1 = rows1[c]
            row2 = rows2[c]
            if row1['cnt'] <= 0:
                cells = ["-     "] * len(ROW_KEYS)
            else:
                cells = [
                    f"{row1['cnt']}     ",
                    f"{row1['st_ave']}     ",
                    f"{int(row2['rate'][1] *100)} / {int(row1['rate'][1] *100):2} % ",
                    f"{int(row2['rate'][2] *100)} / {int(row1['rate'][2] *100):2} % ",
                    f"{int(row2['rate'][3] *100)} / {int(row1['rate'][3] *100):2} % ",
                    f"{int(row2['rate'][4] *100)} / {int(row1['rate'][4] *100):2} % ",
                    f"{int(row2['rate'][5] *100)} / {int(row1['rate'][5] *100):2} % ",
                    f"{int(row2['rate'][6] *100)} / {int(row1['rate'][6] *100):2} % ",
                    f"{row1['F_L']}    ",                                                           ]   

            for row1, val in enumerate(cells, start=1):
                self._cells[(row1, col)].configure(text=str(val))

    # ============= ｺｰｽ別ｸﾞﾗﾌ描画 ================
    def _refresh_course_graph(self):

        fr     = self.fr_graph
        w,  h  = 250, 240
        data   = self.rows1
        framing_graph(self, fr, [1,2,3,4,5,6], rows1=self.rows1, rows2=self.rows2, W=w, H=h)

        for lane in range(1,7):
            y     = (h // 6) *(lane-1) +5
            v     = data[lane]['st_ave']
            label = f"{('ー' if v is None else v)}"

            cLbl(self.fr_label, text=label, Anc="w", font=(MUI,9)).place(x=10, y=y)
            cLbl( self.fr_course, text=f"{lane} ｺｰｽ", Anc="w", font=(MUI,9)
                 ).place(x=0, y=y)

   #--------------------------
    @staticmethod
    def _season_to_date(m1, m2):
        y = date.today().year
        m = date.today().month
        if m2 <= m:
            if m1 >= m2:
                return f"{y-1}-{m1:02}-01", f"{y}-{m2:02}-28"
            else:
                return f"{y}-{m1:02}-01", f"{y}-{m2:02}-30"
        elif m1 >= m2:
            return f"{y-2}-{m1:02}-01", f"{y-1}-{m2:02}-28"
        else:
            return f"{y-1}-{m1:02}-01", f"{y-1}-{m2:02}-30"
   #--------------------------
    @staticmethod
    def _this_term_start(today:date) -> date:

        if 5 <= today.month <= 10: return date(today.year,  5, 1)
        if      today.month >= 11: return date(today.year, 11, 1)

        return date(today.year-1, 11, 1)
    #-------------------------
    @staticmethod
    def _add_months(d:date, n:int) -> date:

        y    = d.year + (d.month-1 + n)//12
        m    =          (d.month-1 + n) %12 +1
        last = (date(y + (m==12), (m%12) +1, 1) - timedelta(days=1)).day

        return date(y, m, min(d.day, last))
    #-------------------------
    @staticmethod
    def _jp_date(d:date) -> str:

       d = _to_date(d)

       return f"{d.year} 年 {d.month}月 {d.day}日"

